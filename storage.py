"""SQLite 存储层 — API Key / 余额快照 / 设置 / 历史导出"""
import sqlite3
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Optional


_DB = None  # 单例连接


def app_dir() -> str:
    """应用根目录 — exe 同目录（PyInstaller）或源码同目录（python）"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def resource_dir() -> str:
    """资源目录 — PyInstaller 解压临时目录或源码同目录"""
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


def get_db_path() -> str:
    """获取数据库文件路径 — exe 同级 data/ 目录下"""
    base = app_dir()
    data_dir = os.path.join(base, "data")
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, "deepseek_monitor.db")


def get_conn() -> sqlite3.Connection:
    global _DB
    if _DB is None:
        _DB = sqlite3.connect(get_db_path(), check_same_thread=False)
        _DB.row_factory = sqlite3.Row
        _DB.execute("PRAGMA journal_mode=WAL")
        _DB.execute("PRAGMA foreign_keys=ON")
        _ensure_tables(_DB)
    return _DB


def _ensure_tables(conn: sqlite3.Connection):
    """自动建表（幂等），首次连接时调用"""
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
        CREATE TABLE IF NOT EXISTS key_presets (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL UNIQUE,
            key_value   TEXT NOT NULL,
            created_at  TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            updated_at  TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        );
    """)
    conn.commit()


def init_db():
    """建表（幂等），显式调用以确保数据库就绪"""
    _ensure_tables(get_conn())


# ── API Key 操作（config.json）──────────────────────

import json as _json


def _config_path() -> str:
    base = app_dir()
    return os.path.join(base, "config.json")


def _read_config() -> dict:
    try:
        with open(_config_path(), "r", encoding="utf-8") as f:
            return _json.load(f)
    except (FileNotFoundError, _json.JSONDecodeError, IOError):
        return {}


def _write_config(config: dict):
    with open(_config_path(), "w", encoding="utf-8") as f:
        _json.dump(config, f, ensure_ascii=False, indent=2)


def save_api_key(key: str):
    """保存 API Key 到 config.json"""
    cfg = _read_config()
    cfg["api_key"] = key
    _write_config(cfg)


def get_api_key() -> Optional[str]:
    """从 config.json 读取 API Key"""
    return _read_config().get("api_key")


def delete_api_key():
    """删除 config.json 中的 API Key"""
    cfg = _read_config()
    cfg.pop("api_key", None)
    _write_config(cfg)


# ── API Key 预设操作 ────────────────────────────────


def get_presets() -> list[dict]:
    """返回所有预设列表，按创建时间升序"""
    rows = get_conn().execute(
        "SELECT id, name, created_at, updated_at FROM key_presets ORDER BY created_at ASC"
    ).fetchall()
    return [dict(r) for r in rows]


def add_preset(name: str, key: str) -> int:
    """新增预设，返回新记录 ID。name 重复时抛出 ValueError"""
    name = name.strip()
    key = key.strip()
    if not name:
        raise ValueError("预设名称不能为空")
    if not key:
        raise ValueError("API Key 不能为空")
    try:
        cur = get_conn().execute(
            "INSERT INTO key_presets (name, key_value) VALUES (?, ?)",
            (name, key)
        )
        get_conn().commit()
        return cur.lastrowid
    except sqlite3.IntegrityError:
        raise ValueError(f"预设名称「{name}」已存在")


def update_preset(id: int, name: str = None, key: str = None):
    """更新预设的名称或 Key。至少提供一个参数"""
    if name is not None:
        name = name.strip()
        if not name:
            raise ValueError("预设名称不能为空")
        try:
            get_conn().execute(
                "UPDATE key_presets SET name = ?, updated_at = datetime('now', 'localtime') WHERE id = ?",
                (name, id)
            )
        except sqlite3.IntegrityError:
            raise ValueError(f"预设名称「{name}」已存在")
    if key is not None:
        key = key.strip()
        if not key:
            raise ValueError("API Key 不能为空")
        get_conn().execute(
            "UPDATE key_presets SET key_value = ?, updated_at = datetime('now', 'localtime') WHERE id = ?",
            (key, id)
        )
    get_conn().commit()


def delete_preset(id: int):
    """删除预设。若当前激活的预设被删，自动清除激活状态"""
    get_conn().execute("DELETE FROM key_presets WHERE id = ?", (id,))
    # 如果删的是当前激活的预设，清除激活标记
    active = get_setting("active_preset_id")
    if active and str(id) == active:
        set_setting("active_preset_id", "")
    get_conn().commit()


def set_active_preset(id: int | None):
    """设置当前激活的预设 ID。传 None 或 0 表示清除"""
    if id:
        set_setting("active_preset_id", str(id))
    else:
        set_setting("active_preset_id", "")


def get_active_preset_key() -> str | None:
    """返回当前激活预设的 Key，没有则返回 None"""
    active_id = get_setting("active_preset_id")
    if not active_id:
        return None
    row = get_conn().execute(
        "SELECT key_value FROM key_presets WHERE id = ?", (int(active_id),)
    ).fetchone()
    if row is None:
        # 预设已被删除但 active_preset_id 没清干净
        set_setting("active_preset_id", "")
        return None
    return row["key_value"]


def _read_key_file(path: str) -> str | None:
    """读取纯文本文件，去除首尾空白。文件不存在或内容为空返回 None"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
        return content if content else None
    except (FileNotFoundError, IOError):
        return None


def _parse_env_file(path: str) -> dict:
    """解析 .env 文件，返回 {KEY: VALUE}。忽略 # 注释行和空行"""
    result = {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, _, val = line.partition("=")
                result[key.strip()] = val.strip().strip("\"'")
        return result
    except (FileNotFoundError, IOError):
        return {}


def resolve_api_key() -> str | None:
    """
    多来源链式获取 API Key，按优先级：
    ① active_preset → SQLite key_presets
    ② config.json → 兼容旧版
    ③ api_key.txt → 同级目录
    ④ .env → DEEPSEEK_API_KEY
    ⑤ 系统环境变量 DEEPSEEK_API_KEY
    """
    # ① active_preset
    key = get_active_preset_key()
    if key:
        return key

    # ② config.json
    key = get_api_key()
    if key:
        return key

    base = app_dir()

    # ③ api_key.txt
    key = _read_key_file(os.path.join(base, "api_key.txt"))
    if key:
        return key

    # ④ .env
    env = _parse_env_file(os.path.join(base, ".env"))
    key = env.get("DEEPSEEK_API_KEY")
    if key:
        return key

    # ⑤ 系统环境变量
    key = os.environ.get("DEEPSEEK_API_KEY")
    if key:
        return key

    return None


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
    base = app_dir()
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
    base = app_dir()
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
    base = app_dir()
    history_dir = os.path.join(base, "history")
    os.makedirs(history_dir, exist_ok=True)
    return history_dir
