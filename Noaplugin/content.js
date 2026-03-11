// 直接DOMまたはiframeの中身を探すスクリプト
function findVideos() {
    let urls = [];
    // ページ内のすべてのvideoタグとsourceタグを探す
    const videos = document.querySelectorAll('video, source');
    for (let v of videos) {
        if (v.src && !v.src.startsWith('blob:') && !urls.includes(v.src)) {
            urls.push(v.src);
            console.log("動画を見つけました(Content Script):", v.src);
        }
    }

    // iframe内のsrcに直接設定されている場合（ただし別ドメインのiframeの中身はCORS制限でここでは見えない）
    const iframes = document.querySelectorAll('iframe');
    for (let i of iframes) {
        if (i.src && (i.src.includes('.mp4') || i.src.includes('video'))) {
            if (!urls.includes(i.src)) urls.push(i.src);
        }
    }
    return urls;
}

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'getVideoUrlsFromDOM') {
        const urls = findVideos();
        // iframeの中のJS(all_frames: true)からの情報を集約するため、非同期で送る設計もあるが、
        // 今回はシンプルに各フレームが持つURLを返す
        sendResponse({ urls: urls, url: window.location.href });
    } else if (request.action === 'getPageTitle') {
        let title = '';
        try {
            const h1 = document.querySelector('h1');
            if (h1 && h1.innerText) {
                title = h1.innerText.trim();
            }
        } catch (e) {
            console.error("Error finding H1", e);
        }
        if (!title) {
            title = document.title || '';
        }
        sendResponse({ title: title });
    }
});

// 自分自身（all_framesなのでiframe内でも動く）で見つけたものを即時記録するアプローチ
const myUrls = findVideos();
if (myUrls.length > 0) {
    console.log("このフレームで見つけた動画:", myUrls);
}

// Aniporn.com 向けの特殊抽出ロジック（広告をスキップして直接MP4を取得）
if (window.location.hostname.includes('aniporn.com')) {
    const s = document.createElement('script');
    s.textContent = `
        (function() {
            let attempts = 0;
            const checkPlayer = setInterval(() => {
                attempts++;
                if (typeof jwplayer === 'function' && jwplayer().getPlaylist) {
                    clearInterval(checkPlayer);
                    try {
                        const playlist = jwplayer().getPlaylist();
                        if (playlist && playlist.length > 0 && playlist[0].file) {
                            const fileUrl = playlist[0].file;
                            const fullUrl = fileUrl.startsWith('http') ? fileUrl : window.location.origin + fileUrl;
                            window.postMessage({ type: 'ANIPORN_EXTRACTED_URL', url: fullUrl }, '*');
                        }
                    } catch (e) {
                        console.error('Aniporn Extraction Error:', e);
                    }
                }
                if (attempts > 50) clearInterval(checkPlayer); // Stop after ~25 seconds
            }, 500);
        })();
    `;
    (document.head || document.documentElement).appendChild(s);
    s.remove();

    window.addEventListener('message', function (event) {
        if (event.source !== window || !event.data || event.data.type !== 'ANIPORN_EXTRACTED_URL') {
            return;
        }
        chrome.runtime.sendMessage({
            action: 'registerExtractedVideo',
            url: event.data.url,
            referer: window.location.href
        });
    });
}
