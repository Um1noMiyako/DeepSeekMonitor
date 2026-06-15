# DeepSeek Monitor — 多 API Key 预设管理器 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 DeepSeek Monitor 增加多 API Key 预设管理功能——用户可存储多个命名 API Key 预设，通过设置页或托盘菜单快速切换，同时完全保留现有单 Key 模式不变。

**Architecture:** 在 SQLite 中新增 `key_presets` 表存储预设，新增 `resolve_api_key()` 作为多来源 Key 解析链（预设 → config.json → 本地文件 → 环境变量），覆盖 `worker.py` 和 `app.py` 中原来直接调用 `get_api_key()` 的位置。现有单 Key 读写函数完全不动。

**Tech Stack:** Python 3.10+, PySide6, SQLite

**Spec:** `docs/superpowers/specs/2026-06-16-deepseek-monitor-multi-api-key-design.md`

---

### Task 1: `storage.py` — 新增 `key_presets` 表 DDL

**Files:**
- Modify: `storage.py:31-53`（`_ensure_tables` 函数）

- [ ] **Step 1: 在 `_ensure_tables()` 中添加 `key_presets` 建表语句**

修改 `storage.py` 中 `_ensure_tables` 函数，在 `executescript` 末尾追加 `key_presets` 建表。

```python
# 在 _ensure_tables 的 executescript 字符串末尾，settings 表后面追加：
CREATE TABLE IF NOT EXISTS key_presets (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL UNIQUE,
    key_value   TEXT NOT NULL,
    created_at  TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at  TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);
```

- [ ] **Step 2: 验证建表**

手动运行验证（或重启程序后检查 `data/deepseek_monitor.db`）：

```bash
cd /d/Projects/DeepSeekMonitor
python -c "from storage import get_conn; conn = get_conn(); print([r['name'] for r in conn.execute(\"SELECT name FROM sqlite_master WHERE type='table'\").fetchall()])"
```

预期输出包含 `key_presets`。

- [ ] **Step 3: 提交**

```bash
git add storage.py
git commit -m "feat(storage): add key_presets table DDL"
```

---

### Task 2: `storage.py` — 预设 CRUD 函数

**Files:**
- Modify: `storage.py`（新增 5 个函数，放在现有 `# ── API Key 操作` 区域之后）

- [ ] **Step 1: 新增 `get_presets()` 和 `add_preset()`**

```python
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
```

- [ ] **Step 2: 新增 `update_preset()` 和 `delete_preset()`**

```python
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
```

- [ ] **Step 3: 新增 `set_active_preset()` 和 `get_active_preset_key()`**

```python
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
```

- [ ] **Step 4: 验证 CRUD 函数**

```bash
cd /d/Projects/DeepSeekMonitor
python -c "
from storage import get_presets, add_preset, update_preset, delete_preset, set_active_preset, get_active_preset_key

# 清理
for p in get_presets():
    delete_preset(p['id'])

# 新增
id1 = add_preset('test1', 'sk-test-key-1')
print(f'add_preset → id={id1}')
id2 = add_preset('test2', 'sk-test-key-2')
print(f'add_preset → id={id2}')

# 列表
print(f'presets: {get_presets()}')

# 更新
update_preset(id1, name='test1-renamed')
print(f'after rename: {get_presets()}')

# 激活
set_active_preset(id2)
key = get_active_preset_key()
print(f'active key: {key}')

# 删除激活的预设
delete_preset(id2)
print(f'after delete active: active_key={get_active_preset_key()}, presets={get_presets()}')

# 清理
delete_preset(id1)
print('CRUD OK')
"
```

预期输出：所有操作无异常，打印结果合理。

- [ ] **Step 5: 提交**

```bash
git add storage.py
git commit -m "feat(storage): add preset CRUD functions"
```

---

### Task 3: `storage.py` — 新增 `resolve_api_key()` 多来源解析链

**Files:**
- Modify: `storage.py`（新增 `resolve_api_key()` + `_read_key_file()` + `_parse_env_file()`）

- [ ] **Step 1: 新增辅助函数 `_read_key_file()`**

```python
def _read_key_file(path: str) -> str | None:
    """读取纯文本文件，去除首尾空白。文件不存在或内容为空返回 None"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
        return content if content else None
    except (FileNotFoundError, IOError):
        return None
```

- [ ] **Step 2: 新增辅助函数 `_parse_env_file()`**

```python
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
```

- [ ] **Step 3: 新增 `resolve_api_key()`**

