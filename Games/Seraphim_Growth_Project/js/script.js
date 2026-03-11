/* --- Zero-Complexity Game Core v6.0 (Recovery) --- */

const NoaGame = {
    // --- State ---
    state: {
        age: 6,
        month: 1,
        // Stats: Initial 20 (Balanced Growth), Energy 100
        stats: { int: 20, sta: 20, lif: 20, aff: 20, eng: 200 },
        isOver: false,
        isProcessing: false
    },

    // --- Initialization ---
    init: function () {
        console.log("NoaGame v6.0 Initializing (Recovery Build)...");

        // 1. Render Initial State
        this.render();

        // 2. Set Initial Image
        this.setImg('neutral');

        // 3. Log Start
        this.log("システム起動 (v6.0 Recovery)... 正常稼働中。");
        console.log("NoaGame Initialized.");

        // 4. Init Audio System
        this.audioSys.init();

        // 5. Global Interaction Listener for Audio (Autoplay Unlock)
        const unlockAudio = () => {
            this.audioSys.ensureStart();
            window.removeEventListener('click', unlockAudio);
            window.removeEventListener('touchstart', unlockAudio);
        };
        window.addEventListener('click', unlockAudio);
        window.addEventListener('touchstart', unlockAudio);
    },

    // --- Audio System ---
    audioSys: {
        bgm: new Audio(),
        currentTrack: 'age6',
        isStarted: false,

        init: function () {
            this.bgm.loop = true;
            this.bgm.volume = 0.5;
            console.log("Audio System Prepared.");
        },

        ensureStart: function () {
            if (!this.isStarted) {
                this.isStarted = true;
                this.play(this.currentTrack);
                NoaGame.log("[Audio] システム連動開始。");
            }
        },

        play: function (trackName) {
            // Prevent restarting same track
            if (this.currentTrack === trackName && !this.bgm.paused && this.bgm.currentTime > 0) return;

            this.currentTrack = trackName;
            this.bgm.src = `Music/${trackName}.mp3`;

            const playPromise = this.bgm.play();
            if (playPromise !== undefined) {
                playPromise.then(() => {
                    console.log(`[Audio] Playing: ${trackName}`);
                }).catch(error => {
                    console.error(`[Audio] Play failed: ${error}`);
                    if (error.name === 'NotAllowedError') {
                        // Suppress visible error for autoplay block, as global listener handles it
                        console.log("Autoplay blocked, waiting for interaction.");
                    } else {
                        NoaGame.log(`<span style='color:red;'>[Audio] エラー: ${error.message} (File: ${trackName}.mp3)</span>`);
                    }
                });
            }
        },

        stop: function () {
            this.bgm.pause();
            this.bgm.currentTime = 0;
        }
    },

    // --- Action Logic (Balanced) ---
    act: function (type) {
        if (this.state.isOver || this.state.isProcessing) return;

        console.log(`Action: ${type}`);
        this.setBusy(true);
        this.audioSys.ensureStart(); // Try to start audio

        const s = this.state.stats;
        const energyCost = 10; // Difficulty: Eased (15 -> 10)
        let msg = "";

        if (type === 'rest') {
            s.eng = Math.min(200, s.eng + 60); // Rest recovers 60
            msg = "ノアはゆっくり休みました。元気が回復しました！";
        } else {
            // Deduct Energy
            s.eng -= energyCost;

            // Probability Logic (Requested Balance)
            // Fail (15%): +1
            // Normal (35%): +2
            // Success (30%): +3
            // Great (20%): +4
            const roll = Math.random() * 100;
            let gain = 0;
            let outcome = "";

            if (roll < 15) {
                gain = 1;
                outcome = "（失敗...）";
            } else if (roll < 50) { // 15 + 35
                gain = 2;
                outcome = "（普通）";
            } else if (roll < 80) { // 50 + 30
                gain = 3;
                outcome = "（成功！）";
            } else {
                gain = 4;
                outcome = "（大成功！！）";
            }

            // Apply Gain
            if (type === 'study') { s.int = Math.min(200, s.int + gain); msg = `勉強をしました${outcome}。知力が${gain}上がりました。`; }
            if (type === 'exercise') { s.sta = Math.min(200, s.sta + gain); msg = `運動をしました${outcome}。体力が${gain}上がりました。`; }
            if (type === 'life') { s.lif = Math.min(200, s.lif + gain); msg = `お手伝いをしました${outcome}。生活力が${gain}上がりました。`; }
            if (type === 'socialize') { s.aff = Math.min(200, s.aff + gain); msg = `おしゃべりをしました${outcome}。好感度が${gain}上がりました。`; }
        }


        // Exhaustion Check
        if (s.eng <= 0) {
            msg += "<br><span style='color:red;'>【警告】元気が尽きてダウン...</span>";
            // Penalty: -2 to all stats
            s.int = Math.max(0, s.int - 2);
            s.sta = Math.max(0, s.sta - 2);
            s.lif = Math.max(0, s.lif - 2);
            s.eng = 30; // Force recovery
            this.setImg('sick');
        } else {
            this.setImg(type);
        }

        // Render & Turn End
        this.render();
        this.log(msg);
        this.nextTurn();

        // Unlock input
        setTimeout(() => {
            this.setBusy(false);
        }, 800);
    },

    nextTurn: function () {
        this.state.month++;
        if (this.state.month > 12) {
            this.state.month = 1;
            this.state.age++;
            this.log(`<b>【誕生日】ノアは${this.state.age}歳になりました！</b>`);

            // Audio Progression
            if (this.state.age === 12) this.audioSys.play('age12');
            if (this.state.age === 15) this.audioSys.play('age15');
            if (this.state.age === 18) this.audioSys.play('age18');
        }

        if (this.state.age >= 22) {
            this.endGame();
        }

        this.render();
    },

    endGame: function () {
        this.state.isOver = true;
        const s = this.state.stats;
        let title = "", desc = "", imgKey = "";

        // Ending Conditions
        if (s.int >= 150 && s.sta >= 150 && s.aff >= 150) {
            title = "True Ending: 大天使の覚醒";
            desc = "伝説の天使として覚醒しました。";
            imgKey = "ending_archangel";
            this.audioSys.play('ending_archangel');
        } else if (s.eng <= 0) {
            title = "Bad Ending: 力尽きた...";
            desc = "無理が祟って倒れてしまいました。";
            imgKey = "ending_lost"; // Corrected from ending_fragile
            this.audioSys.play('ending');
        } else {
            title = "Normal Ending: 旅立ち";
            desc = "新たな旅に出ます。";
            imgKey = "ending_human"; // Corrected from ending_departure
            this.audioSys.play('ending');
        }

        // Show Modal
        const modal = document.getElementById('ending-modal');
        if (modal) {
            document.getElementById('end-title').textContent = title;
            document.getElementById('end-desc').textContent = desc;
            const img = document.getElementById('end-img');

            // Explicit Reset
            img.style.display = 'block';
            document.getElementById('end-fallback').style.display = 'none';

            // Robust Load Logic
            img.onerror = () => {
                console.warn(`[Ending] Failed to load: ${img.src}`);
                // Try JPG if PNG fails
                if (img.src.endsWith('.png')) {
                    img.src = img.src.replace('.png', '.jpg');
                } else {
                    img.style.display = 'none';
                    document.getElementById('end-fallback').style.display = 'block';
                    document.getElementById('end-fallback').textContent = `Image Missing: assets/${imgKey}.png`;
                }
            };

            // Use explicit relative path
            img.src = `./assets/${imgKey}.png`;

            modal.style.display = 'flex';
        }
    },

    // --- Visuals ---
    render: function () {
        const s = this.state;

        this.setText('age-display', `Age: ${s.age}`);
        this.setText('month-display', `Month: ${s.month}`);

        this.updateBar('int', s.int);
        this.updateBar('sta', s.sta);
        this.updateBar('lif', s.lif);
        this.updateBar('aff', s.aff);
        this.updateBar('eng', s.eng);
    },

    updateBar: function (key, val) {
        let safeVal = parseInt(val, 10);
        if (isNaN(safeVal)) safeVal = 0;
        // Keep bar visible if value > 0 but small? Logic from before:
        if (safeVal === 0 && this.state.stats[key] > 0) safeVal = this.state.stats[key];

        const elVal = document.getElementById(`val-${key}`);
        const elBar = document.getElementById(`bar-${key}`);

        if (elVal) elVal.textContent = safeVal;
        if (elBar) elBar.style.width = `${Math.min(100, Math.max(0, (safeVal / 200) * 100))}%`;
    },

    setText: function (id, text) {
        const el = document.getElementById(id);
        if (el) el.textContent = text;
    },

    log: function (text) {
        const box = document.getElementById('msg-box');
        if (box) {
            box.innerHTML = text;
            box.scrollTop = box.scrollHeight;
        }
    },

    setImg: function (action) {
        let age = this.state.age;
        let displayAge = 6;

        // Valid Age Buckets (No gaps!)
        if (age >= 18) displayAge = 18;
        else if (age >= 15) displayAge = 15;
        else if (age >= 12) displayAge = 12;
        else displayAge = 6; // 6-11

        const base = `assets/age${displayAge}_${action}`;
        const img = document.getElementById('main-img');
        const ph = document.getElementById('placeholder');

        if (img && ph) {
            img.style.display = 'block';
            ph.style.display = 'none';

            // Smart Load: Try PNG, fallback to JPG
            img.onerror = () => {
                img.onerror = () => {
                    // Fallback to placeholder if both fail
                    img.style.display = 'none';
                    ph.style.display = 'flex';
                };
                img.src = `${base}.jpg`;
            };
            img.src = `${base}.png`;
        }
    },

    setBusy: function (busy) {
        this.state.isProcessing = busy;
        document.querySelectorAll('.btn-action').forEach(btn => {
            btn.disabled = busy;
            btn.style.opacity = busy ? '0.5' : '1';
        });
    },

    // --- Save System (LocalStorage) ---
    saveGame: function () {
        if (this.state.isOver) {
            alert("終了したゲームはセーブできません。");
            return;
        }
        try {
            const data = JSON.stringify(this.state);
            localStorage.setItem('noa_growth_v6_save', data);
            this.log("<span style='color:cyan;'>【SYSTEM】セーブ完了しました。(LocalStorage)</span>");
            alert("セーブしました！");
        } catch (e) {
            console.error("Save failed:", e);
            alert("セーブに失敗しました。");
        }
    },

    loadGame: function () {
        try {
            const data = localStorage.getItem('noa_growth_v6_save');
            if (!data) {
                alert("セーブデータが見つかりません。");
                return;
            }
            const loadedState = JSON.parse(data);

            // Restore State
            this.state = loadedState;
            this.log("<span style='color:cyan;'>【SYSTEM】ロード完了。再開します。</span>");

            // Refresh UI
            this.render();
            // Restore Image based on loaded age behavior
            this.setImg('neutral');

            // Sync Audio
            if (this.state.age >= 15) this.audioSys.play('age15');
            else if (this.state.age >= 12) this.audioSys.play('age12');
            else this.audioSys.play('age6');

            alert("ロードしました！");
        } catch (e) {
            console.error("Load failed:", e);
            alert("ロードに失敗しました。データ破損の可能性があります。");
        }
    }
};

// Global Exposure
window.NoaGame = NoaGame;

// Universal Init
window.addEventListener('load', function () {
    if (window.NoaGame && window.NoaGame.init) {
        window.NoaGame.init();
    }
});
