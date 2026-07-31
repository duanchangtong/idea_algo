/**
 * 具身智能·生活体验创意站 - 前端交互逻辑
 */

// ===== 全局状态 =====
let currentUser = JSON.parse(localStorage.getItem("painpoint_user") || "null");
let currentCategory = "全部";
let currentSort = "latest";
let selectedAvatar = "😊";
let selectedCategory = "衣";
let selectedEmotion = "";
let selectedLocation = "";

// ===== 初始化 =====
document.addEventListener("DOMContentLoaded", () => {
    initUserUI();
    loadIdeas();
    loadStats();
    loadRewardTiers();
    loadRandomIdea();
    bindFilterEvents();
    bindEmotionEvents();
    bindLocationEvents();
});

// ===== 用户相关 =====
function initUserUI() {
    if (currentUser) {
        document.getElementById("btn-login").classList.add("hidden");
        document.getElementById("user-info").classList.remove("hidden");
        document.getElementById("user-avatar").textContent = currentUser.avatar;
        document.getElementById("user-name").textContent = currentUser.nickname;
        document.getElementById("user-title").textContent =
            `${currentUser.badge} ${currentUser.title}`;
    }
}

function showLogin() {
    document.getElementById("login-modal").classList.remove("hidden");
}

function hideLogin() {
    document.getElementById("login-modal").classList.add("hidden");
}

// 头像选择
document.querySelectorAll(".avatar-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
        document.querySelectorAll(".avatar-btn").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        selectedAvatar = btn.dataset.avatar;
    });
});

async function doRegister() {
    const nickname = document.getElementById("input-nickname").value.trim();
    if (!nickname) {
        alert("请输入昵称");
        return;
    }
    try {
        const res = await fetch("/api/register", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ nickname, avatar: selectedAvatar }),
        });
        const user = await res.json();
        if (user.error) {
            alert(user.error);
            return;
        }
        currentUser = user;
        localStorage.setItem("painpoint_user", JSON.stringify(user));
        hideLogin();
        initUserUI();
        loadIdeas();
    } catch (e) {
        alert("注册失败，请重试");
    }
}

// ===== 标签页切换 =====
function switchTab(tabName) {
    document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
    document.querySelectorAll(".tab-content").forEach((t) => t.classList.remove("active"));
    document.querySelector(`.tab[data-tab="${tabName}"]`).classList.add("active");
    document.getElementById(`tab-${tabName}`).classList.add("active");

    if (tabName === "rank") { loadLeaderboard(); loadLocationStats(); }
    if (tabName === "feed") { loadIdeas(); loadRandomIdea(); }
}

// ===== 筛选事件 =====
function bindFilterEvents() {
    document.querySelectorAll(".cat-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".cat-btn").forEach((b) => b.classList.remove("active"));
            btn.classList.add("active");
            currentCategory = btn.dataset.cat;
            loadIdeas();
        });
    });

    document.querySelectorAll(".sort-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".sort-btn").forEach((b) => b.classList.remove("active"));
            btn.classList.add("active");
            currentSort = btn.dataset.sort;
            loadIdeas();
        });
    });

    document.querySelectorAll(".cat-select-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".cat-select-btn").forEach((b) => b.classList.remove("active"));
            btn.classList.add("active");
            selectedCategory = btn.dataset.val;
        });
    });
}

// ===== 情绪标签选择 =====
function bindEmotionEvents() {
    document.querySelectorAll(".emotion-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            if (btn.classList.contains("active")) {
                btn.classList.remove("active");
                selectedEmotion = "";
            } else {
                document.querySelectorAll(".emotion-btn").forEach((b) => b.classList.remove("active"));
                btn.classList.add("active");
                selectedEmotion = btn.dataset.val;
            }
        });
    });
}

// ===== 地点选择 =====
function bindLocationEvents() {
    document.querySelectorAll(".loc-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            if (btn.classList.contains("active")) {
                btn.classList.remove("active");
                selectedLocation = "";
            } else {
                document.querySelectorAll(".loc-btn").forEach((b) => b.classList.remove("active"));
                btn.classList.add("active");
                selectedLocation = btn.dataset.val;
            }
        });
    });
}