```python
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

    base = os.path.dirname(os.path.abspath(__file__))

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
```

- [ ] **Step 4: 验证 `resolve_api_key()`**

```bash
cd /d/Projects/DeepSeekMonitor
python -c "
from storage import resolve_api_key, add_preset, set_active_preset, delete_preset, get_presets

# 先清除所有预设
for p in get_presets():
    delete_preset(p['id'])
set_active_preset(None)

# 当前无 key
print(f'no key: {resolve_api_key()}')

# 通过预设
id1 = add_preset('test-preset', 'sk-from-preset')
set_active_preset(id1)
print(f'from preset: {resolve_api_key()}')

# 清除激活，测试 config.json
set_active_preset(None)
from storage import save_api_key
save_api_key('sk-from-config')
print(f'from config: {resolve_api_key()}')

# 清理
from storage import delete_api_key
delete_api_key()
for p in get_presets():
    delete_preset(p['id'])
print('resolve_api_key OK')
"
```

预期输出：
```
no key: None
from preset: sk-from-preset
from config: sk-from-config
resolve_api_key OK
```

- [ ] **Step 5: 提交**

```bash
git add storage.py
git commit -m "feat(storage): add resolve_api_key() multi-source chain"
```

---

### Task 4: `settings_page.py` — 新增预设管理 UI 区域

**Files:**
- Modify: `settings_page.py`（新增 `_build_preset_section()` + 对话框 + 信号）

- [ ] **Step 1: 在文件顶部 import 补充**

```python
# 在现有 from storage import ... 末尾追加
from storage import (save_api_key, get_api_key, delete_api_key, get_setting,
                     set_setting, export_all_snapshots, get_history_dir,
                     get_presets, add_preset, update_preset, delete_preset,
                     set_active_preset, get_active_preset_key)
from PySide6.QtWidgets import QDialog, QFormLayout, QDialogButtonBox, QMessageBox
```

- [ ] **Step 2: 新建 `PresetDialog` 类（放在 `SettingsPage` 类前面）**

```python
class PresetDialog(QDialog):
    """新增/编辑预设的对话框"""

    def __init__(self, parent=None, preset: dict = None):
        super().__init__(parent)
        self.setWindowTitle("编辑预设" if preset else "新增预设")
        self.setMinimumWidth(400)
        self._preset = preset

        layout = QFormLayout(self)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("预设名称，如「主用 Key」「R1 测试」")
        if preset:
            self.name_input.setText(preset["name"])
        layout.addRow("名称：", self.name_input)

        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("DeepSeek API Key (sk-...)")
        if preset:
            # 编辑时不回填 Key 值（安全），留空表示不修改
            self.key_input.setPlaceholderText("留空则不修改")
        layout.addRow("API Key：", self.key_input)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self._validate)
        self.buttons.rejected.connect(self.reject)
        layout.addRow(self.buttons)

    def _validate(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "提示", "预设名称不能为空")
            return
        if not self._preset:
            key = self.key_input.text().strip()
            if not key:
                QMessageBox.warning(self, "提示", "API Key 不能为空")
                return
        self.accept()

    def get_name(self) -> str:
        return self.name_input.text().strip()

    def get_key(self) -> str:
        return self.key_input.text().strip()
```

- [ ] **Step 3: 在 `SettingsPage._build_ui()` 末尾（about 前面）追加预设区域构建调用**

```python
    # 在 layout.addWidget(self._divider()) 和 about 之间插入
    layout.addWidget(self._divider())
    self._build_preset_section(layout)
```

- [ ] **Step 4: 新增 `_build_preset_section()` 方法**

