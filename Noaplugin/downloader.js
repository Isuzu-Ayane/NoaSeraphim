chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "processHlsDownload") {
        startHlsDownload(request.url, request.title, request.referer);
        sendResponse({ success: true });
        return true;
    }
});

document.addEventListener('DOMContentLoaded', async () => {
    const params = new URLSearchParams(window.location.search);
    const m3u8Url = params.get('url');
    if (m3u8Url) {
        const title = params.get('title') || 'video';
        const referer = params.get('referer');
        startHlsDownload(m3u8Url, title, referer);
    }
});

async function startHlsDownload(m3u8Url, title, referer) {
    const titleEl = document.getElementById('videoTitle');
    if (titleEl) titleEl.innerText = title;

    try {
        // バックグラウンドにリファラールールの設定を依頼
        const domain = new URL(m3u8Url).hostname;
        updateStatus("通信準備中...");
        await new Promise((resolve, reject) => {
            chrome.runtime.sendMessage({
                action: "setupHlsReferer",
                domain: domain,
                referer: referer || m3u8Url
            }, (res) => {
                if (res && res.success) resolve();
                else reject(new Error(res ? res.error : "Unknown error"));
            });
        });

        updateStatus("プレイリストを解析中...");
        const playlistInfo = await parseM3U8(m3u8Url);

        if (!playlistInfo.segments || playlistInfo.segments.length === 0) {
            throw new Error("ダウンロード可能なセグメントが見つかりませんでした。");
        }

        updateStatus(`動画セグメントをダウンロード中 (全 ${playlistInfo.segments.length} 個)...`);

        const blobs = await downloadSegments(playlistInfo.segments, playlistInfo.encryption);

        updateStatus("ファイルを結合中...");
        const finalBlob = new Blob(blobs, { type: 'video/mp2t' });

        const objectUrl = URL.createObjectURL(finalBlob);

        // aタグをクリックさせて直接ダウンロード（ファイル名を強制適用）
        const a = document.createElement('a');
        a.href = objectUrl;
        a.download = title + ".ts";
        a.click();

        const successText = document.getElementById('successText');
        if (successText) successText.style.display = "block";
        updateStatus("結合完了！");

        // オフスクリーン用：100%を通知し、少し長めに待ってからドキュメントを閉じる（ダウンロード完了猶予）
        chrome.runtime.sendMessage({ action: "updateHlsProgress", percent: 100 });
        setTimeout(() => {
            chrome.runtime.sendMessage({ action: "closeOffscreenDocument" });
        }, 120000); // 2分後に閉じる

        // 短時間後にメモリ解放
        setTimeout(() => URL.revokeObjectURL(objectUrl), 130000);

    } catch (e) {
        showError(e.message);
        chrome.runtime.sendMessage({ action: "updateHlsProgress", percent: -1 });
        setTimeout(() => {
            chrome.runtime.sendMessage({ action: "closeOffscreenDocument" });
        }, 5000);
    }
}

function updateStatus(text) {
    const el = document.getElementById('statusText');
    if (el) el.innerText = text;
}

function updateProgress(percent, ratioText) {
    const bar = document.getElementById('progressBar');
    if (bar) bar.style.width = percent + "%";
    const textEl = document.getElementById('progressText');
    if (textEl) textEl.innerText = ratioText + ` (${percent}%)`;

    // 背景に通知してバッジを更新させる
    chrome.runtime.sendMessage({ action: "updateHlsProgress", percent: percent });
}

function showError(msg) {
    const el = document.getElementById('errorText');
    if (el) {
        el.innerText = "エラー: " + msg;
        el.style.display = "block";
    }
    updateStatus("処理が中断されました");
}

async function parseM3U8(url) {
    const res = await fetch(url);
    if (!res.ok) throw new Error("プレイリストの取得に失敗しました (" + res.status + ")");
    const text = await res.text();
    const lines = text.split(/\r?\n/);

    let isMaster = false;
    let maxBandwidth = 0;
    let bestPlaylistUrl = "";

    for (let i = 0; i < lines.length; i++) {
        if (lines[i].startsWith("#EXT-X-STREAM-INF:")) {
            isMaster = true;
            let bwMatch = lines[i].match(/BANDWIDTH=(\d+)/);
            let bw = bwMatch ? parseInt(bwMatch[1]) : 0;
            let uriLine = lines[i + 1].trim();
            if (bw >= maxBandwidth) {
                maxBandwidth = bw;
                bestPlaylistUrl = new URL(uriLine, url).href;
            }
        }
    }

    if (isMaster) {
        console.log("Master playlist detected, using best stream:", bestPlaylistUrl);
        return parseMediaPlaylist(bestPlaylistUrl);
    } else {
        return parseMediaPlaylist(url);
    }
}

