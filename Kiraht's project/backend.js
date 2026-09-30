/**
 * ============================================================
 * ATOMIC BOOM — ORBITAL DEFENSE ARCADE ENGINE
 * ============================================================
 * Conceived & Directed by Mohamed Tharik
 * Engineered & Powered by KIRAHT AI
 */

// Canvas & Engine Context
const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');

// UI Element References
const hullBar = document.getElementById('hullBar');
const shieldIndicator = document.getElementById('shieldIndicator');
const weaponLevelBadge = document.getElementById('weaponLevelBadge');
const scoreDisplay = document.getElementById('scoreDisplay');
const multiplierDisplay = document.getElementById('multiplierDisplay');
const waveDisplay = document.getElementById('waveDisplay');
const highScoreDisplay = document.getElementById('highScoreDisplay');
const reactorBar = document.getElementById('reactorBar');
const reactorPercent = document.getElementById('reactorPercent');
const reactorReadyPrompt = document.getElementById('reactorReadyPrompt');
const soundToggleBtn = document.getElementById('soundToggleBtn');
const pauseBtn = document.getElementById('pauseBtn');

// Modals
const startModal = document.getElementById('startModal');
const pauseModal = document.getElementById('pauseModal');
const gameOverModal = document.getElementById('gameOverModal');
const startGameBtn = document.getElementById('startGameBtn');
const resumeBtn = document.getElementById('resumeBtn');
const restartFromPauseBtn = document.getElementById('restartFromPauseBtn');
const retryGameBtn = document.getElementById('retryGameBtn');
const toastBanner = document.getElementById('toastBanner');

// Final Stats Displays
const finalScoreDisplay = document.getElementById('finalScoreDisplay');
const finalWaveDisplay = document.getElementById('finalWaveDisplay');
const finalKillsDisplay = document.getElementById('finalKillsDisplay');
const finalBoomsDisplay = document.getElementById('finalBoomsDisplay');
const newHighscoreBadge = document.getElementById('newHighscoreBadge');

// ============================================================
// 1. PROCEDURAL SOUND SYNTHESIZER (WEB AUDIO API)
// ============================================================
class SoundEngine {
    constructor() {
        this.ctx = null;
        this.muted = false;
    }

    init() {
        if (!this.ctx) {
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            this.ctx = new AudioContext();
        }
        if (this.ctx && this.ctx.state === 'suspended') {
            this.ctx.resume();
        }
    }

    toggleMute() {
        this.muted = !this.muted;
        soundToggleBtn.textContent = this.muted ? "🔇 MUTED" : "🔊 AUDIO";
        showToast(this.muted ? "Sound Effects Muted" : "Sound Effects Enabled");
    }

    playLaser() {
        if (this.muted || !this.ctx) return;
        const now = this.ctx.currentTime;
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();

        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(880, now);
        osc.frequency.exponentialRampToValueAtTime(110, now + 0.12);

        gain.gain.setValueAtTime(0.15, now);
        gain.gain.exponentialRampToValueAtTime(0.01, now + 0.12);

        osc.connect(gain);
        gain.connect(this.ctx.destination);
        osc.start(now);
        osc.stop(now + 0.12);
    }

    playExplosion(isLarge = false) {
        if (this.muted || !this.ctx) return;
        const now = this.ctx.currentTime;
        const duration = isLarge ? 0.6 : 0.25;
        const bufferSize = this.ctx.sampleRate * duration;
        const buffer = this.ctx.createBuffer(1, bufferSize, this.ctx.sampleRate);
        const data = buffer.getChannelData(0);

        for (let i = 0; i < bufferSize; i++) {
            data[i] = Math.random() * 2 - 1;
        }

        const noise = this.ctx.createBufferSource();
        noise.buffer = buffer;

        const filter = this.ctx.createBiquadFilter();
        filter.type = 'lowpass';
        filter.frequency.setValueAtTime(isLarge ? 300 : 800, now);
        filter.frequency.exponentialRampToValueAtTime(40, now + duration);

        const gain = this.ctx.createGain();
        gain.gain.setValueAtTime(isLarge ? 0.4 : 0.2, now);
        gain.gain.exponentialRampToValueAtTime(0.01, now + duration);

        noise.connect(filter);
        filter.connect(gain);
        gain.connect(this.ctx.destination);
        noise.start(now);
    }

    playAtomicBoom() {
        if (this.muted || !this.ctx) return;
        const now = this.ctx.currentTime;

        // Sub-bass sine sweep
        const subOsc = this.ctx.createOscillator();
        const subGain = this.ctx.createGain();
        subOsc.type = 'sine';
        subOsc.frequency.setValueAtTime(180, now);
        subOsc.frequency.exponentialRampToValueAtTime(25, now + 1.2);
        subGain.gain.setValueAtTime(0.5, now);
        subGain.gain.exponentialRampToValueAtTime(0.01, now + 1.2);
        subOsc.connect(subGain);
        subGain.connect(this.ctx.destination);
        subOsc.start(now);
        subOsc.stop(now + 1.2);

        // Huge thunderous distortion noise
        this.playExplosion(true);
    }

