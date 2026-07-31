"""数据库模型与操作"""
import sqlite3
import time
import uuid
from config import Config


def get_db():
    """获取数据库连接"""
    conn = sqlite3.connect(Config.DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """初始化数据库表"""
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            nickname TEXT NOT NULL,
            avatar TEXT DEFAULT '😊',
            title TEXT DEFAULT '萌新',
            badge TEXT DEFAULT '🌱',
            total_likes_received INTEGER DEFAULT 0,
            created_at REAL DEFAULT (strftime('%s','now'))
        );

        CREATE TABLE IF NOT EXISTS ideas (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT '其他',
            scene TEXT NOT NULL,
            pain_point TEXT NOT NULL,
            desired_effect TEXT NOT NULL,
            emotion TEXT DEFAULT '',
            location TEXT DEFAULT '',
            ai_suggestion TEXT DEFAULT '',
            likes INTEGER DEFAULT 0,
            empathies INTEGER DEFAULT 0,
            created_at REAL DEFAULT (strftime('%s','now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS likes (
            id TEXT PRIMARY KEY,
            idea_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            created_at REAL DEFAULT (strftime('%s','now')),
            UNIQUE(idea_id, user_id),
            FOREIGN KEY (idea_id) REFERENCES ideas(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS empathies (
            id TEXT PRIMARY KEY,
            idea_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            created_at REAL DEFAULT (strftime('%s','now')),
            UNIQUE(idea_id, user_id),
            FOREIGN KEY (idea_id) REFERENCES ideas(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS comments (
            id TEXT PRIMARY KEY,
            idea_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at REAL DEFAULT (strftime('%s','now')),
            FOREIGN KEY (idea_id) REFERENCES ideas(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE INDEX IF NOT EXISTS idx_ideas_likes ON ideas(likes DESC);
        CREATE INDEX IF NOT EXISTS idx_ideas_category ON ideas(category);
        CREATE INDEX IF NOT EXISTS idx_ideas_empathies ON ideas(empathies DESC);
        CREATE INDEX IF NOT EXISTS idx_likes_idea ON likes(idea_id);
        CREATE INDEX IF NOT EXISTS idx_empathies_idea ON empathies(idea_id);
        CREATE INDEX IF NOT EXISTS idx_comments_idea ON comments(idea_id);
    """)
    conn.commit()
    conn.close()


def create_user(nickname: str, avatar: str = "😊") -> dict:
    """创建新用户"""
    conn = get_db()
    user_id = str(uuid.uuid4())[:8]
    conn.execute(
        "INSERT INTO users (id, nickname, avatar) VALUES (?, ?, ?)",
        (user_id, nickname, avatar),
    )
    conn.commit()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(user)


def get_user(user_id: str) -> dict | None:
    """获取用户信息"""
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(user) if user else None


def update_user_title(user_id: str):
    """根据获得的总点赞数更新用户称号"""
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user:
        conn.close()
        return
    total_likes = user["total_likes_received"]
    title, badge = "萌新", "🌱"
    for tier in reversed(Config.REWARD_TIERS):
        if total_likes >= tier["min_likes"]:
            title, badge = tier["title"], tier["badge"]
            break
    conn.execute(
        "UPDATE users SET title = ?, badge = ? WHERE id = ?",
        (title, badge, user_id),
    )
    conn.commit()
    conn.close()


def create_idea(user_id: str, category: str, scene: str, pain_point: str,
                desired_effect: str, emotion: str = "", location: str = "",
                ai_suggestion: str = "") -> dict:
    """创建新点子"""
    conn = get_db()
    idea_id = str(uuid.uuid4())[:8]
    conn.execute(
        """INSERT INTO ideas (id, user_id, category, scene, pain_point, desired_effect, emotion, location, ai_suggestion)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (idea_id, user_id, category, scene, pain_point, desired_effect, emotion, location, ai_suggestion),
    )
    conn.commit()
    idea = conn.execute("SELECT * FROM ideas WHERE id = ?", (idea_id,)).fetchone()
    conn.close()
    return dict(idea)


def get_ideas(category: str = "", sort_by: str = "latest", page: int = 1,
              page_size: int = 20) -> list[dict]:
    """获取点子列表"""
    conn = get_db()
    offset = (page - 1) * page_size
    query = """
        SELECT i.*, u.nickname, u.avatar, u.title, u.badge
        FROM ideas i JOIN users u ON i.user_id = u.id
    """
    params = []
    if category and category != "全部":
        query += " WHERE i.category = ?"
        params.append(category)

    if sort_by == "hot":
        query += " ORDER BY i.likes DESC, i.created_at DESC"
    elif sort_by == "empathy":
        query += " ORDER BY i.empathies DESC, i.created_at DESC"
    else:
        query += " ORDER BY i.created_at DESC"

    query += " LIMIT ? OFFSET ?"
    params.extend([page_size, offset])

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_idea_detail(idea_id: str) -> dict | None:
    """获取点子详情"""
    conn = get_db()
    row = conn.execute(
        """SELECT i.*, u.nickname, u.avatar, u.title, u.badge
           FROM ideas i JOIN users u ON i.user_id = u.id WHERE i.id = ?""",
        (idea_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def toggle_like(idea_id: str, user_id: str) -> dict:
    """切换点赞状态，返回 {liked: bool, likes: int}"""
    conn = get_db()
    existing = conn.execute(
        "SELECT id FROM likes WHERE idea_id = ? AND user_id = ?",
        (idea_id, user_id),
    ).fetchone()

    if existing:
        conn.execute("DELETE FROM likes WHERE id = ?", (existing["id"],))
        conn.execute("UPDATE ideas SET likes = likes - 1 WHERE id = ?", (idea_id,))
        # 减少作者获得的点赞数
        idea = conn.execute("SELECT user_id FROM ideas WHERE id = ?", (idea_id,)).fetchone()
        if idea:
            conn.execute(
                "UPDATE users SET total_likes_received = MAX(0, total_likes_received - 1) WHERE id = ?",
                (idea["user_id"],),
            )
        liked = False
    else:
        like_id = str(uuid.uuid4())[:8]
        conn.execute(
            "INSERT INTO likes (id, idea_id, user_id) VALUES (?, ?, ?)",
            (like_id, idea_id, user_id),
        )
        conn.execute("UPDATE ideas SET likes = likes + 1 WHERE id = ?", (idea_id,))
        idea = conn.execute("SELECT user_id FROM ideas WHERE id = ?", (idea_id,)).fetchone()
        if idea:
            conn.execute(
                "UPDATE users SET total_likes_received = total_likes_received + 1 WHERE id = ?",
                (idea["user_id"],),
            )
        liked = True

    conn.commit()
    idea_row = conn.execute("SELECT likes, user_id FROM ideas WHERE id = ?", (idea_id,)).fetchone()
    conn.close()

    # 更新作者称号
    if idea_row:
        update_user_title(idea_row["user_id"])

    return {"liked": liked, "likes": idea_row["likes"] if idea_row else 0}


def has_liked(idea_id: str, user_id: str) -> bool:
    """检查是否已点赞"""
    conn = get_db()
    row = conn.execute(
        "SELECT id FROM likes WHERE idea_id = ? AND user_id = ?",
        (idea_id, user_id),
    ).fetchone()
    conn.close()
    return row is not None


def get_leaderboard(limit: int = 10) -> list[dict]:
    """获取排行榜"""
    conn = get_db()
    rows = conn.execute(
        """SELECT id, nickname, avatar, title, badge, total_likes_received
           FROM users ORDER BY total_likes_received DESC LIMIT ?""",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_stats() -> dict:
    """获取平台统计"""
    conn = get_db()
    idea_count = conn.execute("SELECT COUNT(*) as c FROM ideas").fetchone()["c"]
    user_count = conn.execute("SELECT COUNT(*) as c FROM users").fetchone()["c"]
    like_count = conn.execute("SELECT COUNT(*) as c FROM likes").fetchone()["c"]
    empathy_count = conn.execute("SELECT COUNT(*) as c FROM empathies").fetchone()["c"]
    comment_count = conn.execute("SELECT COUNT(*) as c FROM comments").fetchone()["c"]
    conn.close()
    return {"ideas": idea_count, "users": user_count, "likes": like_count,
            "empathies": empathy_count, "comments": comment_count}


# ===== 同感（我也遇到了）=====

def toggle_empathy(idea_id: str, user_id: str) -> dict:
    """切换同感状态"""
    conn = get_db()
    existing = conn.execute(
        "SELECT id FROM empathies WHERE idea_id = ? AND user_id = ?",
        (idea_id, user_id),
    ).fetchone()

    if existing:
        conn.execute("DELETE FROM empathies WHERE id = ?", (existing["id"],))
        conn.execute("UPDATE ideas SET empathies = MAX(0, empathies - 1) WHERE id = ?", (idea_id,))
        empathized = False
    else:
        eid = str(uuid.uuid4())[:8]
        conn.execute(
            "INSERT INTO empathies (id, idea_id, user_id) VALUES (?, ?, ?)",
            (eid, idea_id, user_id),
        )
        conn.execute("UPDATE ideas SET empathies = empathies + 1 WHERE id = ?", (idea_id,))
        empathized = True

    conn.commit()
    row = conn.execute("SELECT empathies FROM ideas WHERE id = ?", (idea_id,)).fetchone()
    conn.close()
    return {"empathized": empathized, "empathies": row["empathies"] if row else 0}


def has_empathized(idea_id: str, user_id: str) -> bool:
    """检查是否已表示同感"""
    conn = get_db()
    row = conn.execute(
        "SELECT id FROM empathies WHERE idea_id = ? AND user_id = ?",
        (idea_id, user_id),
    ).fetchone()
    conn.close()
    return row is not None


# ===== 轻评论 =====

def add_comment(idea_id: str, user_id: str, content: str) -> dict:
    """添加评论（限50字）"""
    conn = get_db()
    comment_id = str(uuid.uuid4())[:8]
    conn.execute(
        "INSERT INTO comments (id, idea_id, user_id, content) VALUES (?, ?, ?, ?)",
        (comment_id, idea_id, user_id, content[:50]),
    )
    conn.commit()
    row = conn.execute(
        """SELECT c.*, u.nickname, u.avatar FROM comments c
           JOIN users u ON c.user_id = u.id WHERE c.id = ?""",
        (comment_id,),
    ).fetchone()
    conn.close()
    return dict(row)


def get_comments(idea_id: str, limit: int = 20) -> list[dict]:
    """获取评论列表"""
    conn = get_db()
    rows = conn.execute(
        """SELECT c.*, u.nickname, u.avatar FROM comments c
           JOIN users u ON c.user_id = u.id
           WHERE c.idea_id = ? ORDER BY c.created_at DESC LIMIT ?""",
        (idea_id, limit),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_comment_count(idea_id: str) -> int:
    """获取评论数"""
    conn = get_db()
    row = conn.execute("SELECT COUNT(*) as c FROM comments WHERE idea_id = ?", (idea_id,)).fetchone()
    conn.close()
    return row["c"]


# ===== 每日随机痛点 =====

def get_random_idea() -> dict | None:
    """随机获取一条点子"""
    conn = get_db()
    row = conn.execute(
        """SELECT i.*, u.nickname, u.avatar, u.title, u.badge
           FROM ideas i JOIN users u ON i.user_id = u.id
           ORDER BY RANDOM() LIMIT 1"""
    ).fetchone()
    conn.close()
    return dict(row) if row else None


# ===== 痛点热区（按地点统计）=====

def get_location_stats(limit: int = 10) -> list[dict]:
    """按地点统计痛点数量"""
    conn = get_db()
    rows = conn.execute(
        """SELECT location, COUNT(*) as count, SUM(empathies) as total_empathies
           FROM ideas WHERE location != '' GROUP BY location
           ORDER BY count DESC LIMIT ?""",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
