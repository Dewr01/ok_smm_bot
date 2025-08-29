# db.py
import sqlite3, json
from datetime import datetime

DB_PATH = "assistant.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    first_seen TIMESTAMP,
    messages_count INTEGER DEFAULT 0,
    last_action TEXT,
    attributes TEXT DEFAULT '{}' -- json (interests, segment, etc)
);
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    event_type TEXT,
    payload TEXT,
    ts TIMESTAMP
);
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT,
    image_path TEXT,
    template TEXT, -- name of template used
    created_at TIMESTAMP,
    scheduled_at TIMESTAMP,
    published_at TIMESTAMP,
    status TEXT DEFAULT 'draft' -- draft|scheduled|published|error
);
CREATE TABLE IF NOT EXISTS templates (
    name TEXT PRIMARY KEY,
    body TEXT
);
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
);
CREATE TABLE IF NOT EXISTS clicks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT,
    target_url TEXT,
    utm TEXT,
    user_agent TEXT,
    ip TEXT,
    ts TIMESTAMP
);
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku TEXT,
    title TEXT,
    price REAL,
    url TEXT,
    image TEXT,
    tags TEXT
);
CREATE TABLE IF NOT EXISTS polls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT,
    options TEXT, -- json list
    created_at TIMESTAMP
);
CREATE TABLE IF NOT EXISTS poll_votes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    poll_id INTEGER,
    user_id TEXT,
    option_index INTEGER,
    ts TIMESTAMP
);
"""


def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.executescript(SCHEMA)
    conn.commit()
    conn.close()


def clear_posts():
    """Удаляет все записи из таблицы posts."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM posts")
    conn.commit()
    conn.close()


def add_user(uid: str, attrs: dict = None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""INSERT OR IGNORE INTO users (user_id, first_seen, messages_count, last_action, attributes)
                    VALUES (?, ?, 0, ?, ?)""", (uid, datetime.now(), "start", json.dumps(attrs or {})))
    conn.commit()
    conn.close()


def update_user(uid: str, action: str, attrs: dict = None):
    conn = get_conn()
    cur = conn.cursor()
    if attrs is None:
        cur.execute("""UPDATE users SET messages_count = messages_count + 1, last_action = ? WHERE user_id = ?""",
                    (action, uid))
    else:
        cur.execute(
            """UPDATE users SET messages_count = messages_count + 1, last_action = ?, attributes = ? WHERE user_id = ?""",
            (action, json.dumps(attrs), uid))
    conn.commit()
    conn.close()


def log_event(uid, etype: str, payload: str = ""):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""INSERT INTO events (user_id, event_type, payload, ts) VALUES (?, ?, ?, ?)""",
                (uid, etype, payload, datetime.now()))
    conn.commit()
    conn.close()


def set_setting(key: str, value):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value""",
        (key, json.dumps(value)))
    conn.commit()
    conn.close()


def get_setting(key: str, default=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT value FROM settings WHERE key=?", (key,))
    row = cur.fetchone()
    conn.close()
    if not row: return default
    try:
        return json.loads(row[0])
    except Exception:
        return default


def add_post(text: str, image_path: str = None, template: str = None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""INSERT INTO posts (text, image_path, template, created_at, status) VALUES (?,?,?,?, 'draft')""",
                (text, image_path, template, datetime.now()))
    conn.commit()
    conn.close()


def get_post(post_id: int):
    """Получить пост по ID"""
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM posts WHERE id = ?", (post_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


# def publish_post(post_id: int):
#     """Пометить пост как опубликованный (фиктивная функция)"""
#     conn = get_conn()
#     cur = conn.cursor()
#     cur.execute(
#         "UPDATE posts SET status='published', published_at=datetime('now') WHERE id=?",
#         (post_id,)
#     )
#     conn.commit()
#     conn.close()