```python
    def _build_preset_section(self, layout):
        layout.addWidget(QLabel("📋 API Key 预设管理"))

        # 提示文字
        hint = QLabel("💡 激活预设后，程序优先使用预设中的 Key，单 Key 模式作为兼容后备")
        hint.setObjectName("preset-hint")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        # 下拉选择行
        select_row = QHBoxLayout()
        self.preset_combo = QComboBox()
        self.preset_combo.setMinimumWidth(200)
        select_row.addWidget(self.preset_combo)

        self.apply_preset_btn = QPushButton("✅ 应用此预设")
        self.apply_preset_btn.setObjectName("btn-primary")
        self.apply_preset_btn.clicked.connect(self._apply_preset)
        select_row.addWidget(self.apply_preset_btn)
        select_row.addStretch()
        layout.addLayout(select_row)

        # 操作按钮行
        btn_row = QHBoxLayout()
        add_btn = QPushButton("➕ 新建")
        add_btn.setObjectName("btn-secondary")
        add_btn.clicked.connect(self._add_preset_dialog)
        btn_row.addWidget(add_btn)

        edit_btn = QPushButton("✏️ 编辑")
        edit_btn.setObjectName("btn-secondary")
        edit_btn.clicked.connect(self._edit_preset_dialog)
        btn_row.addWidget(edit_btn)

        del_btn = QPushButton("🗑 删除")
        del_btn.setObjectName("btn-secondary")
        del_btn.clicked.connect(self._delete_preset_confirm)
        btn_row.addWidget(del_btn)

        save_api_key_btn = QPushButton("💾 存为预设")
        save_btn.setObjectName("btn-secondary")
        save_api_key_btn.clicked.connect(self._save_current_as_preset)
        btn_row.addWidget(save_api_key_btn)

        btn_row.addStretch()
        layout.addLayout(btn_row)
```

- [ ] **Step 5: 新增预设管理的 slot 方法**

```python
    def _load_presets(self):
        """刷新下拉列表"""
        self.preset_combo.clear()
        self.preset_combo.addItem("— 无（使用单 Key 模式）", "")
        for p in get_presets():
            self.preset_combo.addItem(p["name"], p["id"])
        # 选中当前激活的预设
        active_id = get_setting("active_preset_id", "")
        if active_id:
            idx = self.preset_combo.findData(int(active_id))
            if idx >= 0:
                self.preset_combo.setCurrentIndex(idx)

    def _apply_preset(self):
        preset_id = self.preset_combo.currentData()
        if preset_id:
            set_active_preset(int(preset_id))
            self.api_key_saved.emit()
            QMessageBox.information(self, "切换成功", f"已切换到预设「{self.preset_combo.currentText()}」")
        else:
            set_active_preset(None)
            self.api_key_saved.emit()

    def _add_preset_dialog(self):
        dialog = PresetDialog(self)
        if dialog.exec():
            name = dialog.get_name()
            key = dialog.get_key()
            try:
                add_preset(name, key)
                self._load_presets()
            except ValueError as e:
                QMessageBox.warning(self, "添加失败", str(e))

    def _edit_preset_dialog(self):
        preset_id = self.preset_combo.currentData()
        if not preset_id:
            QMessageBox.information(self, "提示", "请先选择一个预设")
            return
        presets = get_presets()
        preset = next((p for p in presets if p["id"] == preset_id), None)
        if not preset:
            return
        dialog = PresetDialog(self, preset=preset)
        if dialog.exec():
            name = dialog.get_name()
            key = dialog.get_key()
            try:
                update_preset(preset_id, name=name, key=key if key else None)
                self._load_presets()
            except ValueError as e:
                QMessageBox.warning(self, "修改失败", str(e))

    def _delete_preset_confirm(self):
        preset_id = self.preset_combo.currentData()
        if not preset_id:
            QMessageBox.information(self, "提示", "请先选择一个预设")
            return
        name = self.preset_combo.currentText()
        reply = QMessageBox.question(
            self, "确认删除", f"确定删除预设「{name}」吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            delete_preset(preset_id)
            self._load_presets()
            self.api_key_saved.emit()

    def _save_current_as_preset(self):
        """将当前输入框的 Key 一键存为预设"""
        key = self.key_input.text().strip()
        if not key:
            QMessageBox.information(self, "提示", "请先在 API Key 输入框中输入 Key")
            return
        dialog = PresetDialog(self)
        # 自动填入 Key
        dialog.key_input.setText(key)
        if dialog.exec():
            name = dialog.get_name()
            try:
                add_preset(name, key)
                self._load_presets()
            except ValueError as e:
                QMessageBox.warning(self, "添加失败", str(e))
```

- [ ] **Step 6: 在 `_load_values()` 末尾追加调用 `_load_presets()`**

```python
    def _load_values(self):
        # ... 现有代码不变 ...
        self._load_presets()  # 追加
```

- [ ] **Step 7: 提交**

```bash
git add settings_page.py
git commit -m "feat(settings): add preset management UI"
```

---

### Task 5: `worker.py` 和 `app.py` — 改用 `resolve_api_key()`

**Files:**
- Modify: `worker.py:4`（import 行）+ `worker.py:40`（`_refresh` 中的 key 获取）
- Modify: `app.py:5`（import 行）+ `app.py:21`（启动 key 检查）

