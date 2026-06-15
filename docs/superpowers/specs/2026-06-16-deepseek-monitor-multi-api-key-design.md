# DeepSeek Monitor — 多 API Key 预设管理器

**日期**: 2026-06-16
**状态**: 待实施
**关联**: [DeepSeek Monitor 设计](2026-06-15-deepseek-monitor-design.md)

---

## 1. 动机

当前 DeepSeek Monitor 只支持保存单个 API Key（通过设置页 UI 写入 `config.json`）。用户希望在**完全保留现有行为的前提下**，新增多 API Key 预设管理功能，支持：

- 存储多个命名 API Key 预设（数量不限）
- 快速切换当前使用的 Key（托盘菜单 + 设置页）
- 兼容旧版单 Key 模式（`config.json` 仍可正常使用）

---

## 2. 不变项（现状零改动）

以下文件和功能**完全不修改**：

| 文件 | 说明 |
|------|------|
| `api.py` | 仅接收 key 字符串，不关心来源 |
| `main.py` | 入口逻辑无关 |
| `crypto.py` | 加密逻辑独立 |
| `theme.py` | 纯样式 |
| `popup.py` | 弹窗展示，不改 |
| `main_window.py` | Tab 结构不变 |
| `config.json` | 仍作为兼容层保留 |

现有 `get_api_key()` / `save_api_key()` / `delete_api_key()` 三个函数**保持不动**，以确保旧版单 Key 模式完全正常。

---

## 3. 存储层设计（`storage.py`）

### 3.1 新表 `key_presets`

```sql
CREATE TABLE IF NOT EXISTS key_presets (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL UNIQUE,
    key_value   TEXT NOT NULL,
    created_at  TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at  TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);
```

- `name` 唯一约束，不允许重名
- `key_value` 存 API Key 明文字符串（与现有 `config.json` 一致，保持同一安全级别）

### 3.2 设置项

在已有 `settings` 表中新增 key：

| key | value 说明 |
|-----|-----------|
| `active_preset_id` | 当前激活的 preset ID（整数），空表示未启用预设模式 |

### 3.3 新增函数

```python
def get_presets() -> list[dict]:
    """返回所有预设列表，按创建时间排序"""

def add_preset(name: str, key: str) -> int:
    """新增预设，返回 ID。name 重复时抛出 ValueError"""

def update_preset(id: int, name: str = None, key: str = None):
    """更新预设的名称或 Key。name 不可为空"""

def delete_preset(id: int):
    """删除指定预设；若为当前激活的预设，同时清除 active_preset_id"""

def set_active_preset(id: int):
    """设置当前激活的预设。传 None 或 0 表示清除激活状态"""

def get_active_preset_key() -> str | None:
    """返回当前激活预设的 Key，没有则返回 None"""

def resolve_api_key() -> str | None:
    """
    多来源链式获取 Key，按优先级：
    ① active_preset 的 key_value（SQLite）
    ② config.json 的 api_key（向后兼容）
    ③ api_key.txt（同级目录纯文本文件）
    ④ .env 文件中的 DEEPSEEK_API_KEY
    ⑤ 系统环境变量 DEEPSEEK_API_KEY
    """
```

### 3.4 辅助函数

```python
def _read_key_file(path: str) -> str | None:
    """读取纯文本文件，去除首尾空白。文件不存在或为空返回 None"""

def _parse_env_file(path: str) -> dict:
    """解析 .env 格式文件，返回 {KEY: VALUE} 字典。忽略注释和空行"""
```

---

## 4. 数据流

### 4.1 写入流

```
设置页 UI "新增预设" → add_preset() → SQLite key_presets 表
设置页 UI "切换预设" → set_active_preset() → settings.active_preset_id
托盘菜单快速切换    → set_active_preset() → settings.active_preset_id
设置页 UI 保存单 Key → save_api_key() → config.json（原逻辑，完全不变）
```

### 4.2 读取流

```
worker._refresh() / app.py 启动检查
       ↓
resolve_api_key()
       ↓
① active_preset 存在？ → 返回 SQLite 中的 key
② 没有 active_preset → config.json 有 key？ → 返回
③ 都没有 → api_key.txt？ → 返回
④ 没有 → .env？ → 返回
⑤ 没有 → 环境变量？ → 返回
⑥ 都没有 → None（无 Key 状态）
```

---

## 5. UI 设计

### 5.1 设置页新增（`settings_page.py`）

