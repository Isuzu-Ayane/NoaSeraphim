let tabVideoUrls = {};
let pendingDownloads = {};

// オフスクリーンドキュメントの管理用
let creating;
async function setupOffscreenDocument(path) {
    if (chrome.offscreen) {
        if (await chrome.offscreen.hasDocument()) return;
        if (creating) {
            await creating;
        } else {
            creating = chrome.offscreen.createDocument({
                url: path,
                reasons: ['BLOBS'], // Blobとしてファイルを結合する用途
                justification: 'Merging HLS video segments in background'
            });
            await creating;
            creating = null;
        }
    }
}

// ネットワークリクエストの監視
// 拡張機能の核となる部分です
chrome.webRequest.onHeadersReceived.addListener(
    (details) => {
        const url = details.url;
        let isVideo = false;
        let contentType = '';
        let contentLength = 0;

        // レスポンスヘッダーからコンテンツタイプとサイズをチェック
        if (details.responseHeaders) {
            for (let header of details.responseHeaders) {
                const name = header.name.toLowerCase();
                if (name === 'content-type') {
                    contentType = header.value.toLowerCase();
                } else if (name === 'content-length') {
                    contentLength = parseInt(header.value, 10);
                } else if (name === 'content-range') {
                    const rangeMatch = header.value.match(/\/(\d+)/);
                    if (rangeMatch && rangeMatch[1]) {
                        contentLength = parseInt(rangeMatch[1], 10);
                    }
                }
            }
        }

        // --- 強力な判定ロジック群 ---

        // 1. Content-Typeによる判定
        if (contentType.includes('video/') ||
            contentType.includes('application/vnd.apple.mpegurl') || // HLS (m3u8)
            contentType.includes('application/x-mpegurl') ||
            contentType.includes('application/dash+xml')) {          // MPEG-DASH
            isVideo = true;
        }

        // 2. URLの拡張子やパターンによる判定（Video DownloadHelperがよくやるヒューリスティック）
        const lowerUrl = url.toLowerCase();
        if (lowerUrl.includes('.mp4') ||
            lowerUrl.includes('.m3u8') ||
            lowerUrl.includes('.ts') ||
            lowerUrl.includes('.webm') ||
            lowerUrl.includes('get_video') ||
            lowerUrl.includes('videoplayback')) { // YouTubeなどでよくあるパターン
            isVideo = true;
        }

        // 3. サイズによる判定（非常に小さいものはアイコンや広告の断片の可能性が高いため弾く）
        // 逆に言えば、バイナリデータ（application/octet-streamなど）でもサイズが大きければ動画の可能性がある
        // 1MB(1048576 bytes)以下のものは動画本体の可能性は低いとして除外（.m3u8のようなプレイリストファイル自体は軽いので除外しない）
        if (isVideo) {
            if (!contentType.includes('mpegurl') && !lowerUrl.includes('.m3u8') && contentLength > 0 && contentLength < 1000000) {
                // 広告の短いmp4やトラッキング用の可能性がある
                // 完全に除外するかは要検討だが、一旦はログだけ出す
                // console.log("サイズが小さすぎる動画:", url);
            }
        }

        // 記録処理
        if (isVideo && !lowerUrl.includes('doubleclick') && !lowerUrl.includes('adsystem')) {
            const tabId = details.tabId;
            // リクエストがMain Frame(0)、Sub Frame(1)等のページ内から発火した場合のみ追跡
            if (tabId >= 0) {
                if (!tabVideoUrls[tabId]) {
                    tabVideoUrls[tabId] = [];
                }

                // 重複排除と情報保存（URLだけでなく、Typeなども後で表示に使えるように）
                let exists = tabVideoUrls[tabId].find(item => item.url === url);
                if (!exists) {
                    let referer = details.initiator || url;
                    tabVideoUrls[tabId].push({
                        url: url,
                        type: contentType || getExtension(url),
                        size: contentLength,
                        timestamp: Date.now(),
                        referer: referer
                    });
                    console.log("動画(M3U8含む)をキャプチャしました:", url, contentType);
                }
            }
        }
    },
    { urls: ["<all_urls>"] },
    ["responseHeaders"] // ヘッダーを読むための権限必須
);

function getExtension(url) {
    try {
        let path = new URL(url).pathname;
        let ext = path.split('.').pop();
        if (['mp4', 'm3u8', 'ts', 'webm'].includes(ext)) return ext;
    } catch (e) { }
    return "unknown";
}

