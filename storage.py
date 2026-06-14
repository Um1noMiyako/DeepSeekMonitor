"""SQLite 存储层 — API Key / 余额快照 / 设置 / 历史导出"""
import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import Optional


_DB = None  # 单例连接


def get_db_path() -> str:
    """获取数据库文件路径 — exe 同级 data/ 目录下"""
    base = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base, "data")
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, "deepseek_monitor.db")


def get_conn() -> sqlite3.Connection:
    global _DB
    if _DB is None:
        _DB = sqlite3.connect(get_db_path())
        _DB.row_factory = sqlite3.Row
        _DB.execute("PRAGMA journal_mode=WAL")
        _DB.execute("PRAGMA foreign_keys=ON")
    return _DB


def init_db():
    """建表（幂等）"""
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS api_keys (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            encrypted_key  TEXT NOT NULL,
            created_at     TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        );

        CREATE TABLE IF NOT EXISTS balance_snapshots (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            total_balance     REAL NOT NULL,
            granted_balance   REAL NOT NULL,
            topped_up_balance REAL NOT NULL,
            is_available      INTEGER NOT NULL DEFAULT 1,
            currency          TEXT NOT NULL DEFAULT 'CNY',
            fetched_at        TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        );

        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
    """)
    conn.commit()


# ── API Key 操作 ──────────────────────────────────

def save_api_key(encrypted_key: str):
    """保存加密后的 API Key（替换旧值）"""
    conn = get_conn()
    conn.execute("DELETE FROM api_keys")
    conn.execute("INSERT INTO api_keys (encrypted_key) VALUES (?)", (encrypted_key,))
    conn.commit()


def get_api_key() -> Optional[str]:
    """获取加密的 API Key，无记录返回 None"""
    row = get_conn().execute("SELECT encrypted_key FROM api_keys ORDER BY id DESC LIMIT 1").fetchone()
    return row["encrypted_key"] if row else None


# ── 余额快照操作 ─────────────────────────────────

def insert_snapshot(total: float, granted: float, topped_up: float,
                    is_available: bool, currency: str = "CNY"):
    """插入一条余额快照"""
    conn = get_conn()
    conn.execute(
        "INSERT INTO balance_snapshots (total_balance, granted_balance, topped_up_balance, is_available, currency) "
        "VALUES (?, ?, ?, ?, ?)",
        (total, granted, topped_up, 1 if is_available else 0, currency)
    )
    conn.commit()
    # 触发过期清理
    _cleanup_old_snapshots()


def get_recent_snapshots(days: int = 30) -> list[dict]:
    """获取最近 N 天的快照列表（按时间倒序）"""
    rows = get_conn().execute(
        "SELECT * FROM balance_snapshots WHERE fetched_at >= datetime('now', 'localtime', ?) "
        "ORDER BY fetched_at DESC",
        (f"-{days} days",)
    ).fetchall()
    return [dict(r) for r in rows]


def get_latest_snapshot() -> Optional[dict]:
    """获取最新一条快照"""
    row = get_conn().execute(
        "SELECT * FROM balance_snapshots ORDER BY fetched_at DESC LIMIT 1"
    ).fetchone()
    return dict(row) if row else None


def _cleanup_old_snapshots():
    """清理 30 天前的快照：先导出到 history/，再删除"""
    conn = get_conn()
    cutoff = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
    old_rows = conn.execute(
        "SELECT * FROM balance_snapshots WHERE fetched_at < ?",
        (cutoff,)
    ).fetchall()

    if not old_rows:
        return

    # 导出到 history/
    base = os.path.dirname(os.path.abspath(__file__))
    history_dir = os.path.join(base, "history")
    os.makedirs(history_dir, exist_ok=True)

    # 按月分组
    monthly = {}
    for r in old_rows:
        month_key = r["fetched_at"][:7]  # "2026-05"
        monthly.setdefault(month_key, []).append({
            "fetched_at": r["fetched_at"],
            "total_balance": r["total_balance"],
            "granted_balance": r["granted_balance"],
            "topped_up_balance": r["topped_up_balance"],
            "is_available": bool(r["is_available"]),
            "currency": r["currency"],
        })

    for month_key, entries in monthly.items():
        filepath = os.path.join(history_dir, f"{month_key}.json")
        existing = []
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        existing.extend(entries)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)

    # 删除
    conn.execute("DELETE FROM balance_snapshots WHERE fetched_at < ?", (cutoff,))
    conn.commit()


def export_all_snapshots() -> str:
    """导出所有快照为 JSON，返回文件路径"""
    rows = get_conn().execute(
        "SELECT * FROM balance_snapshots ORDER BY fetched_at DESC"
    ).fetchall()
    base = os.path.dirname(os.path.abspath(__file__))
    history_dir = os.path.join(base, "history")
    os.makedirs(history_dir, exist_ok=True)
    filepath = os.path.join(history_dir, f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    data = [{
        "fetched_at": r["fetched_at"],
        "total_balance": r["total_balance"],
        "granted_balance": r["granted_balance"],
        "topped_up_balance": r["topped_up_balance"],
        "is_available": bool(r["is_available"]),
        "currency": r["currency"],
    } for r in rows]
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return filepath


# ── 设置操作 ─────────────────────────────────────

def get_setting(key: str, default: str = None) -> Optional[str]:
    """读设置"""
    row = get_conn().execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else default


def set_setting(key: str, value: str):
    """写设置"""
    conn = get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
        (key, value)
    )
    conn.commit()


def get_history_dir() -> str:
    """获取 history 目录路径"""
    base = os.path.dirname(os.path.abspath(__file__))
    history_dir = os.path.join(base, "history")
    os.makedirs(history_dir, exist_ok=True)
    return history_dir
