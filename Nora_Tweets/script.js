// Basic Auth & Post Loader

// --- CONFIG ---
const SECRET_PASS = "seraphim"; // Basic Client-Side Lock
// To add posts, just add to this list.
// Images should be placed in the 'images' folder.
const POSTS = [
    {
        id: 1,
        date: "2025-12-15",
        title: "はじまりの日",
        image: "post_01.png"
    }
];

// --- AUTH LOGIC ---
function tryLogin() {
    const input = document.getElementById('pass-input').value;
    const err = document.getElementById('error-msg');

    if (input === SECRET_PASS) {
        // Unlock
        document.getElementById('login-gate').style.display = 'none';
        document.getElementById('blog-container').style.display = 'block';
        loadPosts();
    } else {
        err.textContent = "Access Denied.";
        // Shake animation effect could go here
    }
}

// Allow Enter key
document.getElementById('pass-input').addEventListener('keypress', function (e) {
    if (e.key === 'Enter') tryLogin();
});


// --- BLOG LOGIC ---
function loadPosts() {
    const container = document.getElementById('posts-area');
    container.innerHTML = "";

    // Reverse order (newest first)
    [...POSTS].reverse().forEach(post => {
        const card = document.createElement('div');
        card.className = 'post-card';

        card.innerHTML = `
            <img src="images/${post.image}" alt="${post.title}" class="post-image" onerror="this.style.display='none'; this.nextElementSibling.style.display='block'">
            <div class="img-missing-msg" style="display:none; padding:20px; color:orange;">
                [Image Not Found: ${post.image}]<br>
                Please place image in 'images/' folder.
            </div>
            <div class="post-meta">
                <span class="post-title">${post.title}</span>
                <span class="post-date">${post.date}</span>
            </div>
        `;

        container.appendChild(card);
    });
}