// タブが閉じられたらデータを削除
chrome.tabs.onRemoved.addListener((tabId) => {
    delete tabVideoUrls[tabId];
});

// ポップアップからの問い合わせに応答
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "registerExtractedVideo") {
        const tabId = sender.tab ? sender.tab.id : -1;
        if (tabId >= 0) {
            if (!tabVideoUrls[tabId]) {
                tabVideoUrls[tabId] = [];
            }
            let exists = tabVideoUrls[tabId].find(item => item.url === request.url);
            if (!exists) {
                tabVideoUrls[tabId].push({
                    url: request.url,
                    type: "video/mp4",
                    size: 1000000000,
                    timestamp: Date.now(),
                    referer: request.referer
                });
                console.log("Aniporn extracted video registered:", request.url);
            }
        }
    } else if (request.action === "getCapturedUrls") {
        const data = tabVideoUrls[request.tabId] || [];
        sendResponse({ videoData: data });
    } else if (request.action === "startDownloadWithReferer") {
        const { url, filename, referer } = request;
        try {
            chrome.declarativeNetRequest.updateDynamicRules({
                removeRuleIds: [1],
                addRules: [{
                    id: 1,
                    priority: 1,
                    action: {
                        type: "modifyHeaders",
                        requestHeaders: [
                            { header: "Referer", operation: "set", value: referer }
                        ],
                        responseHeaders: [
                            { header: "Content-Disposition", operation: "remove" }
                        ]
                    },
                    condition: {
                        urlFilter: url,
                        resourceTypes: ["main_frame", "sub_frame", "xmlhttprequest", "other"]
                    }
                }]
            }, () => {
                chrome.downloads.download({
                    url: url,
                    saveAs: false
                }, (downloadId) => {
                    if (chrome.runtime.lastError) {
                        sendResponse({ success: false, error: chrome.runtime.lastError.message });
                    } else {
                        // ダウンロードIDとファイル名の紐付けを保存する
                        pendingDownloads[downloadId] = filename || ("video_" + Date.now() + ".mp4");
                        sendResponse({ success: true, downloadId: downloadId });
                    }
                });
            });
        } catch (e) {
            sendResponse({ success: false, error: e.toString() });
        }
        return true;
    } else if (request.action === "setupHlsReferer") {
        const { domain, referer } = request;
        try {
            chrome.declarativeNetRequest.updateDynamicRules({
                removeRuleIds: [2],
                addRules: [{
                    id: 2,
                    priority: 2,
                    action: {
                        type: "modifyHeaders",
                        requestHeaders: [
                            { header: "Referer", operation: "set", value: referer }
                        ]
                    },
                    condition: {
                        urlFilter: `||${domain}/*`,
                        resourceTypes: ["xmlhttprequest", "other"]
                    }
                }]
            }, () => {
                sendResponse({ success: true });
            });
        } catch (e) {
            sendResponse({ success: false, error: e.toString() });
        }
        return true;
    } else if (request.action === "startHlsDownload") {
        setupOffscreenDocument('downloader.html').then(() => {
            // オフスクリーンドキュメント側にDL開始を指示する
            chrome.runtime.sendMessage({
                action: "processHlsDownload",
                url: request.url,
                title: request.title,
                referer: request.referer
            });
        }).catch(err => {
            console.error("Offscreen creation failed:", err);
            sendResponse({ success: false, error: err.toString() });
        });
        sendResponse({ success: true });
        return true;
    } else if (request.action === "updateHlsProgress") {
        // バッジに進捗を表示
        if (request.percent !== undefined) {
            chrome.action.setBadgeText({ text: request.percent + "%" });
            chrome.action.setBadgeBackgroundColor({ color: "#3182ce" });
        }
        if (request.percent >= 100 || request.percent === -1) {
            setTimeout(() => {
                chrome.action.setBadgeText({ text: "" });
            }, 3000);
        }
    } else if (request.action === "closeOffscreenDocument") {
        // 結合完了後にオフスクリーンドキュメントを閉じる
        if (chrome.offscreen) {
            chrome.offscreen.closeDocument();
        }
    }
});

// ダウンロードファイル名が決定される直前に介入し、強制的にファイル名を上書きする
chrome.downloads.onDeterminingFilename.addListener((item, suggest) => {
    if (pendingDownloads[item.id]) {
        // 設定しておいた和名のファイル名を適用する
        suggest({
            filename: pendingDownloads[item.id],
            conflictAction: "uniquify"
        });
        delete pendingDownloads[item.id];
    } else {
        // 対象外のダウンロードはそのまま
        suggest();
    }
});