- [ ] **Step 1: 修改 `worker.py`**

改动 import 行：
```python
# 旧
from storage import get_api_key as db_get_api_key, insert_snapshot, get_setting
# 新
from storage import resolve_api_key, insert_snapshot, get_setting
```

改动 `_refresh()` 中 key 获取：
```python
    def _refresh(self):
        """执行一次刷新"""
        try:
            api_key = resolve_api_key()  # 旧: db_get_api_key()
            if not api_key:
                self.no_key.emit()
                return
```

- [ ] **Step 2: 验证 `worker.py` 没有遗漏旧引用**

```bash
cd /d/Projects/DeepSeekMonitor
python -c "import ast; ast.parse(open('worker.py').read()); print('syntax OK')"
grep -n "db_get_api_key" worker.py
```

预期输出：`syntax OK`，且 grep 无匹配。

- [ ] **Step 3: 修改 `app.py`**

改动 import 行：
```python
# 旧
from storage import init_db, get_latest_snapshot, get_api_key as db_get_api_key
# 新
from storage import init_db, get_latest_snapshot, resolve_api_key
```

改动 `start()` 中 key 检查（两处）：
```python
    def start(self):
        init_db()
        self._tray = TrayManager(self._app)
        self._tray.refresh_requested.connect(self._refresh_now)
        self._tray.quit_requested.connect(self._quit)

        if not resolve_api_key():  # 旧: db_get_api_key()
            self._tray.show_message(...)
            ...

    def _refresh_ui_from_snapshot(self, snap: dict | None, status: str = "ok"):
        if snap is None:
            status = "no_key" if not resolve_api_key() else "ok"  # 旧: db_get_api_key()
        self._tray.update_popup(snap, status)
        self._tray.update_main_window(snap, status)
```

- [ ] **Step 4: 验证 `app.py`**

```bash
cd /d/Projects/DeepSeekMonitor
python -c "import ast; ast.parse(open('app.py').read()); print('syntax OK')"
grep -n "db_get_api_key" app.py
```

预期输出：`syntax OK`，且 grep 无匹配。

- [ ] **Step 5: 提交**

```bash
git add worker.py app.py
git commit -m "refactor: switch to resolve_api_key() for multi-source key resolution"
```

---

### Task 6: `tray.py` — 托盘菜单新增"切换 API Key"子菜单

**Files:**
- Modify: `tray.py`（import + 构建子菜单 + 信号连接）

- [ ] **Step 1: 先读 `tray.py` 了解现有菜单结构**

```bash
cat -n tray.py
```

基于输出确定子菜单插入位置。

- [ ] **Step 2: 修改 `tray.py` import 行**

在文件顶部补充 import：
```python
from storage import get_presets, set_active_preset, set_setting, get_setting, resolve_api_key
```

- [ ] **Step 3: 新增 `_build_preset_submenu()` 方法**

在 `TrayManager` 类中新增方法，假设现有菜单构造在 `_build_menu()` 或 `__init__` 中，找到"手动刷新"和"退出"之间的位置，插入子菜单构建逻辑。

```python
    def _build_preset_submenu(self):
        """构建切换 API Key 子菜单"""
        menu = QMenu("切换 API Key")

        presets = get_presets()
        active_id = get_setting("active_preset_id", "")

        if presets:
            for p in presets:
                action = menu.addAction(p["name"])
                action.setCheckable(True)
                action.setChecked(str(p["id"]) == active_id)
                action.setData(p["id"])
                action.triggered.connect(lambda checked, pid=p["id"], pname=p["name"]: self._switch_preset(pid, pname))
            menu.addSeparator()

        # "单 Key 模式"选项
        no_preset_action = menu.addAction("单 Key 模式")
        no_preset_action.setCheckable(True)
        no_preset_action.setChecked(not active_id and resolve_api_key() is not None)
        no_preset_action.triggered.connect(lambda: self._switch_preset(None, "单 Key 模式"))

        return menu

    def _switch_preset(self, preset_id: int | None, name: str):
        """切换预设并触发刷新"""
        set_active_preset(preset_id)
        self.refresh_requested.emit()
        self.show_message("DeepSeek Monitor", f"已切换到「{name}」")
```

- [ ] **Step 4: 在现有菜单中插入子菜单**

在 `_build_menu()` 或等效位置，找到"手动刷新"和"退出"之间的分隔线处插入：