    playPickup() {
        if (this.muted || !this.ctx) return;
        const now = this.ctx.currentTime;
        const notes = [523.25, 659.25, 783.99, 1046.50]; // C5, E5, G5, C6
        notes.forEach((freq, i) => {
            const osc = this.ctx.createOscillator();
            const gain = this.ctx.createGain();
            osc.type = 'triangle';
            osc.frequency.setValueAtTime(freq, now + i * 0.04);
            gain.gain.setValueAtTime(0.12, now + i * 0.04);
            gain.gain.exponentialRampToValueAtTime(0.01, now + i * 0.04 + 0.15);
            osc.connect(gain);
            gain.connect(this.ctx.destination);
            osc.start(now + i * 0.04);
            osc.stop(now + i * 0.04 + 0.15);
        });
    }

    playShieldHit() {
        if (this.muted || !this.ctx) return;
        const now = this.ctx.currentTime;
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(440, now);
        osc.frequency.exponentialRampToValueAtTime(80, now + 0.15);
        gain.gain.setValueAtTime(0.25, now);
        gain.gain.exponentialRampToValueAtTime(0.01, now + 0.15);
        osc.connect(gain);
        gain.connect(this.ctx.destination);
        osc.start(now);
        osc.stop(now + 0.15);
    }
}

const sound = new SoundEngine();

// ============================================================
// 2. GAME STATE & GLOBALS
// ============================================================
let gameState = 'START'; // 'START', 'PLAYING', 'PAUSED', 'GAMEOVER'
let score = 0;
let highScore = parseInt(localStorage.getItem('atomic_boom_highscore') || '0', 10);
let scoreMultiplier = 1.0;
let multTimer = 0;
let currentWave = 1;
let enemiesKilled = 0;
let atomicBoomsFired = 0;
let screenShake = 0;
let screenFlash = 0;

// Resize canvas to full viewport
function resizeCanvas() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
}
window.addEventListener('resize', resizeCanvas);
resizeCanvas();

// ============================================================
// 3. BACKGROUND STARFIELD (PARALLAX EFFECT)
// ============================================================
const stars = [];
for (let i = 0; i < 140; i++) {
    stars.push({
        x: Math.random() * window.innerWidth,
        y: Math.random() * window.innerHeight,
        size: Math.random() * 2 + 0.5,
        speed: Math.random() * 1.5 + 0.3,
        alpha: Math.random() * 0.8 + 0.2
    });
}

function updateStars() {
    for (let s of stars) {
        s.y += s.speed;
        if (s.y > canvas.height) {
            s.y = 0;
            s.x = Math.random() * canvas.width;
        }
    }
}

function drawStars() {
    ctx.save();
    for (let s of stars) {
        ctx.fillStyle = `rgba(224, 242, 254, ${s.alpha})`;
        ctx.shadowBlur = s.size > 1.8 ? 6 : 0;
        ctx.shadowColor = '#00f0ff';
        ctx.beginPath();
        ctx.arc(s.x, s.y, s.size, 0, Math.PI * 2);
        ctx.fill();
    }
    ctx.restore();
}

// ============================================================
// 4. PLAYER SPACESHIP ENTITY
// ============================================================
class Player {
    constructor() {
        this.width = 46;
        this.height = 54;
        this.x = canvas.width / 2;
        this.y = canvas.height - 120;
        this.vx = 0;
        this.speed = 8.5;
        this.maxHealth = 100;
        this.health = 100;
        this.maxShield = 100;
        this.shield = 100;
        this.atomicReactor = 0; // 0 to 100
        this.weaponLevel = 1;   // 1: single, 2: dual, 3: triple spread
        this.powerupTimer = 0;
        this.lastShotTime = 0;
        this.fireInterval = 140; // ms
        this.hitFlash = 0;
    }

    reset() {
        this.x = canvas.width / 2;
        this.y = canvas.height - 120;
        this.vx = 0;
        this.health = 100;
        this.shield = 100;
        this.atomicReactor = 0;
        this.weaponLevel = 1;
        this.powerupTimer = 0;
        this.hitFlash = 0;
    }

    takeDamage(amount) {
        if (this.shield > 0) {
            this.shield -= amount;
            sound.playShieldHit();
            if (this.shield < 0) {
                this.health += this.shield;
                this.shield = 0;
            }
        } else {
            this.health -= amount;
            sound.playExplosion(false);
        }
        this.hitFlash = 10;
        screenShake = 12;
        if (this.health <= 0) {
            this.health = 0;
            triggerGameOver();
        }
        updateHUD();
    }

    addReactorEnergy(amount) {
        this.atomicReactor = Math.min(100, this.atomicReactor + amount);
        updateHUD();
        if (this.atomicReactor >= 100) {
            reactorReadyPrompt.classList.remove('hidden');
        }
    }