async function parseMediaPlaylist(url) {
    const res = await fetch(url);
    if (!res.ok) throw new Error("メディアプレイリストの取得に失敗しました");
    const text = await res.text();
    const lines = text.split(/\r?\n/);

    let segments = [];
    let encryption = null;
    let sequence = 0;

    for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();
        if (line.startsWith("#EXT-X-MEDIA-SEQUENCE:")) {
            sequence = parseInt(line.split(":")[1]);
        } else if (line.startsWith("#EXT-X-KEY:")) {
            let methodMatch = line.match(/METHOD=([^,]+)/);
            if (methodMatch && methodMatch[1] === "AES-128") {
                let uriMatch = line.match(/URI="([^"]+)"/);
                let ivMatch = line.match(/IV=(0x[0-9A-Fa-f]+)/);
                encryption = {
                    method: "AES-128",
                    uri: uriMatch ? new URL(uriMatch[1], url).href : null,
                    iv: ivMatch ? ivMatch[1] : null
                };
            }
        } else if (line.startsWith("#EXTINF:")) {
            i++;
            while (i < lines.length && lines[i].trim().startsWith("#")) {
                i++;
            }
            if (i < lines.length && lines[i].trim()) {
                segments.push({
                    url: new URL(lines[i].trim(), url).href,
                    sequence: sequence++
                });
            }
        }
    }

    return { segments, encryption };
}

async function downloadSegments(segments, encryption) {
    let importedKey = null;
    if (encryption && encryption.method === "AES-128" && encryption.uri) {
        updateStatus("暗号化キーを取得中...");
        const keyRes = await fetch(encryption.uri);
        if (!keyRes.ok) throw new Error("暗号化キーの取得に失敗しました");
        const keyBuffer = await keyRes.arrayBuffer();
        importedKey = await crypto.subtle.importKey('raw', keyBuffer, { name: 'AES-CBC' }, false, ['decrypt']);
    }

    const total = segments.length;
    let completed = 0;
    const results = new Array(total);

    // 最大同時接続数
    const CONCURRENCY = 4;
    let currentIndex = 0;

    return new Promise((resolve, reject) => {
        let hasError = false;

        function next() {
            if (hasError) return;
            if (currentIndex >= total) return;

            const index = currentIndex++;
            const segment = segments[index];

            fetchSegment(segment, encryption, importedKey)
                .then(data => {
                    results[index] = data;
                    completed++;

                    let percent = Math.floor((completed / total) * 100);
                    updateProgress(percent, `${completed} / ${total}`);

                    if (completed === total) {
                        resolve(results);
                    } else {
                        next();
                    }
                })
                .catch(err => {
                    hasError = true;
                    reject(err);
                });
        }

        for (let i = 0; i < Math.min(CONCURRENCY, total); i++) {
            next();
        }
    });
}

async function fetchSegment(segment, encryption, importedKey) {
    let retries = 3;
    let lastError;

    while (retries > 0) {
        try {
            const res = await fetch(segment.url);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);

            const buffer = await res.arrayBuffer();

            if (importedKey) {
                let ivBuffer = new Uint8Array(16);
                if (encryption && encryption.iv) {
                    let ivStr = encryption.iv.replace("0x", "");
                    for (let j = 0; j < 16; j++) {
                        ivBuffer[j] = parseInt(ivStr.slice(j * 2, j * 2 + 2), 16) || 0;
                    }
                } else {
                    let view = new DataView(ivBuffer.buffer);
                    view.setUint32(12, segment.sequence, false); // Big endian sequence number
                }

                return await crypto.subtle.decrypt({ name: 'AES-CBC', iv: ivBuffer }, importedKey, buffer);
            } else {
                return buffer;
            }
        } catch (e) {
            lastError = e;
            retries--;
            await new Promise(r => setTimeout(r, 1000));
        }
    }
    throw lastError;
}