```python
    # 手动刷新 action 之后、退出 action 之前插入：
    menu.addSeparator()
    preset_menu = self._build_preset_submenu()
    menu.addMenu(preset_menu)
    menu.addSeparator()
```

- [ ] **Step 5: 验证托盘菜单构建**

```bash
cd /d/Projects/DeepSeekMonitor
python -c "import ast; ast.parse(open('tray.py').read()); print('syntax OK')"
```

- [ ] **Step 6: 提交**

```bash
git add tray.py
git commit -m "feat(tray): add API key preset switching submenu"
```

---

### Task 7: 端到端功能验证

**Files:** 无代码改动，运行程序手动测试

- [ ] **Step 1: 清空已有 Key，全新启动验证**

```bash
cd /d/Projects/DeepSeekMonitor
echo '{}' > config.json
python -c "from storage import get_conn; conn = get_conn(); conn.execute('DROP TABLE IF EXISTS key_presets'); conn.commit()"
python -c "from storage import get_presets; print(f'presets after reset: {get_presets()}')"
```

预期输出：`presets after reset: []`

- [ ] **Step 2: 启动程序**

```bash
cd /d/Projects/DeepSeekMonitor
python main.py &
```

等待 2 秒，观察托盘图标出现，提示"未配置 API Key"。

- [ ] **Step 3: 测试设置页预设管理**

1. 双击托盘图标打开窗口 → 设置 Tab
2. 确认看到"API Key 预设管理"区域
3. 点击「新建」，输入名称"主用 Key"、Key `sk-test-1` → 保存
4. 下拉框出现"主用 Key"
5. 再新建"备用 Key" → `sk-test-2`
6. 选中"主用 Key"→ 点击「应用此预设」
7. 刷新间隔选 5 分钟（或点手动刷新），观察余额成功拉取
8. 回到下拉框切换为"备用 Key"

- [ ] **Step 4: 测试托盘菜单切换**

1. 右键托盘图标 → 看到"切换 API Key"子菜单
2. 展开 → 列出 2 个预设，当前激活的带 ✓
3. 点击另一个预设 → 弹出提示"已切换到「...」"
4. 勾选标记切换到对应预设

- [ ] **Step 5: 测试单 Key 模式兼容**

1. 在设置页中，下拉框选"无（使用单 Key 模式）"→ 应用
2. 在 API Key 输入框输入一个有效 Key → 保存
3. 托盘菜单中"单 Key 模式"被勾选
4. 余额正常拉取

- [ ] **Step 6: 测试本地文件回退**

```bash
cd /d/Projects/DeepSeekMonitor
# 清空预设和 config
python -c "
from storage import set_active_preset, get_presets, delete_preset, save_api_key, delete_api_key
set_active_preset(None)
for p in get_presets(): delete_preset(p['id'])
delete_api_key()
"
# 写入 api_key.txt
echo -n "sk-from-file-test" > api_key.txt
# 验证
python -c "from storage import resolve_api_key; print(f'from file: {resolve_api_key()}')"
# 清理
rm api_key.txt
```

预期输出：`from file: sk-from-file-test`

- [ ] **Step 7: 测试 .env 文件回退**

```bash
cd /d/Projects/DeepSeekMonitor
# 写入 .env
echo 'DEEPSEEK_API_KEY=sk-from-env-file' > .env
# 验证
python -c "from storage import resolve_api_key; print(f'from .env: {resolve_api_key()}')"
# 清理
rm .env
```

预期输出：`from .env: sk-from-env-file`

- [ ] **Step 8: 最终清理**

```bash
cd /d/Projects/DeepSeekMonitor
echo '{}' > config.json
python -c "
from storage import set_active_preset, get_presets, delete_preset, delete_api_key
set_active_preset(None)
for p in get_presets(): delete_preset(p['id'])
delete_api_key()
"
```

- [ ] **Step 9: 全量提交**

```bash
git add -A
git commit -m "chore: cleanup test artifacts"
```

---

### 改动文件汇总

| 文件 | 改动类型 | 改动量 |
|------|---------|--------|
| `storage.py` | 修改 | +~100 行（表 DDL + 5 CRUD + resolve_api_key + 辅助函数） |
| `settings_page.py` | 修改 | +~130 行（PresetDialog 类 + 预设 UI 区域 + slot 方法） |
| `worker.py` | 修改 | 2 行（import + 函数调用） |
| `app.py` | 修改 | 3 行（import + 2 处函数调用） |
| `tray.py` | 修改 | +~40 行（子菜单构建 + 切换方法） |