    triggerAtomicBoom() {
        if (this.atomicReactor < 100) {
            showToast("☢️ Atomic Reactor is charging! (" + Math.floor(this.atomicReactor) + "%)");
            return;
        }

        this.atomicReactor = 0;
        reactorReadyPrompt.classList.add('hidden');
        atomicBoomsFired++;
        updateHUD();

        sound.playAtomicBoom();
        screenFlash = 1.0;
        screenShake = 35;

        // Spawn massive central shockwave
        shockwaves.push(new Shockwave(canvas.width / 2, canvas.height / 2, 800, '#39ff14'));
        shockwaves.push(new Shockwave(canvas.width / 2, canvas.height / 2, 600, '#00f0ff'));

        // Vaporize all enemies on screen with high score
        let vaporized = 0;
        for (let enemy of enemies) {
            createExplosion(enemy.x, enemy.y, enemy.color, 35);
            score += Math.floor(enemy.points * 2.5 * scoreMultiplier);
            vaporized++;
        }
        enemies = [];
        enemyProjectiles = [];

        // Spawn reward particles
        for (let i = 0; i < 70; i++) {
            particles.push(new Particle(canvas.width / 2, canvas.height / 2, '#39ff14', 12));
        }

        showToast(`💥 ATOMIC BOOM DETONATED! (${vaporized} Obliterated)`);
    }

    update() {
        // Keyboard controls
        if (keys['ArrowLeft'] || keys['KeyA']) this.vx = -this.speed;
        else if (keys['ArrowRight'] || keys['KeyD']) this.vx = this.speed;
        else this.vx *= 0.8;

        this.x += this.vx;

        // Boundary clamp
        if (this.x < this.width / 2) this.x = this.width / 2;
        if (this.x > canvas.width - this.width / 2) this.x = canvas.width - this.width / 2;

        // Auto/Hold Fire
        const now = Date.now();
        if ((keys['ArrowUp'] || keys['KeyW'] || mouseDown) && now - this.lastShotTime > this.fireInterval) {
            this.shoot();
            this.lastShotTime = now;
        }

        // Powerup expiration timer
        if (this.powerupTimer > 0) {
            this.powerupTimer--;
            if (this.powerupTimer <= 0) {
                this.weaponLevel = 1;
                weaponLevelBadge.textContent = "CANNON: LVL 1";
                weaponLevelBadge.style.color = "#ffe600";
            }
        }

        if (this.hitFlash > 0) this.hitFlash--;
    }

    shoot() {
        sound.playLaser();
        const topY = this.y - this.height / 2;

        if (this.weaponLevel === 1) {
            bullets.push(new Bullet(this.x, topY, 0, -14, '#00f0ff', 18));
        } else if (this.weaponLevel === 2) {
            bullets.push(new Bullet(this.x - 12, topY, 0, -14, '#00f0ff', 18));
            bullets.push(new Bullet(this.x + 12, topY, 0, -14, '#00f0ff', 18));
        } else if (this.weaponLevel >= 3) {
            bullets.push(new Bullet(this.x, topY, 0, -15, '#39ff14', 24));
            bullets.push(new Bullet(this.x - 14, topY, -2.5, -14, '#00f0ff', 18));
            bullets.push(new Bullet(this.x + 14, topY, 2.5, -14, '#00f0ff', 18));
        }

        // Thruster sparks
        for (let i = 0; i < 2; i++) {
            particles.push(new Particle(this.x + (Math.random() * 8 - 4), this.y + this.height / 2, '#00f0ff', 2));
        }
    }

    draw() {
        ctx.save();
        ctx.translate(this.x, this.y);

        // Thruster glow animation
        const flameLength = 14 + Math.sin(Date.now() * 0.02) * 6;
        const thrusterGrad = ctx.createLinearGradient(0, this.height / 2, 0, this.height / 2 + flameLength);
        thrusterGrad.addColorStop(0, '#00f0ff');
        thrusterGrad.addColorStop(0.5, '#0077ff');
        thrusterGrad.addColorStop(1, 'transparent');
        ctx.fillStyle = thrusterGrad;
        ctx.beginPath();
        ctx.moveTo(-10, this.height / 2 - 4);
        ctx.lineTo(0, this.height / 2 + flameLength);
        ctx.lineTo(10, this.height / 2 - 4);
        ctx.fill();

        // Hull Body (Futuristic Cyber Interceptor)
        ctx.fillStyle = this.hitFlash > 0 ? '#ff0055' : '#0f172a';
        ctx.strokeStyle = '#00f0ff';
        ctx.lineWidth = 2;
        ctx.shadowBlur = 12;
        ctx.shadowColor = '#00f0ff';

        ctx.beginPath();
        ctx.moveTo(0, -this.height / 2); // Cockpit tip
        ctx.lineTo(this.width / 2, this.height / 2 - 10);
        ctx.lineTo(this.width / 4, this.height / 2);
        ctx.lineTo(0, this.height / 2 - 6);
        ctx.lineTo(-this.width / 4, this.height / 2);
        ctx.lineTo(-this.width / 2, this.height / 2 - 10);
        ctx.closePath();
        ctx.fill();
        ctx.stroke();

        // Cockpit canopy glow
        ctx.fillStyle = '#39ff14';
        ctx.beginPath();
        ctx.ellipse(0, -4, 5, 14, 0, 0, Math.PI * 2);
        ctx.fill();

        // Shield Bubble Overlay
        if (this.shield > 0) {
            ctx.strokeStyle = `rgba(0, 240, 255, ${0.3 + (this.shield / 100) * 0.4})`;
            ctx.lineWidth = 2.5;
            ctx.shadowBlur = 18;
            ctx.shadowColor = '#00f0ff';
            ctx.beginPath();
            ctx.arc(0, 0, this.height * 0.65, 0, Math.PI * 2);
            ctx.stroke();
        }

        ctx.restore();
    }
}