// ===== 加载点子列表 =====
async function loadIdeas() {
    const container = document.getElementById("ideas-list");
    container.innerHTML = '<div class="loading">加载中...</div>';
    try {
        const params = new URLSearchParams({ sort: currentSort });
        if (currentCategory !== "全部") params.set("category", currentCategory);
        const res = await fetch(`/api/ideas?${params}`);
        const ideas = await res.json();

        if (ideas.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">🌱</div>
                    <p>还没有想法，快来分享第一个吧！</p>
                </div>`;
            return;
        }
        container.innerHTML = ideas.map((idea) => renderIdeaCard(idea)).join("");
    } catch (e) {
        container.innerHTML = '<div class="loading">加载失败，请刷新重试</div>';
    }
}

function renderIdeaCard(idea) {
    const timeStr = formatTime(idea.created_at);
    const categoryEmoji = { "衣": "👕", "食": "🍜", "住": "🏠", "行": "🚗", "购物结账": "🛒", "办公工作": "💼", "公共服务": "🏪", "其他": "📌" };
    const emoji = categoryEmoji[idea.category] || "📌";

    const tagsHtml = (idea.emotion || idea.location) ? `
        <div class="idea-tags">
            ${idea.emotion ? `<span class="tag-emotion">${idea.emotion}</span>` : ""}
            ${idea.location ? `<span class="tag-location">📍 ${escapeHtml(idea.location)}</span>` : ""}
        </div>` : "";

    return `
    <div class="idea-card">
        <div class="idea-header">
            <div class="idea-author">
                <span class="avatar">${idea.avatar}</span>
                <span class="name">${escapeHtml(idea.nickname)}</span>
                <span class="author-title">${idea.badge} ${idea.title}</span>
            </div>
            <span class="idea-category">${emoji} ${idea.category}</span>
        </div>
        ${tagsHtml}
        <div class="idea-body">
            <div class="idea-field">
                <div class="field-label">🎬 场景</div>
                <div class="field-value">${escapeHtml(idea.scene)}</div>
            </div>
            <div class="idea-field">
                <div class="field-label">😤 痛点</div>
                <div class="field-value">${escapeHtml(idea.pain_point)}</div>
            </div>
            <div class="idea-field">
                <div class="field-label">✨ 期望体验</div>
                <div class="field-value">${escapeHtml(idea.desired_effect)}</div>
            </div>
            ${idea.ai_suggestion ? `
            <div class="idea-ai">
                <div class="ai-label">🤖 AI建议</div>
                <div>${escapeHtml(idea.ai_suggestion)}</div>
            </div>` : ""}
        </div>
        <div class="idea-footer">
            <div style="display:flex;gap:8px;align-items:center">
                <button class="like-btn" onclick="toggleLike('${idea.id}', this)">
                    <span class="like-icon">🤍</span>
                    <span class="like-count">${idea.likes}</span>
                </button>
                <button class="empathy-btn" onclick="toggleEmpathy('${idea.id}', this)">
                    <span class="empathy-icon">🙋</span>
                    <span class="empathy-count">${idea.empathies || 0}</span>
                    <span class="empathy-label">同感</span>
                </button>
            </div>
            <span class="idea-time">${timeStr}</span>
        </div>
        <div class="comment-section">
            <button class="comment-toggle" onclick="toggleComments('${idea.id}', this)">💬 查看评论</button>
            <div class="comment-area hidden" id="comments-${idea.id}"></div>
        </div>
    </div>`;
}

// ===== 点赞 =====
async function toggleLike(ideaId, btn) {
    if (!currentUser) { showLogin(); return; }
    try {
        const res = await fetch(`/api/ideas/${ideaId}/like`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ user_id: currentUser.id }),
        });
        const data = await res.json();
        btn.classList.toggle("liked", data.liked);
        btn.querySelector(".like-icon").textContent = data.liked ? "❤️" : "🤍";
        btn.querySelector(".like-count").textContent = data.likes;
    } catch (e) {
        alert("操作失败，请重试");
    }
}

// ===== 同感（我也遇到了）=====
async function toggleEmpathy(ideaId, btn) {
    if (!currentUser) { showLogin(); return; }
    try {
        const res = await fetch(`/api/ideas/${ideaId}/empathy`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ user_id: currentUser.id }),
        });
        const data = await res.json();
        btn.classList.toggle("empathized", data.empathized);
        btn.querySelector(".empathy-count").textContent = data.empathies;
        btn.querySelector(".empathy-label").textContent = data.empathized ? "已同感" : "同感";
    } catch (e) {
        alert("操作失败，请重试");
    }
}

// ===== 评论区 =====
async function toggleComments(ideaId, btn) {
    const area = document.getElementById(`comments-${ideaId}`);
    if (area.classList.contains("hidden")) {
        area.classList.remove("hidden");
        btn.textContent = "💬 收起评论";
        await loadComments(ideaId);
    } else {
        area.classList.add("hidden");
        btn.textContent = "💬 查看评论";
    }
}

async function loadComments(ideaId) {
    const area = document.getElementById(`comments-${ideaId}`);
    try {
        const res = await fetch(`/api/ideas/${ideaId}/comments`);
        const comments = await res.json();
        const listHtml = comments.length > 0
            ? comments.map((c) => `
                <div class="comment-item">
                    <span class="c-avatar">${c.avatar}</span>
                    <span><span class="c-name">${escapeHtml(c.nickname)}</span>：<span class="c-text">${escapeHtml(c.content)}</span></span>
                </div>`).join("")
            : '<div style="font-size:0.8rem;color:var(--text-secondary);padding:4px 0">暂无评论，来说第一句吧~</div>';

        area.innerHTML = `
            <div class="comment-list">${listHtml}</div>
            <div class="comment-input-row">
                <input type="text" id="comment-input-${ideaId}" placeholder="说点什么...（限50字）" maxlength="50"
                    onkeydown="if(event.key==='Enter')submitComment('${ideaId}')">
                <button onclick="submitComment('${ideaId}')">发送</button>
            </div>`;
    } catch (e) {
        area.innerHTML = '<div style="font-size:0.8rem;color:var(--text-secondary)">加载失败</div>';
    }
}

async function submitComment(ideaId) {
    if (!currentUser) { showLogin(); return; }
    const input = document.getElementById(`comment-input-${ideaId}`);
    const content = input.value.trim();
    if (!content) return;
    try {
        const res = await fetch(`/api/ideas/${ideaId}/comments`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ user_id: currentUser.id, content }),
        });
        const data = await res.json();
        if (data.error) { alert(data.error); return; }
        input.value = "";
        await loadComments(ideaId);
    } catch (e) {
        alert("评论失败，请重试");
    }
}

// ===== 发布点子 =====
async function submitIdea() {
    if (!currentUser) { showLogin(); return; }
    const scene = document.getElementById("input-scene").value.trim();
    const pain = document.getElementById("input-pain").value.trim();
    const effect = document.getElementById("input-effect").value.trim();

    if (!scene || !pain || !effect) {
        alert("请填写完整信息（场景、痛点、期望体验）");
        return;
    }

    const btn = document.querySelector("#tab-submit .btn-block");
    btn.textContent = "⏳ 提交中...";
    btn.disabled = true;

    try {
        const res = await fetch("/api/ideas", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                user_id: currentUser.id,
                category: selectedCategory,
                scene,
                pain_point: pain,
                desired_effect: effect,
                emotion: selectedEmotion,
                location: selectedLocation,
            }),
        });
        const data = await res.json();
        if (data.error) { alert(data.error); return; }
        // 清空表单
        document.getElementById("input-scene").value = "";
        document.getElementById("input-pain").value = "";
        document.getElementById("input-effect").value = "";
        document.querySelectorAll(".emotion-btn").forEach((b) => b.classList.remove("active"));
        document.querySelectorAll(".loc-btn").forEach((b) => b.classList.remove("active"));
        selectedEmotion = "";
        selectedLocation = "";
        alert("🎉 提交成功！" + (data.ai_suggestion ? "\n\n🤖 AI建议：" + data.ai_suggestion : ""));
        switchTab("feed");
        loadIdeas();
    } catch (e) {
        alert("提交失败，请重试");
    } finally {
        btn.textContent = "🚀 提交想法";
        btn.disabled = false;
    }
}

// ===== 每日随机痛点 =====
async function loadRandomIdea() {
    const container = document.getElementById("random-idea-card");
    try {
        const res = await fetch("/api/random-idea");
        const idea = await res.json();
        if (idea.empty) {
            container.classList.add("hidden");
            return;
        }
        container.classList.remove("hidden");
        container.innerHTML = `
            <div class="random-label">🎲 随机灵感</div>
            <div class="random-text">
                <strong>${idea.emotion || ""} ${idea.location ? "📍" + escapeHtml(idea.location) : ""}</strong><br>
                ${escapeHtml(idea.pain_point)}
            </div>
            <button class="random-refresh" onclick="loadRandomIdea()" title="换一个">🔄</button>`;
    } catch (e) {
        container.classList.add("hidden");
    }
}

// ===== 排行榜 =====
async function loadLeaderboard() {
    const container = document.getElementById("leaderboard-list");
    try {
        const res = await fetch("/api/leaderboard?limit=10");
        const data = await res.json();
        if (data.length === 0) {
            container.innerHTML = '<div class="empty-state"><p>暂无数据</p></div>';
            return;
        }
        const medals = ["🥇", "🥈", "🥉"];
        container.innerHTML = data
            .map((u, i) => `
            <div class="rank-item">
                <span class="rank-num">${medals[i] || i + 1}</span>
                <span class="rank-avatar">${u.avatar}</span>
                <div class="rank-info">
                    <div class="rank-name">${escapeHtml(u.nickname)}</div>
                    <div class="rank-title">${u.badge} ${u.title}</div>
                </div>
                <span class="rank-likes">❤️ ${u.total_likes_received}</span>
            </div>`)
            .join("");
    } catch (e) {
        container.innerHTML = '<div class="loading">加载失败</div>';
    }
}

// ===== 痛点热区 =====
async function loadLocationStats() {
    const container = document.getElementById("location-stats");
    try {
        const res = await fetch("/api/location-stats");
        const data = await res.json();
        if (data.length === 0) {
            container.innerHTML = '<div class="empty-state"><p>暂无数据，提交想法时选择地点即可上榜</p></div>';
            return;
        }
        const maxCount = data[0].count || 1;
        container.innerHTML = data
            .map((item) => `
            <div class="loc-stat-item">
                <span class="loc-name">📍 ${escapeHtml(item.location)}</span>
                <div class="loc-bar" style="width:${Math.max(20, (item.count / maxCount) * 120)}px"></div>
                <span class="loc-count">${item.count} 条</span>
            </div>`)
            .join("");
    } catch (e) {
        container.innerHTML = '<div class="loading">加载失败</div>';
    }
}

// ===== 奖励阶梯 =====
async function loadRewardTiers() {
    const container = document.getElementById("reward-tiers");
    try {
        const res = await fetch("/api/reward-tiers");
        const tiers = await res.json();
        container.innerHTML = tiers
            .map((t) => `
            <div class="tier-item">
                <span class="tier-badge">${t.badge}</span>
                <div class="tier-info">
                    <div class="tier-title">${t.title}</div>
                    <div class="tier-req">累计获得 ${t.min_likes} 个点赞即可解锁</div>
                </div>
            </div>`)
            .join("");
    } catch (e) {
        container.innerHTML = '<div class="loading">加载失败</div>';
    }
}

// ===== 统计 =====
async function loadStats() {
    try {
        const res = await fetch("/api/stats");
        const s = await res.json();
        document.getElementById("stats-display").textContent =
            `💡${s.ideas} 个想法 · 👥${s.users} 位用户 · ❤️${s.likes} 赞 · 🙋${s.empathies} 同感`;
    } catch (e) {}
}

// ===== 工具函数 =====
function formatTime(timestamp) {
    const now = Date.now() / 1000;
    const diff = now - timestamp;
    if (diff < 60) return "刚刚";
    if (diff < 3600) return `${Math.floor(diff / 60)}分钟前`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}小时前`;
    if (diff < 604800) return `${Math.floor(diff / 86400)}天前`;
    const d = new Date(timestamp * 1000);
    return `${d.getMonth() + 1}月${d.getDate()}日`;
}

function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
}
