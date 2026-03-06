document.addEventListener('DOMContentLoaded', () => {
    const scanBtn = document.getElementById('scanBtn');
    const videoList = document.getElementById('videoList');
    const statusText = document.getElementById('status');
    const versionLabel = document.getElementById('versionLabel');

    if (versionLabel) {
        versionLabel.textContent = "v" + chrome.runtime.getManifest().version;
    }

    if (!scanBtn) {
        console.error("scanBtn not found in DOM");
        return;
    }

    scanBtn.addEventListener('click', () => {
        statusText.textContent = "";
        videoList.innerHTML = "<div style='text-align:center;'>スキャン中...</div>";

        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            if (tabs.length === 0) return;
            const currentTabId = tabs[0].id;

            // ブラウザのタブ名を取得してファイル名用にサニタイズ（使用不可文字を置換）
            let pageTitle = tabs[0].title || "";
            pageTitle = pageTitle.replace(/[\\/:*?"<>|]/g, '_');

            // Backgroundからキャプチャしたすべての動画データを取得
            chrome.runtime.sendMessage({ action: "getCapturedUrls", tabId: currentTabId }, (bgRes) => {
                let capturedData = [];
                if (bgRes && bgRes.videoData) {
                    capturedData = bgRes.videoData;
                }

                if (videoList) videoList.innerHTML = "";

                if (capturedData.length === 0) {
                    if (statusText) statusText.innerHTML = "動画が見つかりません。<br>ページをリロードして、動画を数秒再生してから<br>再度お試しください。";
                    return;
                }

                // ファイルサイズが大きい順にソートする (不明・0は一番下)
                capturedData.sort((a, b) => {
                    const sizeA = a.size || 0;
                    const sizeB = b.size || 0;
                    return sizeB - sizeA;
                });

                capturedData.forEach((data, index) => {
                    const itemDiv = document.createElement('div');
                    itemDiv.className = 'video-item';

                    // サイズのフォーマット
                    let sizeStr = "サイズ不明";
                    if (data.size > 0) {
                        sizeStr = (data.size / (1024 * 1024)).toFixed(2) + " MB";
                    }

                    // 短いURL表示用
                    let shortUrl = data.url;
                    try {
                        let urlObj = new URL(data.url);
                        shortUrl = "..." + urlObj.pathname.substring(urlObj.pathname.length - 30);
                    } catch (e) { }

                    // 種類によるボタンの見た目変更
                    let isM3u8 = data.type.includes('mpegurl') || data.url.includes('.m3u8');
                    let btnClass = isM3u8 ? 'download-target-btn m3u8' : 'download-target-btn';
                    let btnText = isM3u8 ? 'プレイリスト (m3u8) をコピー' : 'ダウンロードする';

                    itemDiv.innerHTML = `
                        <div class="video-info">
                            <span class="video-type">${isM3u8 ? 'HLS' : 'MP4'}</span>
                            <span class="video-size">${sizeStr}</span><br>
                            <span style="color:#a0aec0;font-size:10px;">${shortUrl}</span>
                        </div>
                        <button class="${btnClass}" data-url="${data.url}" data-is-m3u8="${isM3u8}" data-referer="${data.referer || ''}">
                            ${btnText}
                        </button>
                    `;
                    videoList.appendChild(itemDiv);
                });

                // 各ボタンのイベントリスナー設定
                document.querySelectorAll('.download-target-btn').forEach(btn => {
                    btn.addEventListener('click', (e) => {
                        const url = e.target.getAttribute('data-url');
                        const isM3u8 = e.target.getAttribute('data-is-m3u8') === 'true';
                        const referer = e.target.getAttribute('data-referer');

                        if (isM3u8) {
                            if (statusText) {
                                statusText.style.color = "#3182ce";
                                statusText.innerText = "HLSダウンロードをバックグラウンドで開始します...";
                            }
                            chrome.runtime.sendMessage({
                                action: "startHlsDownload",
                                url: url,
                                title: pageTitle,
                                referer: referer || url
                            }, (res) => {
                                if (res && res.success) {
                                    if (statusText) {
                                        statusText.style.color = "#38a169";
                                        statusText.innerText = "HLSダウンロード開始！進捗は拡張機能のアイコンのバッジに表示されます。";
                                    }
                                } else {
                                    if (statusText) {
                                        statusText.style.color = "#e53e3e";
                                        statusText.innerText = "エラー: " + (res ? res.error : "不明なエラー");
                                    }
                                }
                            });
                        } else {
                            startDownload(url, referer, pageTitle);
                        }
                    });
                });
            });
        });
    });

    function startDownload(url, referer, pageTitle) {
        if (statusText) {
            statusText.style.color = "#3182ce";
            statusText.innerText = "ダウンロードを開始します...";
        }

        let filename = "video_" + Date.now() + ".mp4";
        if (pageTitle) {
            filename = pageTitle + ".mp4";
        } else {
            try {
                let extracted = new URL(url).pathname.split('/').pop();
                if (extracted.includes('.mp4')) filename = extracted;
            } catch (e) { }
        }

        chrome.runtime.sendMessage({
            action: "startDownloadWithReferer",
            url: url,
            filename: filename,
            referer: referer || url
        }, (res) => {
            if (!statusText) return;
            if (res && res.success) {
                statusText.style.color = "#38a169";
                statusText.innerText = "指定のフォルダへダウンロードを開始しました！";
            } else {
                statusText.style.color = "#e53e3e";
                statusText.innerText = "エラー: " + (res ? res.error : "不明なエラー");
            }
        });
    }
});