const player = new Player();

// ============================================================
// 5. BULLETS, PROJECTILES & SHOCKWAVES
// ============================================================
class Bullet {
    constructor(x, y, vx, vy, color, damage) {
        this.x = x;
        this.y = y;
        this.vx = vx;
        this.vy = vy;
        this.color = color;
        this.damage = damage;
        this.radius = 4;
    }

    update() {
        this.x += this.vx;
        this.y += this.vy;
    }

    draw() {
        ctx.save();
        ctx.fillStyle = '#ffffff';
        ctx.shadowBlur = 10;
        ctx.shadowColor = this.color;
        ctx.strokeStyle = this.color;
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
        ctx.fill();
        ctx.stroke();
        ctx.restore();
    }
}

let bullets = [];
let enemyProjectiles = [];

class Shockwave {
    constructor(x, y, maxRadius, color) {
        this.x = x;
        this.y = y;
        this.radius = 10;
        this.maxRadius = maxRadius;
        this.color = color;
        this.alpha = 1.0;
        this.speed = 18;
    }

    update() {
        this.radius += this.speed;
        this.alpha = Math.max(0, 1 - this.radius / this.maxRadius);
    }

    draw() {
        if (this.alpha <= 0) return;
        ctx.save();
        ctx.strokeStyle = this.color;
        ctx.globalAlpha = this.alpha;
        ctx.lineWidth = 8 * this.alpha;
        ctx.shadowBlur = 25;
        ctx.shadowColor = this.color;
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
        ctx.stroke();
        ctx.restore();
    }
}

let shockwaves = [];

// ============================================================
// 6. PARTICLES & FLOATING COMBAT TEXT
// ============================================================
class Particle {
    constructor(x, y, color, speedMul = 1) {
        this.x = x;
        this.y = y;
        const angle = Math.random() * Math.PI * 2;
        const speed = (Math.random() * 4 + 1.5) * speedMul;
        this.vx = Math.cos(angle) * speed;
        this.vy = Math.sin(angle) * speed;
        this.color = color;
        this.radius = Math.random() * 3.5 + 1.5;
        this.alpha = 1.0;
        this.decay = Math.random() * 0.03 + 0.015;
    }

    update() {
        this.x += this.vx;
        this.y += this.vy;
        this.vx *= 0.96;
        this.vy *= 0.96;
        this.alpha -= this.decay;
    }

    draw() {
        if (this.alpha <= 0) return;
        ctx.save();
        ctx.globalAlpha = this.alpha;
        ctx.fillStyle = this.color;
        ctx.shadowBlur = 8;
        ctx.shadowColor = this.color;
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
    }
}

let particles = [];

function createExplosion(x, y, color, count = 20) {
    for (let i = 0; i < count; i++) {
        particles.push(new Particle(x, y, color));
    }
}

class FloatingText {
    constructor(text, x, y, color = '#39ff14') {
        this.text = text;
        this.x = x;
        this.y = y;
        this.color = color;
        this.alpha = 1.0;
        this.vy = -1.6;
    }

    update() {
        this.y += this.vy;
        this.alpha -= 0.02;
    }

    draw() {
        if (this.alpha <= 0) return;
        ctx.save();
        ctx.globalAlpha = this.alpha;
        ctx.font = '700 16px "Orbitron", sans-serif';
        ctx.fillStyle = this.color;
        ctx.shadowBlur = 8;
        ctx.shadowColor = this.color;
        ctx.textAlign = 'center';
        ctx.fillText(this.text, this.x, this.y);
        ctx.restore();
    }
}

let floatingTexts = [];

// ============================================================
// 7. POWER-UPS & URANIUM CORES
// ============================================================
class Powerup {
    constructor(x, y, type) {
        this.x = x;
        this.y = y;
        this.type = type; // 'uranium', 'trishot', 'shield', 'nanobot'
        this.vy = 2.2;
        this.radius = 16;
        this.angle = 0;
    }

    update() {
        this.y += this.vy;
        this.angle += 0.04;
    }

    draw() {
        ctx.save();
        ctx.translate(this.x, this.y);
        ctx.rotate(this.angle);

        let icon = "☢️";
        let color = "#39ff14";
        if (this.type === 'trishot') { icon = "⚡"; color = "#ffe600"; }
        if (this.type === 'shield') { icon = "🛡️"; color = "#00f0ff"; }
        if (this.type === 'nanobot') { icon = "❤️"; color = "#ff0055"; }

        ctx.shadowBlur = 15;
        ctx.shadowColor = color;
        ctx.strokeStyle = color;
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(0, 0, this.radius, 0, Math.PI * 2);
        ctx.stroke();

        ctx.font = "18px sans-serif";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(icon, 0, 0);

        ctx.restore();
    }
}

let powerups = [];

// ============================================================
// 8. ENEMY WAVES & ARCHETYPES
// ============================================================
class Enemy {
    constructor(type, x, y) {
        this.type = type;
        this.x = x;
        this.y = y;
        this.initType(type);
    }