在现有"删除 Key"按钮下方，新增预设管理区域：

```
┌─────────────────────────────────────────┐
│  🔑 API Key（单 Key 模式）              │ ← 现有区域，完全不动
│  [当前输入框...............]             │
│  [显示] [保存] [删除]                   │
│                                         │
│  ─────────────────────────────────      │
│                                         │
│  📋 API Key 预设管理                     │ ← 新增区域
│                                         │
│  当前预设: [下拉框 ▾]                   │
│            [应用此预设]                  │
│                                         │
│  [➕ 新建]  [✏️ 编辑]  [🗑 删除]        │
│                                         │
│  💡 激活预设后，程序优先使用预设中的 Key  │
│  ，单 Key 模式作为兼容后备               │
└─────────────────────────────────────────┘
```

交互细节：

- **下拉框**：列出所有预设名称。当前激活的预设显示在首位默认选中
- **应用此预设**：调用 `set_active_preset()`，发送信号让 worker 下次刷新用新 Key
- **新建**：弹出 `QDialog`，输入名称 + Key，调用 `add_preset()`
- **编辑**：选中预设 → 弹出 `QDialog` 修改名称或 Key，调用 `update_preset()`
- **删除**：确认对话框 → 调用 `delete_preset()`
- **清除激活**：下拉框增加一个"无（使用单 Key 模式）"选项，选中即清除激活状态

### 5.2 托盘菜单新增（`tray.py`）

在"手动刷新"和"退出"之间插入子菜单：

```
┌──────────────────────────────┐
│  打开详情                     │
│  手动刷新                     │
│  ─────────────                │
│  ▶ 切换 API Key              │ ← 子菜单
│       ✓ 预设：主用 Key        │
│         预设：R1 测试账号      │
│         预设：V3 生产         │
│       ─────────────            │
│         单 Key 模式           │ ← 无激活预设时勾选
│  ─────────────                │
│  退出                         │
└──────────────────────────────┘
```

交互细节：

- 点击任一预设 → 调用 `set_active_preset()` → 自动触发一次余额刷新 → 更新托盘提示
- ✓ 标记当前激活的预设（或"单 Key 模式"）
- 预设列表动态生成，增删预设后下次打开菜单自动同步

---

## 6. 改动清单

### 6.1 `storage.py` — 新增约 120 行

- 新增表 `key_presets`（在 `_ensure_tables()` 中添加 DDL）
- 5 个预设 CRUD 函数
- `resolve_api_key()` + 2 个辅助函数
- `import os` 和 `from pathlib import Path`（如未引入）

### 6.2 `settings_page.py` — 新增约 80 行

- 新增 `_build_preset_section()` 构建预设管理 UI
- 信号连接：新增/编辑对话框 → 刷新下拉列表
- `_load_presets()` 刷新下拉列表

### 6.3 `worker.py` — 改动 2 行

- `_refresh()` 中 `db_get_api_key()` → `resolve_api_key()`
- 新增 import：`from storage import resolve_api_key`

### 6.4 `app.py` — 改动 2 行

- 启动 key 检查：`db_get_api_key()` → `resolve_api_key()`
- 新增 import

### 6.5 `tray.py` — 新增子菜单逻辑

- `_build_preset_menu()` 构建动态子菜单
- 预设切换信号 → 调用 `set_active_preset()` → 触发刷新

---

## 7. 兼容性与迁移

| 场景 | 行为 |
|------|------|
| 旧用户升级，`config.json` 有 key | resolve_api_key() 回退到 ②，工作完全正常 |
| 旧用户升级，无任何预设 | 托盘菜单只显示"单 Key 模式（当前）"，和之前体验一致 |
| 新用户创建预设并激活 | resolve_api_key() 走 ①，config.json 被跳过 |
| 用户删除所有预设 | 自动回退到 config.json / 文件 / 环境变量 |
| 用户通过设置页保存 Key | 仍写入 config.json（原逻辑），不影响预设 |

---

## 8. 边界与异常处理

- **名称重复**：`add_preset()` 抛出 `ValueError`，UI 捕获并提示用户
- **空名称**：前端校验不可为空，长度 ≥ 1
- **删除已激活的预设**：自动清除 `active_preset_id`，退回到 config.json
- **预设为空（无预设 + 无 config.json + 无文件）**：resolve_api_key() 返回 None，和现有无 Key 状态表现一致
- **托盘子菜单超长**：预设名称超过 30 字符时 UI 截断显示，hover 显示完整名称