def schedule_post(post_id: int, dt_iso: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE posts SET scheduled_at=?, status='scheduled' WHERE id=?", (dt_iso, post_id))
    conn.commit()
    conn.close()


def list_posts(limit=500):
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM posts ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def publish_post(text: str, image_path: str = None, template: str = None):
    """Добавляет пост и сразу помечает как опубликованный"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""INSERT INTO posts (text, image_path, template, created_at, published_at, status)
                   VALUES (?,?,?,?,?, 'published')""",
                (text, image_path, template, datetime.now(), datetime.utcnow()))
    conn.commit()
    conn.close()


def delete_post(post_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM posts WHERE id = ?", (post_id,))
    conn.commit()


def list_queue(limit=200):
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM posts WHERE status='scheduled' ORDER BY scheduled_at ASC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def next_due(now_iso: str):
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM posts WHERE status='scheduled' AND scheduled_at <= ? ORDER BY scheduled_at ASC LIMIT 1",
                (now_iso,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def mark_published(post_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE posts SET status='published', published_at=? WHERE id=?", (datetime.utcnow(), post_id))
    conn.commit()
    conn.close()


def mark_error(post_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE posts SET status='error' WHERE id=?", (post_id,))
    conn.commit()
    conn.close()


def list_templates():
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM templates ORDER BY name ASC")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def upsert_template(name: str, body: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO templates (name, body) VALUES (?, ?) ON CONFLICT(name) DO UPDATE SET body=excluded.body""",
        (name, body))
    conn.commit()
    conn.close()


def log_click(slug: str, target_url: str, utm: str, user_agent: str, ip: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO clicks (slug, target_url, utm, user_agent, ip, ts) VALUES (?,?,?,?,?,?)",
                (slug, target_url, utm, user_agent, ip, datetime.now()))
    conn.commit()
    conn.close()


def clicks_by_slug():
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT slug, COUNT(*) as cnt FROM clicks GROUP BY slug ORDER BY cnt DESC")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def engagement_histogram_by_hour():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""SELECT strftime('%H', ts) as hour, COUNT(*) FROM events 
                WHERE event_type IN ('like','comment','share','click') GROUP BY hour""")
    rows = cur.fetchall()
    conn.close()
    hist = {str(h).zfill(2): 0 for h in range(24)}
    for h, c in rows:
        if h is None: continue
        hist[str(h).zfill(2)] = c
    return hist


def list_users(limit=1000):
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM users ORDER BY messages_count DESC, first_seen DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# --- schema patch for PRO ---
SCHEMA += '''

-- A/B tests core
CREATE TABLE IF NOT EXISTS ab_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    created_at TIMESTAMP
);
CREATE TABLE IF NOT EXISTS ab_variants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER,
    post_id INTEGER,
    variant_label TEXT -- 'A' | 'B' | 'C' ...
);
'''


def create_ab_group(name: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO ab_groups (name, created_at) VALUES (?,?)", (name, datetime.now()))
    gid = cur.lastrowid
    conn.commit()
    conn.close()
    return gid


def add_ab_variant(group_id: int, post_id: int, label: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO ab_variants (group_id, post_id, variant_label) VALUES (?,?,?)", (group_id, post_id, label))
    conn.commit()
    conn.close()


def ab_group_stats():
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    # clicks table has slugs; we use post_id in payload-less demo, so aggregate by redirect slug pattern if any
    # For demo, return variants list without metrics (metrics via clicks_by_slug UI chart)
    cur.execute("""
        SELECT g.id as group_id, g.name, v.post_id, v.variant_label
        FROM ab_groups g
        JOIN ab_variants v ON v.group_id = g.id
        ORDER BY g.id ASC, v.variant_label ASC
    """)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# --- CRM segmentation ---
def segment_top_loyal(limit=10):
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM users ORDER BY messages_count DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def segment_by_event(event_type: str, limit=100):
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT user_id, COUNT(*) as cnt FROM events WHERE type=? GROUP BY user_id ORDER BY cnt DESC LIMIT ?",
                (event_type, limit))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]