    initType(type) {
        if (type === 'scout') {
            this.width = 32;
            this.height = 32;
            this.hp = 25;
            this.maxHp = 25;
            this.vy = 3.2 + currentWave * 0.2;
            this.color = '#00f0ff';
            this.points = 100;
            this.frequency = 0.05;
            this.amplitude = 3.5;
            this.phase = Math.random() * 10;
        } else if (type === 'asteroid') {
            this.width = 44;
            this.height = 44;
            this.hp = 50;
            this.maxHp = 50;
            this.vy = 2.0;
            this.color = '#ff7700';
            this.points = 180;
            this.rotation = 0;
            this.rotSpeed = 0.02;
        } else if (type === 'dreadnought') {
            this.width = 54;
            this.height = 46;
            this.hp = 120;
            this.maxHp = 120;
            this.vy = 1.3;
            this.color = '#ff0055';
            this.points = 350;
            this.shootTimer = 0;
            this.shootInterval = 90; // frames
        } else if (type === 'boss') {
            this.width = 140;
            this.height = 90;
            this.hp = 800 + currentWave * 200;
            this.maxHp = this.hp;
            this.vy = 0.8;
            this.color = '#ffe600';
            this.points = 2500;
            this.shootTimer = 0;
            this.targetY = 140;
            this.moveDir = 1;
        }
    }

    update() {
        if (this.type === 'scout') {
            this.y += this.vy;
            this.x += Math.sin(this.y * this.frequency + this.phase) * this.amplitude;
        } else if (this.type === 'asteroid') {
            this.y += this.vy;
            this.rotation += this.rotSpeed;
        } else if (this.type === 'dreadnought') {
            this.y += this.vy;
            this.shootTimer++;
            if (this.shootTimer >= this.shootInterval && this.y > 50 && this.y < canvas.height - 200) {
                this.shootTimer = 0;
                enemyProjectiles.push(new Bullet(this.x, this.y + this.height / 2, 0, 6, '#ff0055', 15));
            }
        } else if (this.type === 'boss') {
            if (this.y < this.targetY) {
                this.y += this.vy;
            } else {
                this.x += 2.5 * this.moveDir;
                if (this.x > canvas.width - this.width / 2 - 20) this.moveDir = -1;
                if (this.x < this.width / 2 + 20) this.moveDir = 1;
            }
            this.shootTimer++;
            if (this.shootTimer >= 45) {
                this.shootTimer = 0;
                // Triple bullet barrage
                enemyProjectiles.push(new Bullet(this.x - 30, this.y + this.height / 2, -1.8, 6.5, '#ff0055', 18));
                enemyProjectiles.push(new Bullet(this.x, this.y + this.height / 2, 0, 7.5, '#ffe600', 20));
                enemyProjectiles.push(new Bullet(this.x + 30, this.y + this.height / 2, 1.8, 6.5, '#ff0055', 18));
            }
        }
    }

    draw() {
        ctx.save();
        ctx.translate(this.x, this.y);

        if (this.type === 'scout') {
            ctx.strokeStyle = this.color;
            ctx.fillStyle = '#0a1628';
            ctx.lineWidth = 2;
            ctx.shadowBlur = 10;
            ctx.shadowColor = this.color;
            ctx.beginPath();
            ctx.moveTo(0, this.height / 2);
            ctx.lineTo(-this.width / 2, -this.height / 2);
            ctx.lineTo(0, -this.height / 4);
            ctx.lineTo(this.width / 2, -this.height / 2);
            ctx.closePath();
            ctx.fill();
            ctx.stroke();
        } else if (this.type === 'asteroid') {
            ctx.rotate(this.rotation);
            ctx.strokeStyle = this.color;
            ctx.fillStyle = '#1c1917';
            ctx.lineWidth = 2.5;
            ctx.shadowBlur = 12;
            ctx.shadowColor = this.color;
            ctx.beginPath();
            ctx.arc(0, 0, this.width / 2, 0, Math.PI * 2);
            ctx.fill();
            ctx.stroke();
            // Core radiation glow
            ctx.fillStyle = '#ff7700';
            ctx.beginPath();
            ctx.arc(0, 0, 8, 0, Math.PI * 2);
            ctx.fill();
        } else if (this.type === 'dreadnought') {
            ctx.strokeStyle = this.color;
            ctx.fillStyle = '#1e1124';
            ctx.lineWidth = 2.5;
            ctx.shadowBlur = 14;
            ctx.shadowColor = this.color;
            ctx.beginPath();
            ctx.moveTo(0, this.height / 2);
            ctx.lineTo(-this.width / 2, 0);
            ctx.lineTo(-this.width / 3, -this.height / 2);
            ctx.lineTo(this.width / 3, -this.height / 2);
            ctx.lineTo(this.width / 2, 0);
            ctx.closePath();
            ctx.fill();
            ctx.stroke();
        } else if (this.type === 'boss') {
            ctx.strokeStyle = this.color;
            ctx.fillStyle = '#181824';
            ctx.lineWidth = 3;
            ctx.shadowBlur = 20;
            ctx.shadowColor = this.color;
            ctx.beginPath();
            ctx.rect(-this.width / 2, -this.height / 2, this.width, this.height);
            ctx.fill();
            ctx.stroke();

            // Boss Health Bar above ship
            const barW = this.width;
            ctx.fillStyle = 'rgba(0,0,0,0.6)';
            ctx.fillRect(-barW / 2, -this.height / 2 - 16, barW, 8);
            ctx.fillStyle = '#ff0055';
            ctx.fillRect(-barW / 2, -this.height / 2 - 16, barW * (this.hp / this.maxHp), 8);
            ctx.strokeStyle = '#ffffff';
            ctx.strokeRect(-barW / 2, -this.height / 2 - 16, barW, 8);
        }

        ctx.restore();
    }
}

let enemies = [];
let waveSpawning = false;
let waveEnemiesTotal = 0;
let waveEnemiesSpawned = 0;
let waveSpawnInterval = 1000;
let lastSpawnTime = 0;

function startWave(waveNum) {
    currentWave = waveNum;
    waveDisplay.textContent = `WAVE ${currentWave}`;
    waveEnemiesSpawned = 0;
    waveSpawning = true;

    const isBossWave = (currentWave % 5 === 0);
    waveEnemiesTotal = isBossWave ? 1 : (8 + currentWave * 4);
    waveSpawnInterval = Math.max(350, 1200 - currentWave * 80);

    showToast(isBossWave ? `⚠️ BOSS ALERT: TITAN CORE INCOMING!` : `🚀 WAVE ${currentWave} ENGAGED!`);
}

function spawnEnemy() {
    if (currentWave % 5 === 0) {
        // Boss Wave
        enemies.push(new Enemy('boss', canvas.width / 2, -100));
        waveEnemiesSpawned = waveEnemiesTotal;
        waveSpawning = false;
        return;
    }

    const rand = Math.random();
    const x = Math.random() * (canvas.width - 120) + 60;
    let type = 'scout';

    if (rand < 0.45) type = 'scout';
    else if (rand < 0.75) type = 'asteroid';
    else type = 'dreadnought';

    enemies.push(new Enemy(type, x, -50));
    waveEnemiesSpawned++;

    if (waveEnemiesSpawned >= waveEnemiesTotal) {
        waveSpawning = false;
    }
}

// ============================================================
// 9. COLLISION DETECTION & LOGIC
// ============================================================
function checkCollisions() {
    // 1. Player Bullets vs Enemies
    for (let bIdx = bullets.length - 1; bIdx >= 0; bIdx--) {
        const bullet = bullets[bIdx];
        for (let eIdx = enemies.length - 1; eIdx >= 0; eIdx--) {
            const enemy = enemies[eIdx];
            const dist = Math.hypot(bullet.x - enemy.x, bullet.y - enemy.y);
            const hitThreshold = (enemy.width / 2) + bullet.radius;

            if (dist < hitThreshold) {
                enemy.hp -= bullet.damage;
                createExplosion(bullet.x, bullet.y, bullet.color, 4);
                bullets.splice(bIdx, 1);

                if (enemy.hp <= 0) {
                    // Enemy Destroyed
                    enemiesKilled++;
                    enemies.splice(eIdx, 1);
                    sound.playExplosion(enemy.type === 'boss' || enemy.type === 'dreadnought');
                    createExplosion(enemy.x, enemy.y, enemy.color, enemy.type === 'boss' ? 50 : 20);

                    // Score calculation
                    const earned = Math.floor(enemy.points * scoreMultiplier);
                    score += earned;
                    floatingTexts.push(new FloatingText(`+${earned}`, enemy.x, enemy.y, enemy.color));

                    // Combo Multiplier
                    scoreMultiplier = Math.min(4.0, scoreMultiplier + 0.1);
                    multTimer = 180; // 3 seconds

                    // Charge Atomic Reactor
                    player.addReactorEnergy(enemy.type === 'boss' ? 50 : 8);

                    // Chance to drop powerups
                    const dropChance = Math.random();
                    if (dropChance < 0.22) {
                        const types = ['uranium', 'trishot', 'shield', 'nanobot'];
                        const chosen = types[Math.floor(Math.random() * types.length)];
                        powerups.push(new Powerup(enemy.x, enemy.y, chosen));
                    }
                }
                break;
            }
        }
    }

    // 2. Enemy Projectiles vs Player
    for (let pIdx = enemyProjectiles.length - 1; pIdx >= 0; pIdx--) {
        const proj = enemyProjectiles[pIdx];
        const dist = Math.hypot(proj.x - player.x, proj.y - player.y);
        if (dist < (player.width / 2) + proj.radius) {
            player.takeDamage(proj.damage);
            createExplosion(proj.x, proj.y, proj.color, 6);
            enemyProjectiles.splice(pIdx, 1);
        }
    }

    // 3. Enemies vs Player (Ramming)
    for (let eIdx = enemies.length - 1; eIdx >= 0; eIdx--) {
        const enemy = enemies[eIdx];
        const dist = Math.hypot(enemy.x - player.x, enemy.y - player.y);
        if (dist < (enemy.width / 2) + (player.width / 2)) {
            player.takeDamage(35);
            createExplosion(enemy.x, enemy.y, enemy.color, 15);
            if (enemy.type !== 'boss') {
                enemies.splice(eIdx, 1);
            }
        }
    }

    // 4. Powerups vs Player
    for (let puIdx = powerups.length - 1; puIdx >= 0; puIdx--) {
        const pu = powerups[puIdx];
        const dist = Math.hypot(pu.x - player.x, pu.y - player.y);
        if (dist < pu.radius + (player.width / 2)) {
            sound.playPickup();
            if (pu.type === 'uranium') {
                player.addReactorEnergy(25);
                floatingTexts.push(new FloatingText("☢️ URANIUM +25%", player.x, player.y - 30, '#39ff14'));
            } else if (pu.type === 'trishot') {
                player.weaponLevel = 3;
                player.powerupTimer = 500; // ~8 seconds
                weaponLevelBadge.textContent = "SPREAD CANNON";
                weaponLevelBadge.style.color = "#39ff14";
                floatingTexts.push(new FloatingText("⚡ SPREAD CANNON!", player.x, player.y - 30, '#ffe600'));
            } else if (pu.type === 'shield') {
                player.shield = Math.min(100, player.shield + 40);
                updateHUD();
                floatingTexts.push(new FloatingText("🛡️ SHIELD RECHARGED", player.x, player.y - 30, '#00f0ff'));
            } else if (pu.type === 'nanobot') {
                player.health = Math.min(100, player.health + 30);
                updateHUD();
                floatingTexts.push(new FloatingText("❤️ HULL REPAIRED", player.x, player.y - 30, '#ff0055'));
            }
            powerups.splice(puIdx, 1);
        }
    }
}

// ============================================================
// 10. HUD & NOTIFICATIONS
// ============================================================
function updateHUD() {
    hullBar.style.width = `${Math.max(0, player.health)}%`;
    if (player.health < 30) {
        hullBar.style.background = '#ff0055';
    } else {
        hullBar.style.background = 'linear-gradient(90deg, #ff0055 0%, #39ff14 70%)';
    }

    shieldIndicator.textContent = player.shield > 0 ? `SHIELD: ${Math.floor(player.shield)}%` : `SHIELD: OFFLINE`;
    shieldIndicator.style.color = player.shield > 0 ? '#00f0ff' : '#94a3b8';

    scoreDisplay.textContent = String(score).padStart(6, '0');
    multiplierDisplay.textContent = `${scoreMultiplier.toFixed(1)}x`;
    highScoreDisplay.textContent = String(highScore).padStart(6, '0');

    reactorBar.style.width = `${player.atomicReactor}%`;
    reactorPercent.textContent = `${Math.floor(player.atomicReactor)}%`;
}

function showToast(msg) {
    toastBanner.textContent = msg;
    toastBanner.classList.remove('hidden');
    clearTimeout(toastBanner.timer);
    toastBanner.timer = setTimeout(() => {
        toastBanner.classList.add('hidden');
    }, 2800);
}

// ============================================================
// 11. GAME OVER & HIGH SCORE
// ============================================================
function triggerGameOver() {
    gameState = 'GAMEOVER';
    finalScoreDisplay.textContent = score;
    finalWaveDisplay.textContent = currentWave;
    finalKillsDisplay.textContent = enemiesKilled;
    finalBoomsDisplay.textContent = atomicBoomsFired;

    if (score > highScore) {
        highScore = score;
        localStorage.setItem('atomic_boom_highscore', String(highScore));
        newHighscoreBadge.classList.remove('hidden');
    } else {
        newHighscoreBadge.classList.add('hidden');
    }

    gameOverModal.classList.remove('hidden');
}

// ============================================================
// 12. INPUT HANDLERS
// ============================================================
const keys = {};
let mouseDown = false;

window.addEventListener('keydown', (e) => {
    keys[e.code] = true;

    // Detonate Atomic Boom
    if (e.code === 'Space' || e.code === 'KeyB') {
        if (gameState === 'PLAYING') {
            player.triggerAtomicBoom();
        }
    }

    // Pause toggle
    if (e.code === 'KeyP' || e.code === 'Escape') {
        if (gameState === 'PLAYING') {
            togglePause();
        } else if (gameState === 'PAUSED') {
            togglePause();
        }
    }
});

window.addEventListener('keyup', (e) => {
    keys[e.code] = false;
});

canvas.addEventListener('mousemove', (e) => {
    if (gameState === 'PLAYING') {
        player.x = e.clientX;
    }
});

canvas.addEventListener('mousedown', (e) => {
    if (e.button === 0) mouseDown = true;
});

window.addEventListener('mouseup', () => {
    mouseDown = false;
});

// Touch controls for mobile / tablets
canvas.addEventListener('touchmove', (e) => {
    if (gameState === 'PLAYING' && e.touches[0]) {
        player.x = e.touches[0].clientX;
    }
});

canvas.addEventListener('touchstart', (e) => {
    sound.init();
    mouseDown = true;
});

canvas.addEventListener('touchend', () => {
    mouseDown = false;
});

// UI Button Clicks
startGameBtn.addEventListener('click', () => {
    sound.init();
    startModal.classList.add('hidden');
    gameState = 'PLAYING';
    resetGame();
});

resumeBtn.addEventListener('click', () => {
    togglePause();
});

restartFromPauseBtn.addEventListener('click', () => {
    pauseModal.classList.add('hidden');
    gameState = 'PLAYING';
    resetGame();
});

retryGameBtn.addEventListener('click', () => {
    gameOverModal.classList.add('hidden');
    gameState = 'PLAYING';
    resetGame();
});

soundToggleBtn.addEventListener('click', () => {
    sound.init();
    sound.toggleMute();
});

pauseBtn.addEventListener('click', () => {
    togglePause();
});

function togglePause() {
    if (gameState === 'PLAYING') {
        gameState = 'PAUSED';
        document.getElementById('pauseScore').textContent = score;
        document.getElementById('pauseWave').textContent = `Wave ${currentWave}`;
        pauseModal.classList.remove('hidden');
    } else if (gameState === 'PAUSED') {
        gameState = 'PLAYING';
        pauseModal.classList.add('hidden');
    }
}

function resetGame() {
    score = 0;
    scoreMultiplier = 1.0;
    currentWave = 1;
    enemiesKilled = 0;
    atomicBoomsFired = 0;
    bullets = [];
    enemyProjectiles = [];
    enemies = [];
    particles = [];
    floatingTexts = [];
    powerups = [];
    shockwaves = [];
    player.reset();
    updateHUD();
    startWave(1);
}

// ============================================================
// 13. MAIN ENGINE LOOP
// ============================================================
let lastTime = performance.now();

function gameLoop(now) {
    const dt = now - lastTime;
    lastTime = now;

    // Screen Shake Offset
    let offsetX = 0;
    let offsetY = 0;
    if (screenShake > 0) {
        offsetX = (Math.random() - 0.5) * screenShake;
        offsetY = (Math.random() - 0.5) * screenShake;
        screenShake *= 0.9;
        if (screenShake < 0.5) screenShake = 0;
    }

    ctx.save();
    ctx.translate(offsetX, offsetY);

    // Clear Canvas
    ctx.clearRect(-20, -20, canvas.width + 40, canvas.height + 40);

    // Update & Draw Background Starfield
    updateStars();
    drawStars();

    if (gameState === 'PLAYING') {
        // Multiplier Decay
        if (multTimer > 0) {
            multTimer--;
            if (multTimer <= 0) {
                scoreMultiplier = 1.0;
                multiplierDisplay.textContent = "1.0x";
            }
        }

        // Enemy Wave Spawner
        const currentTime = Date.now();
        if (waveSpawning && currentTime - lastSpawnTime > waveSpawnInterval) {
            spawnEnemy();
            lastSpawnTime = currentTime;
        }

        // Wave Completion Check
        if (!waveSpawning && enemies.length === 0) {
            startWave(currentWave + 1);
        }

        // Update & Draw Player
        player.update();
        player.draw();

        // Update & Draw Bullets
        for (let i = bullets.length - 1; i >= 0; i--) {
            bullets[i].update();
            bullets[i].draw();
            if (bullets[i].y < -20) bullets.splice(i, 1);
        }

        // Update & Draw Enemy Projectiles
        for (let i = enemyProjectiles.length - 1; i >= 0; i--) {
            enemyProjectiles[i].update();
            enemyProjectiles[i].draw();
            if (enemyProjectiles[i].y > canvas.height + 20) enemyProjectiles.splice(i, 1);
        }

        // Update & Draw Enemies
        for (let i = enemies.length - 1; i >= 0; i--) {
            enemies[i].update();
            enemies[i].draw();
            if (enemies[i].y > canvas.height + 60) {
                // Enemy breached defenses
                player.takeDamage(10);
                enemies.splice(i, 1);
            }
        }

        // Update & Draw Powerups
        for (let i = powerups.length - 1; i >= 0; i--) {
            powerups[i].update();
            powerups[i].draw();
            if (powerups[i].y > canvas.height + 40) powerups.splice(i, 1);
        }

        // Collisions
        checkCollisions();
    } else {
        // Still draw player in start/gameover states
        player.draw();
    }

    // Update & Draw Shockwaves
    for (let i = shockwaves.length - 1; i >= 0; i--) {
        shockwaves[i].update();
        shockwaves[i].draw();
        if (shockwaves[i].alpha <= 0) shockwaves.splice(i, 1);
    }

    // Update & Draw Particles
    for (let i = particles.length - 1; i >= 0; i--) {
        particles[i].update();
        particles[i].draw();
        if (particles[i].alpha <= 0) particles.splice(i, 1);
    }

    // Update & Draw Floating Texts
    for (let i = floatingTexts.length - 1; i >= 0; i--) {
        floatingTexts[i].update();
        floatingTexts[i].draw();
        if (floatingTexts[i].alpha <= 0) floatingTexts.splice(i, 1);
    }

    // Screen Flash (Atomic Detonation)
    if (screenFlash > 0) {
        ctx.fillStyle = `rgba(255, 255, 255, ${screenFlash})`;
        ctx.fillRect(-20, -20, canvas.width + 40, canvas.height + 40);
        screenFlash *= 0.88;
        if (screenFlash < 0.02) screenFlash = 0;
    }

    ctx.restore();

    requestAnimationFrame(gameLoop);
}

// Start Game Loop
requestAnimationFrame(gameLoop);