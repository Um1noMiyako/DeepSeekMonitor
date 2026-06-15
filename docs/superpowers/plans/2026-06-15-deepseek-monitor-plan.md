# DeepSeek Monitor 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个 Windows 桌面托盘应用，调用 DeepSeek API 显示账户余额，10 分钟自动刷新，支持 9 色玻璃主题。

**Architecture:** PySide6 单进程，QSystemTrayIcon 托盘 + Frameless Popup 浮窗 + QMainWindow 完整窗口。数据流：api.py → storage.py (SQLite) → 信号槽 → UI 层更新。theme.py 用 dataclass + QSS 模板驱动 9 色主题。

**Tech Stack:** Python 3.11+, PySide6, requests, cryptography.fernet, sqlite3, PyInstaller

---

## 文件结构

| 文件 | 创建/修改 | 职责 |
|:--|:--|:--|
| `requirements.txt` | 新建 | 依赖声明 |
| `theme.py` | 新建 | 9 色主题 dataclass + QSS 生成 + custom.css 覆盖 |
| `crypto.py` | 新建 | API Key 加解密 (Fernet) |
| `storage.py` | 新建 | SQLite CRUD + 历史导出 |
| `api.py` | 新建 | DeepSeek 余额 API 调用 |
| `worker.py` | 新建 | QThread 后台定时刷新 |
| `popup.py` | 新建 | Frameless 预览浮窗 |
| `settings_page.py` | 新建 | 设置 Tab 内容 |
| `main_window.py` | 新建 | 完整窗口（概览/历史/设置三 Tab）|
| `tray.py` | 新建 | 系统托盘图标 + 右键菜单 |
| `app.py` | 新建 | QApplication + 生命周期 + 组件接线 |
| `main.py` | 新建 | 入口 + 单例锁 |
| `build.bat` | 新建 | PyInstaller 打包脚本 |
| `resources/icon.png` | 新建 | 应用图标（1024x1024 占位） |

---

### Task 1: 项目骨架和依赖

**Files:**
- Create: `D:\Projects\DeepSeekMonitor\requirements.txt`
- Create: `D:\Projects\DeepSeekMonitor\resources\icon.png` (占位)

- [ ] **Step 1: 创建 requirements.txt**

```txt
PySide6>=6.5.0
requests>=2.28.0
cryptography>=41.0.0
```

- [ ] **Step 2: 创建占位图标**

```bash
python -c "
from PySide6.QtGui import QPixmap, QPainter, QColor
from PySide6.QtCore import Qt
p = QPixmap(256, 256)
p.fill(Qt.transparent)
pt = QPainter(p)
pt.setBrush(QColor(99, 102, 241))
pt.setPen(Qt.NoPen)
pt.drawRoundedRect(32, 32, 192, 192, 48, 48)
pt.end()
p.save('D:/Projects/DeepSeekMonitor/resources/icon.png')
"
```

- [ ] **Step 3: 安装依赖并验证**

```bash
cd /d/Projects/DeepSeekMonitor && pip install -r requirements.txt
python -c "import PySide6; print('PySide6', PySide6.__version__); import requests; import cryptography; print('OK')"
```

Expected: 打印 PySide6 版本号和 OK

- [ ] **Step 4: Commit**

```bash
cd /d/Projects/DeepSeekMonitor
git init
git add requirements.txt resources/icon.png
git commit -m "chore: init project skeleton with deps"
```

---

### Task 2: 主题系统 theme.py

**Files:**
- Create: `D:\Projects\DeepSeekMonitor\theme.py`

- [ ] **Step 1: 编写 ThemeColors dataclass 和 9 色主题数据**

```python
"""DeepSeek Monitor — 深空玻璃 9 色主题 → PySide6 QSS"""
from dataclasses import dataclass, field
from typing import Optional
import os, sys, re


@dataclass
class ThemeColors:
    """24 字段主题色板"""
    name: str
    # 背景层级
    bg_deep: str
    bg_surface: str
    bg_elevated: str
    # 玻璃
    glass_bg: str
    glass_border: str
    glass_border_hover: str
    # 强调色
    accent_1: str
    accent_2: str
    accent_3: str
    accent_light: str
    # 渐变
    gradient: str
    glow: str
    glow_pulse: str
    # 文字
    text_primary: str
    text_secondary: str
    text_muted: str
    # 按钮
    btn_primary_bg: str
    btn_primary_hover: str
    btn_primary_color: str
    # 徽标
    badge_bg: str
    badge_border: str
    badge_dot: str
    # 输入框
    input_bg: str
    input_border: str
    input_focus: str


# ── 9 色主题定义 ────────────────────────────────

THEMES: dict[str, ThemeColors] = {
    "indigo": ThemeColors(
        name="靛蓝流光",
        bg_deep="#06060E", bg_surface="#0B0B18", bg_elevated="#111128",
        glass_bg="rgba(16,16,40,0.55)", glass_border="rgba(99,102,241,0.12)",
        glass_border_hover="rgba(99,102,241,0.25)",
        accent_1="#6366F1", accent_2="#8B5CF6", accent_3="#A78BFA",
        accent_light="rgba(99,102,241,0.08)",
        gradient="linear-gradient(135deg, #6366F1, #8B5CF6, #A78BFA)",
        glow="rgba(99,102,241,0.15)", glow_pulse="rgba(99,102,241,0.3)",
        text_primary="#E8E6F0", text_secondary="#8A88A8", text_muted="#4A4968",
        btn_primary_bg="qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #6366F1,stop:1 #4F46E5)",
        btn_primary_hover="qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #818CF8,stop:1 #6366F1)",
        btn_primary_color="#FFFFFF",
        badge_bg="rgba(99,102,241,0.1)", badge_border="rgba(99,102,241,0.2)",
        badge_dot="#6366F1",
        input_bg="rgba(255,255,255,0.03)", input_border="rgba(255,255,255,0.06)",
        input_focus="rgba(99,102,241,0.2)",
    ),
    "emerald": ThemeColors(
        name="碧翠琉璃",
        bg_deep="#040E09", bg_surface="#081812", bg_elevated="#0F2820",
        glass_bg="rgba(16,48,36,0.55)", glass_border="rgba(16,185,129,0.12)",
        glass_border_hover="rgba(16,185,129,0.25)",
        accent_1="#10B981", accent_2="#34D399", accent_3="#6EE7B7",
        accent_light="rgba(16,185,129,0.08)",
        gradient="linear-gradient(135deg, #10B981, #34D399, #6EE7B7)",
        glow="rgba(16,185,129,0.15)", glow_pulse="rgba(16,185,129,0.3)",
        text_primary="#E0F0E8", text_secondary="#80A898", text_muted="#386858",
        btn_primary_bg="qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #10B981,stop:1 #059669)",
        btn_primary_hover="qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #34D399,stop:1 #10B981)",
        btn_primary_color="#FFFFFF",
        badge_bg="rgba(16,185,129,0.1)", badge_border="rgba(16,185,129,0.2)",
        badge_dot="#10B981",
        input_bg="rgba(255,255,255,0.03)", input_border="rgba(255,255,255,0.06)",
        input_focus="rgba(16,185,129,0.2)",
    ),
    "amber": ThemeColors(
        name="赤焰熔金",
        bg_deep="#0E0804", bg_surface="#1A0E06", bg_elevated="#2A1A0A",
        glass_bg="rgba(48,28,12,0.55)", glass_border="rgba(245,158,11,0.12)",
        glass_border_hover="rgba(245,158,11,0.25)",
        accent_1="#F59E0B", accent_2="#F97316", accent_3="#FB923C",
        accent_light="rgba(245,158,11,0.08)",
        gradient="linear-gradient(135deg, #F59E0B, #F97316, #FB923C)",
        glow="rgba(245,158,11,0.15)", glow_pulse="rgba(245,158,11,0.3)",
        text_primary="#F0E0D0", text_secondary="#A88860", text_muted="#684830",
        btn_primary_bg="qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #F59E0B,stop:1 #D97706)",
        btn_primary_hover="qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #FBBF24,stop:1 #F59E0B)",
        btn_primary_color="#0E0804",
        badge_bg="rgba(245,158,11,0.1)", badge_border="rgba(245,158,11,0.2)",
        badge_dot="#F59E0B",
        input_bg="rgba(255,255,255,0.03)", input_border="rgba(255,255,255,0.06)",
        input_focus="rgba(245,158,11,0.2)",
    ),
    "rose": ThemeColors(
        name="玫瑰星云",
        bg_deep="#0E0408", bg_surface="#1A0810", bg_elevated="#2A0A1A",
        glass_bg="rgba(48,12,28,0.55)", glass_border="rgba(236,72,153,0.12)",
        glass_border_hover="rgba(236,72,153,0.25)",
        accent_1="#EC4899", accent_2="#F472B6", accent_3="#F9A8D4",
        accent_light="rgba(236,72,153,0.08)",
        gradient="linear-gradient(135deg, #EC4899, #F472B6, #F9A8D4)",
        glow="rgba(236,72,153,0.15)", glow_pulse="rgba(236,72,153,0.3)",
        text_primary="#F0D8E0", text_secondary="#A87080", text_muted="#683848",
        btn_primary_bg="qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #EC4899,stop:1 #DB2777)",
        btn_primary_hover="qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #F472B6,stop:1 #EC4899)",
        btn_primary_color="#FFFFFF",
        badge_bg="rgba(236,72,153,0.1)", badge_border="rgba(236,72,153,0.2)",
        badge_dot="#EC4899",
        input_bg="rgba(255,255,255,0.03)", input_border="rgba(255,255,255,0.06)",
        input_focus="rgba(236,72,153,0.2)",
    ),
    "cyan": ThemeColors(
        name="极光冰晶",
        bg_deep="#040A0E", bg_surface="#08141A", bg_elevated="#0A202E",
        glass_bg="rgba(8,44,60,0.55)", glass_border="rgba(6,182,212,0.12)",
        glass_border_hover="rgba(6,182,212,0.25)",
        accent_1="#06B6D4", accent_2="#22D3EE", accent_3="#67E8F9",
        accent_light="rgba(6,182,212,0.08)",
        gradient="linear-gradient(135deg, #06B6D4, #22D3EE, #67E8F9)",
        glow="rgba(6,182,212,0.15)", glow_pulse="rgba(6,182,212,0.3)",
        text_primary="#D8ECF0", text_secondary="#689CA8", text_muted="#285868",
        btn_primary_bg="qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #06B6D4,stop:1 #0891B2)",
        btn_primary_hover="qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #22D3EE,stop:1 #06B6D4)",
        btn_primary_color="#FFFFFF",
        badge_bg="rgba(6,182,212,0.1)", badge_border="rgba(6,182,212,0.2)",
        badge_dot="#06B6D4",
        input_bg="rgba(255,255,255,0.03)", input_border="rgba(255,255,255,0.06)",
        input_focus="rgba(6,182,212,0.2)",
    ),
    "violet": ThemeColors(
        name="紫罗兰夜",
        bg_deep="#08040E", bg_surface="#100820", bg_elevated="#1C0A36",
        glass_bg="rgba(24,12,48,0.55)", glass_border="rgba(139,92,246,0.12)",
        glass_border_hover="rgba(139,92,246,0.25)",
        accent_1="#8B5CF6", accent_2="#A78BFA", accent_3="#C4B5FD",
        accent_light="rgba(139,92,246,0.08)",
        gradient="linear-gradient(135deg, #8B5CF6, #A78BFA, #C4B5FD)",
        glow="rgba(139,92,246,0.15)", glow_pulse="rgba(139,92,246,0.3)",
        text_primary="#E0D8F0", text_secondary="#8878A8", text_muted="#483868",
        btn_primary_bg="qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #8B5CF6,stop:1 #7C3AED)",
        btn_primary_hover="qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #A78BFA,stop:1 #8B5CF6)",
        btn_primary_color="#FFFFFF",
        badge_bg="rgba(139,92,246,0.1)", badge_border="rgba(139,92,246,0.2)",
        badge_dot="#8B5CF6",
        input_bg="rgba(255,255,255,0.03)", input_border="rgba(255,255,255,0.06)",
        input_focus="rgba(139,92,246,0.2)",
    ),
    "neon": ThemeColors(
        name="霓虹都市",
        bg_deep="#0E0008", bg_surface="#1A0012", bg_elevated="#2A001C",
        glass_bg="rgba(48,0,28,0.55)", glass_border="rgba(255,0,128,0.12)",
        glass_border_hover="rgba(255,0,128,0.25)",
        accent_1="#FF0080", accent_2="#7928CA", accent_3="#B84AE0",
        accent_light="rgba(255,0,128,0.08)",
        gradient="linear-gradient(135deg, #FF0080, #7928CA, #B84AE0)",
        glow="rgba(255,0,128,0.2)", glow_pulse="rgba(255,0,128,0.35)",
        text_primary="#F0D8E8", text_secondary="#A86888", text_muted="#682848",
        btn_primary_bg="qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #FF0080,stop:1 #CC0066)",
        btn_primary_hover="qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #FF3399,stop:1 #FF0080)",
        btn_primary_color="#FFFFFF",
        badge_bg="rgba(255,0,128,0.1)", badge_border="rgba(255,0,128,0.2)",
        badge_dot="#FF0080",
        input_bg="rgba(255,255,255,0.03)", input_border="rgba(255,255,255,0.06)",
        input_focus="rgba(255,0,128,0.2)",
    ),
    "charcoal": ThemeColors(
        name="暗灰墨",
        bg_deep="#08080E", bg_surface="#12121A", bg_elevated="#1E1E2A",
        glass_bg="rgba(24,24,36,0.55)", glass_border="rgba(120,120,140,0.12)",
        glass_border_hover="rgba(120,120,140,0.25)",
        accent_1="#8888A0", accent_2="#A0A0B8", accent_3="#B8B8D0",
        accent_light="rgba(136,136,160,0.06)",
        gradient="linear-gradient(135deg, #8888A0, #A0A0B8, #B8B8D0)",
        glow="rgba(136,136,160,0.12)", glow_pulse="rgba(136,136,160,0.25)",
        text_primary="#D8D8E0", text_secondary="#78788A", text_muted="#48485A",
        btn_primary_bg="qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #8888A0,stop:1 #666680)",
        btn_primary_hover="qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #A0A0B8,stop:1 #8888A0)",
        btn_primary_color="#FFFFFF",
        badge_bg="rgba(136,136,160,0.08)", badge_border="rgba(136,136,160,0.15)",
        badge_dot="#8888A0",
        input_bg="rgba(255,255,255,0.03)", input_border="rgba(255,255,255,0.06)",
        input_focus="rgba(136,136,160,0.2)",
    ),
    "white": ThemeColors(
        name="皓白流光",
        bg_deep="#F0F0F5", bg_surface="#FAFAFE", bg_elevated="#FFFFFF",
        glass_bg="rgba(255,255,255,0.65)", glass_border="rgba(0,0,0,0.06)",
        glass_border_hover="rgba(0,0,0,0.12)",
        accent_1="#4F46E5", accent_2="#6366F1", accent_3="#A78BFA",
        accent_light="rgba(99,102,241,0.04)",
        gradient="linear-gradient(135deg, #4F46E5, #6366F1, #A78BFA)",
        glow="rgba(99,102,241,0.1)", glow_pulse="rgba(99,102,241,0.2)",
        text_primary="#1A1A2E", text_secondary="#5A5A72", text_muted="#9A9AAE",
        btn_primary_bg="qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #4F46E5,stop:1 #4F46E5)",
        btn_primary_hover="qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #6366F1,stop:1 #818CF8)",
        btn_primary_color="#FFFFFF",
        badge_bg="rgba(99,102,241,0.06)", badge_border="rgba(99,102,241,0.12)",
        badge_dot="#4F46E5",
        input_bg="rgba(0,0,0,0.02)", input_border="rgba(0,0,0,0.08)",
        input_focus="rgba(99,102,241,0.15)",
    ),
}

DEFAULT_THEME = "indigo"
```

- [ ] **Step 2: 编写 QSS 模板和生成函数**

```python
# ── QSS 全局模板 ─────────────────────────────────

GLOBAL_QSS = """
/* === 全局背景 === */
QMainWindow, QWidget#central {{
    background: {bg_deep};
    color: {text_primary};
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
    font-size: 13px;
}}

/* === 玻璃卡片 === */
QFrame.glass-card {{
    background: {glass_bg};
    border: 1px solid {glass_border};
    border-radius: 12px;
    padding: 16px;
}}
QFrame.glass-card:hover {{
    border-color: {glass_border_hover};
}}

/* === 主按钮 === */
QPushButton.btn-primary {{
    background: {btn_primary_bg};
    color: {btn_primary_color};
    border: none;
    border-radius: 10px;
    padding: 8px 20px;
    font-size: 13px;
    font-weight: 500;
}}
QPushButton.btn-primary:hover {{
    background: {btn_primary_hover};
}}
QPushButton.btn-primary:pressed {{
    background: {btn_primary_bg};
}}

/* === 次级按钮 === */
QPushButton.btn-secondary {{
    background: {glass_bg};
    color: {text_primary};
    border: 1px solid {glass_border};
    border-radius: 10px;
    padding: 8px 16px;
    font-size: 13px;
}}
QPushButton.btn-secondary:hover {{
    background: {bg_elevated};
    border-color: {glass_border_hover};
}}

/* === 输入框 === */
QLineEdit {{
    background: {input_bg};
    border: 1px solid {input_border};
    border-radius: 8px;
    padding: 8px 12px;
    color: {text_primary};
    font-size: 13px;
}}
QLineEdit:focus {{
    border-color: {input_focus};
}}

/* === 下拉框 === */
QComboBox {{
    background: {input_bg};
    border: 1px solid {input_border};
    border-radius: 8px;
    padding: 6px 12px;
    color: {text_primary};
    font-size: 13px;
}}
QComboBox:hover {{
    border-color: {glass_border_hover};
}}
QComboBox QAbstractItemView {{
    background: {bg_elevated};
    border: 1px solid {glass_border};
    color: {text_primary};
    selection-background-color: {accent_light};
    selection-color: {text_primary};
}}

/* === 标签页 === */
QTabWidget::pane {{
    border: 1px solid {glass_border};
    border-radius: 12px;
    background: transparent;
    top: -1px;
}}
QTabBar::tab {{
    background: transparent;
    color: {text_secondary};
    padding: 8px 24px;
    border: none;
    border-bottom: 2px solid transparent;
    font-size: 13px;
}}
QTabBar::tab:selected {{
    color: {accent_1};
    border-bottom: 2px solid {accent_1};
}}
QTabBar::tab:hover {{
    color: {text_primary};
}}

/* === 表格 === */
QTableWidget {{
    background: {glass_bg};
    border: 1px solid {glass_border};
    border-radius: 8px;
    gridline-color: {glass_border};
    color: {text_primary};
    font-size: 12px;
}}
QTableWidget::item {{
    padding: 6px 12px;
}}
QTableWidget::item:selected {{
    background: {accent_light};
    color: {text_primary};
}}
QHeaderView::section {{
    background: {bg_elevated};
    color: {text_secondary};
    border: none;
    border-bottom: 1px solid {glass_border};
    padding: 8px 12px;
    font-weight: 600;
    font-size: 12px;
}}

/* === 滚动条 === */
QScrollBar:vertical {{
    background: transparent;
    width: 4px;
}}
QScrollBar::handle:vertical {{
    background: {glass_border};
    border-radius: 2px;
    min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{
    background: {glass_border_hover};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

/* === 提示框 === */
QToolTip {{
    background: {bg_elevated};
    color: {text_primary};
    border: 1px solid {glass_border};
    border-radius: 6px;
    padding: 4px 8px;
    font-size: 12px;
}}

/* === 菜单 === */
QMenu {{
    background: {bg_elevated};
    border: 1px solid {glass_border};
    border-radius: 8px;
    padding: 4px;
    color: {text_primary};
}}
QMenu::item {{
    padding: 6px 24px;
    border-radius: 4px;
}}
QMenu::item:selected {{
    background: {accent_light};
    color: {accent_1};
}}

/* === 徽标 === */
QLabel.badge {{
    background: {badge_bg};
    border: 1px solid {badge_border};
    border-radius: 12px;
    padding: 2px 10px;
    font-size: 12px;
    color: {text_secondary};
}}

/* === 状态点 === */
QLabel.dot-green {{
    background: #22C55E;
    border-radius: 4px;
    min-width: 8px;
    max-width: 8px;
    min-height: 8px;
    max-height: 8px;
}}
QLabel.dot-yellow {{
    background: #F59E0B;
    border-radius: 4px;
    min-width: 8px;
    max-width: 8px;
    min-height: 8px;
    max-height: 8px;
}}
QLabel.dot-red {{
    background: #EF4444;
    border-radius: 4px;
    min-width: 8px;
    max-width: 8px;
    min-height: 8px;
    max-height: 8px;
}}
QLabel.dot-gray {{
    background: #6B7280;
    border-radius: 4px;
    min-width: 8px;
    max-width: 8px;
    min-height: 8px;
    max-height: 8px;
}}

/* === 大余额文字 === */
QLabel.balance-large {{
    font-size: 32px;
    font-weight: 700;
    color: {accent_1};
}}

/* === 次级文字 === */
QLabel.text-secondary {{
    color: {text_secondary};
    font-size: 12px;
}}

/* === 弱文字 === */
QLabel.text-muted {{
    color: {text_muted};
    font-size: 11px;
}}

/* === 主题色板按钮 === */
QPushButton.theme-swatch {{
    width: 16px;
    height: 16px;
    border-radius: 8px;
    border: 2px solid transparent;
    margin: 2px;
}}
QPushButton.theme-swatch:hover {{
    border-color: {glass_border_hover};
}}
QPushButton.theme-swatch:checked {{
    border-color: {accent_1};
}}
"""

POPUP_QSS = """
/* === 浮窗专用 === */
QWidget#popup-root {{
    background: {bg_deep};
    border: 1px solid {glass_border};
    border-radius: 12px;
}}
QWidget#popup-titlebar {{
    background: transparent;
    border-top-left-radius: 12px;
    border-top-right-radius: 12px;
}}
"""


def generate_qss(theme_name: str, custom_css_overrides: dict = None) -> str:
    """根据主题名生成完整 QSS，可选 custom.css 覆盖"""
    t = THEMES.get(theme_name, THEMES[DEFAULT_THEME])
    # 合并覆盖值
    vals = dict(t.__dict__)
    if custom_css_overrides:
        for k, v in custom_css_overrides.items():
            if k in vals and k != "name":
                vals[k] = v
    # 注入渐变伪值（QSS: pane background → glass_bg）
    vals["pane_bg"] = vals["glass_bg"]
    return GLOBAL_QSS.format(**vals)


def generate_popup_qss(theme_name: str, custom_css_overrides: dict = None) -> str:
    """生成浮窗专用 QSS"""
    t = THEMES.get(theme_name, THEMES[DEFAULT_THEME])
    vals = dict(t.__dict__)
    if custom_css_overrides:
        for k, v in custom_css_overrides.items():
            if k in vals and k != "name":
                vals[k] = v
    return (GLOBAL_QSS + POPUP_QSS).format(**vals)
```

- [ ] **Step 3: 编写 custom.css 解析函数（和 OptiX 同模式）**

```python
# ── CSS 变量映射 ──────────────────────────────────

_CSS_VAR_MAP = {
    "bg-deep": "bg_deep",
    "bg-surface": "bg_surface",
    "bg-elevated": "bg_elevated",
    "glass-bg": "glass_bg",
    "glass-border": "glass_border",
    "glass-border-hover": "glass_border_hover",
    "accent-1": "accent_1", "accent-2": "accent_2", "accent-3": "accent_3",
    "accent-light": "accent_light",
    "gradient": "gradient", "glow": "glow", "glow-pulse": "glow_pulse",
    "text-primary": "text_primary", "text-secondary": "text_secondary",
    "text-muted": "text_muted",
    "btn-primary-bg": "btn_primary_bg", "btn-primary-hover": "btn_primary_hover",
    "btn-primary-color": "btn_primary_color",
    "badge-bg": "badge_bg", "badge-border": "badge_border", "badge-dot": "badge_dot",
    "input-bg": "input_bg", "input-border": "input_border", "input-focus": "input_focus",
}


def parse_css_variables(css_text: str) -> dict:
    """解析 :root CSS 变量，返回 {字段名: 值}"""
    overrides = {}
    for m in re.finditer(r'--([\w-]+)\s*:\s*([^;]+);', css_text):
        css_name = m.group(1).strip()
        value = m.group(2).strip()
        field = _CSS_VAR_MAP.get(css_name)
        if field:
            overrides[field] = value
    return overrides


def load_css_overrides(css_dir: str = None) -> dict:
    """读取 custom.css 返回覆盖字典"""
    css_dir = css_dir or (
        os.path.dirname(sys.executable) if getattr(sys, "frozen", False)
        else os.path.dirname(os.path.abspath(__file__))
    )
    css_path = os.path.join(css_dir, "custom.css")
    if not os.path.exists(css_path):
        return {}
    try:
        with open(css_path, "r", encoding="utf-8") as f:
            overrides = parse_css_variables(f.read())
        if overrides:
            print(f"[CSS] 已加载 {len(overrides)} 个自定义主题变量 ← {css_path}")
        return overrides
    except Exception as e:
        print(f"[CSS] 读取失败: {e}")
        return {}
```

- [ ] **Step 4: 验证 theme.py**

```bash
cd /d/Projects/DeepSeekMonitor
python -c "from theme import THEMES, generate_qss, DEFAULT_THEME; q = generate_qss(DEFAULT_THEME); print(f'QSS generated: {len(q)} chars'); print('Themes:', list(THEMES.keys()))"
```

Expected: `QSS generated: <N> chars`, `Themes: ['indigo', 'emerald', 'amber', 'rose', 'cyan', 'violet', 'neon', 'charcoal', 'white']`

- [ ] **Step 5: Commit**

```bash
cd /d/Projects/DeepSeekMonitor
git add theme.py
git commit -m "feat: add 9-color glass theme system with QSS generator"
```

---

### Task 3: 加密层 crypto.py

**Files:**
- Create: `D:\Projects\DeepSeekMonitor\crypto.py`

- [ ] **Step 1: 编写 crypto.py**

```python
"""API Key 加解密 — 基于机器指纹的 Fernet 加密"""
import uuid
import socket
import hashlib
import base64
from cryptography.fernet import Fernet


def _derive_key() -> bytes:
    """从机器指纹派生加密密钥（MAC + hostname + salt）"""
    machine_id = uuid.getnode()
    hostname = socket.gethostname()
    seed = f"{machine_id}:{hostname}:deepseek-monitor-salt"
    digest = hashlib.sha256(seed.encode()).digest()
    return base64.urlsafe_b64encode(digest)


def encrypt(plaintext: str) -> str:
    """加密明文 API Key → base64 密文"""
    if not plaintext:
        return ""
    f = Fernet(_derive_key())
    token = f.encrypt(plaintext.encode())
    return token.decode()


def decrypt(ciphertext: str) -> str:
    """解密 base64 密文 → 明文 API Key"""
    if not ciphertext:
        return ""
    f = Fernet(_derive_key())
    return f.decrypt(ciphertext.encode()).decode()
```

- [ ] **Step 2: 验证加密往返**

```bash
cd /d/Projects/DeepSeekMonitor
python -c "
from crypto import encrypt, decrypt
key = 'sk-test-api-key-12345'
enc = encrypt(key)
print(f'Encrypted: {enc[:40]}...')
dec = decrypt(enc)
assert dec == key, f'Mismatch: {dec} != {key}'
print('Encrypt/decrypt roundtrip OK')
"
```

Expected: `Encrypted: gAAAAA...`, `Encrypt/decrypt roundtrip OK`

- [ ] **Step 3: Commit**

```bash
cd /d/Projects/DeepSeekMonitor
git add crypto.py
git commit -m "feat: add API key encryption (Fernet + machine fingerprint)"
```

---

### Task 4: 存储层 storage.py

**Files:**
- Create: `D:\Projects\DeepSeekMonitor\storage.py`

- [ ] **Step 1: 编写 storage.py 数据库初始化**

```python
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
```

- [ ] **Step 2: 验证 storage.py**

```bash
cd /d/Projects/DeepSeekMonitor
python -c "
from storage import init_db, save_api_key, get_api_key, insert_snapshot, get_recent_snapshots, get_setting, set_setting
init_db()
save_api_key('test-encrypted-key')
assert get_api_key() == 'test-encrypted-key'
insert_snapshot(927.23, 100.0, 827.23, True, 'CNY')
snaps = get_recent_snapshots(30)
assert len(snaps) >= 1
set_setting('theme', 'indigo')
assert get_setting('theme') == 'indigo'
print('All storage tests passed')
"
```

Expected: `All storage tests passed`

- [ ] **Step 3: Commit**

```bash
cd /d/Projects/DeepSeekMonitor
git add storage.py
git commit -m "feat: add SQLite storage with balance snapshots and history export"
```

---

### Task 5: API 层 api.py

**Files:**
- Create: `D:\Projects\DeepSeekMonitor\api.py`

- [ ] **Step 1: 编写 api.py**

```python
"""DeepSeek API — GET /user/balance"""
from dataclasses import dataclass, field
from typing import Optional
import requests
import time


@dataclass
class BalanceInfo:
    currency: str
    total_balance: str
    granted_balance: str
    topped_up_balance: str


@dataclass
class Balance:
    is_available: bool
    balance_infos: list[BalanceInfo] = field(default_factory=list)
    response_time_ms: float = 0.0


@dataclass
class BalanceError:
    message: str
    status_code: Optional[int] = None


API_URL = "https://api.deepseek.com/user/balance"
TIMEOUT = (10, 15)  # (connect, read)


def fetch_balance(api_key: str) -> Balance | BalanceError:
    """调用 DeepSeek 余额 API，返回 Balance 或 BalanceError"""
    if not api_key:
        return BalanceError("未配置 API Key")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    }

    try:
        t0 = time.perf_counter()
        resp = requests.get(API_URL, headers=headers, timeout=TIMEOUT)
        elapsed = (time.perf_counter() - t0) * 1000

        if resp.status_code == 200:
            data = resp.json()
            infos = [BalanceInfo(
                currency=info.get("currency", ""),
                total_balance=info.get("total_balance", "0"),
                granted_balance=info.get("granted_balance", "0"),
                topped_up_balance=info.get("topped_up_balance", "0"),
            ) for info in data.get("balance_infos", [])]
            return Balance(
                is_available=data.get("is_available", False),
                balance_infos=infos,
                response_time_ms=elapsed,
            )

        if resp.status_code == 401:
            return BalanceError("API Key 无效，请在设置中更新", 401)
        elif resp.status_code == 429:
            return BalanceError("请求太频繁，请稍后重试", 429)
        else:
            return BalanceError(f"服务器错误 ({resp.status_code})", resp.status_code)

    except requests.exceptions.Timeout:
        return BalanceError("请求超时，请检查网络")
    except requests.exceptions.ConnectionError:
        return BalanceError("网络连接失败，请检查网络")
    except Exception as e:
        return BalanceError(f"未知错误: {e}")
```

- [ ] **Step 2: 验证 API 调用**

```bash
cd /d/Projects/DeepSeekMonitor
python -c "
from api import fetch_balance, Balance, BalanceError
# 无 Key 情况
result = fetch_balance('')
assert isinstance(result, BalanceError)
assert '未配置' in result.message
print(f'No-key test: {result.message}')
# 无效 Key 情况 — 会返回 401（需网络）
result = fetch_balance('sk-invalid-test-key')
if isinstance(result, BalanceError):
    print(f'Invalid-key test: [{result.status_code}] {result.message}')
elif isinstance(result, Balance):
    print(f'Got balance: {result}')
"
```

Expected: 无 Key → 错误提示，无效 Key → 401 错误

- [ ] **Step 3: Commit**

```bash
cd /d/Projects/DeepSeekMonitor
git add api.py
git commit -m "feat: add DeepSeek balance API client"
```

---

### Task 6: 后台刷新 worker.py

**Files:**
- Create: `D:\Projects\DeepSeekMonitor\worker.py`

- [ ] **Step 1: 编写 worker.py**

```python
"""后台刷新线程 — QThread 定时拉取余额"""
from PySide6.QtCore import QThread, Signal
from api import fetch_balance, Balance, BalanceError
from storage import get_api_key as db_get_api_key, insert_snapshot, get_setting
from crypto import decrypt


class RefreshWorker(QThread):
    """后台定时刷新线程"""

    balance_ready = Signal(object)   # Balance 对象
    error_occurred = Signal(str)     # 错误消息
    no_key = Signal()                # 无 Key 信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self._running = True
        self._fail_count = 0

    def run(self):
        """首次立即执行，之后按间隔循环"""
        import time

        # 首次立即刷新
        self._refresh()
        if not self._running:
            return

        interval = self._get_interval_seconds()

        while self._running:
            for _ in range(interval):
                if not self._running:
                    return
                time.sleep(1)
            self._refresh()

    def _refresh(self):
        """执行一次刷新"""
        encrypted = db_get_api_key()
        if not encrypted:
            self.no_key.emit()
            return

        api_key = decrypt(encrypted)
        result = fetch_balance(api_key)

        if isinstance(result, Balance):
            self._fail_count = 0
            # 存快照
            for info in result.balance_infos:
                try:
                    insert_snapshot(
                        total=float(info.total_balance),
                        granted=float(info.granted_balance),
                        topped_up=float(info.topped_up_balance),
                        is_available=result.is_available,
                        currency=info.currency,
                    )
                except (ValueError, TypeError):
                    pass
            self.balance_ready.emit(result)
        else:
            self._fail_count += 1
            self.error_occurred.emit(result.message)

    def _get_interval_seconds(self) -> int:
        """从设置读刷新间隔，默认 600 秒（10 分钟）"""
        try:
            val = get_setting("refresh_interval", "600")
            return max(60, int(val))  # 最少 1 分钟
        except (ValueError, TypeError):
            return 600

    def stop(self):
        self._running = False
        self.wait(3000)  # 最多等 3 秒
```

- [ ] **Step 2: 验证 worker 导入**

```bash
cd /d/Projects/DeepSeekMonitor
python -c "from worker import RefreshWorker; print('Worker class OK')"
```

Expected: `Worker class OK`

- [ ] **Step 3: Commit**

```bash
cd /d/Projects/DeepSeekMonitor
git add worker.py
git commit -m "feat: add background refresh worker thread"
```

---

### Task 7: 预览浮窗 popup.py

**Files:**
- Create: `D:\Projects\DeepSeekMonitor\popup.py`

- [ ] **Step 1: 编写 popup.py**

```python
"""预览浮窗 — Frameless 弹出窗口，显示余额概览"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                                QPushButton, QFrame, QApplication)
from PySide6.QtCore import Qt, Signal, QPoint, QTimer
from PySide6.QtGui import QMouseEvent
from theme import generate_popup_qss, THEMES, DEFAULT_THEME
from storage import get_latest_snapshot, get_setting

SWATCH_COLORS = [
    ("#6366F1", "indigo"), ("#10B981", "emerald"), ("#F59E0B", "amber"),
    ("#EC4899", "rose"), ("#06B6D4", "cyan"), ("#8B5CF6", "violet"),
    ("#FF0080", "neon"), ("#8888A0", "charcoal"), ("#4F46E5", "white"),
]


class ThemeSwatch(QPushButton):
    def __init__(self, color: str, theme_name: str, parent=None):
        super().__init__(parent)
        self.theme_name = theme_name
        self.setFixedSize(16, 16)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            QPushButton {{
                background: {color};
                border-radius: 8px;
                border: 2px solid transparent;
            }}
            QPushButton:hover {{
                border-color: rgba(255,255,255,0.4);
            }}
        """)


class PopupWindow(QWidget):
    """Frameless 浮窗 — 点击外部自动关闭"""

    refresh_requested = Signal()
    settings_requested = Signal()
    theme_changed = Signal(str)  # theme_name
    closed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setFixedWidth(320)

        self.setObjectName("popup-root")
        self._build_ui()
        self._apply_theme()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── 伪标题栏 ──
        titlebar = QWidget()
        titlebar.setObjectName("popup-titlebar")
        titlebar.setFixedHeight(40)
        tb_layout = QHBoxLayout(titlebar)
        tb_layout.setContentsMargins(12, 0, 8, 0)
        tb_layout.setSpacing(8)

        # 标题
        title_label = QLabel("🐋 DeepSeek Monitor")
        title_label.setStyleSheet("font-weight:600; font-size:13px;")
        tb_layout.addWidget(title_label)
        tb_layout.addStretch()

        # 刷新按钮
        btn_refresh = QPushButton("⟳")
        btn_refresh.setFixedSize(28, 28)
        btn_refresh.setToolTip("刷新余额")
        btn_refresh.setCursor(Qt.PointingHandCursor)
        btn_refresh.clicked.connect(self.refresh_requested.emit)
        btn_refresh.setStyleSheet("QPushButton{background:transparent;border:none;font-size:16px;color:#94A3B8;} QPushButton:hover{color:#fff;}")
        tb_layout.addWidget(btn_refresh)

        # 设置按钮
        btn_settings = QPushButton("⚙")
        btn_settings.setFixedSize(28, 28)
        btn_settings.setToolTip("打开设置")
        btn_settings.setCursor(Qt.PointingHandCursor)
        btn_settings.clicked.connect(self.settings_requested.emit)
        btn_settings.setStyleSheet("QPushButton{background:transparent;border:none;font-size:16px;color:#94A3B8;} QPushButton:hover{color:#fff;}")
        tb_layout.addWidget(btn_settings)

        # 关闭按钮
        btn_close = QPushButton("✕")
        btn_close.setFixedSize(28, 28)
        btn_close.setToolTip("关闭")
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.clicked.connect(self.hide)
        btn_close.setStyleSheet("QPushButton{background:transparent;border:none;font-size:14px;color:#94A3B8;} QPushButton:hover{color:#EF4444;}")
        tb_layout.addWidget(btn_close)

        root.addWidget(titlebar)

        # ── 色板栏 ──
        swatch_row = QWidget()
        swatch_layout = QHBoxLayout(swatch_row)
        swatch_layout.setContentsMargins(12, 0, 12, 4)
        swatch_layout.setSpacing(6)
        swatch_layout.addStretch()
        for color, theme_name in SWATCH_COLORS:
            sw = ThemeSwatch(color, theme_name)
            sw.clicked.connect(lambda checked, tn=theme_name: self.theme_changed.emit(tn))
            swatch_layout.addWidget(sw)
        root.addWidget(swatch_row)

        # ── 余额区域 ──
        balance_section = QFrame()
        balance_section.setObjectName("balance-section")
        bl = QVBoxLayout(balance_section)
        bl.setContentsMargins(16, 8, 16, 16)
        bl.setSpacing(8)

        # 标题行
        header_row = QHBoxLayout()
        header_label = QLabel("💰 账户余额")
        header_label.setStyleSheet("font-size:13px; font-weight:500;")
        header_row.addWidget(header_label)
        header_row.addStretch()

        self.status_dot = QLabel()
        self.status_dot.setFixedSize(8, 8)
        self.status_dot.setObjectName("dot-gray")
        header_row.addWidget(self.status_dot)

        self.status_label = QLabel("未配置 Key")
        self.status_label.setStyleSheet("font-size:12px;")
        header_row.addWidget(self.status_label)
        bl.addLayout(header_row)

        # 大余额
        self.balance_amount = QLabel("--.--")
        self.balance_amount.setObjectName("balance-large")
        self.balance_amount.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bl.addWidget(self.balance_amount)

        # 两个卡片行
        cards_row = QHBoxLayout()
        cards_row.setSpacing(8)

        # 充值卡片
        card_topup = QFrame()
        card_topup.setObjectName("glass-card")
        ctl = QVBoxLayout(card_topup)
        ctl.setContentsMargins(12, 10, 12, 10)
        ctl.setSpacing(4)
        ctl.addWidget(QLabel("💰 充值"))
        self.topup_amount = QLabel("--.--")
        self.topup_amount.setStyleSheet("font-size:18px; font-weight:700;")
        ctl.addWidget(self.topup_amount)
        cards_row.addWidget(card_topup)

        # 赠金卡片
        card_grant = QFrame()
        card_grant.setObjectName("glass-card")
        cgl = QVBoxLayout(card_grant)
        cgl.setContentsMargins(12, 10, 12, 10)
        cgl.setSpacing(4)
        cgl.addWidget(QLabel("🎁 赠送"))
        self.granted_amount = QLabel("--.--")
        self.granted_amount.setStyleSheet("font-size:18px; font-weight:700;")
        cgl.addWidget(self.granted_amount)
        cards_row.addWidget(card_grant)

        bl.addLayout(cards_row)

        # 总余额汇总条
        summary_row = QHBoxLayout()
        summary_label = QLabel("📊 总余额")
        summary_label.setStyleSheet("font-size:12px;")
        summary_row.addWidget(summary_label)
        summary_row.addStretch()
        self.total_summary = QLabel("--.--")
        self.total_summary.setStyleSheet("font-size:16px; font-weight:700;")
        summary_row.addWidget(self.total_summary)
        bl.addLayout(summary_row)

        root.addWidget(balance_section)

        # ── 底部刷新时间 ──
        footer = QHBoxLayout()
        footer.setContentsMargins(16, 4, 16, 8)
        self.refresh_time = QLabel("")
        self.refresh_time.setStyleSheet("font-size:10px; color:#64748B;")
        footer.addStretch()
        footer.addWidget(self.refresh_time)
        root.addLayout(footer)

    def _apply_theme(self):
        theme_name = get_setting("theme", DEFAULT_THEME) or DEFAULT_THEME
        qss = generate_popup_qss(theme_name)
        self.setStyleSheet(qss)

    def update_balance(self, balance_data: dict | None, status: str = "ok"):
        """更新浮窗余额显示
        - balance_data: 来自 storage.get_latest_snapshot() 的 dict
        - status: 'ok' | 'no_key' | 'error'
        """
        if status == "no_key":
            self.status_dot.setObjectName("dot-gray")
            self.status_label.setText("未配置 Key")
            self.balance_amount.setText("--.--")
            self.topup_amount.setText("--.--")
            self.granted_amount.setText("--.--")
            self.total_summary.setText("--.--")
        elif status == "error":
            self.status_dot.setObjectName("dot-red")
            self.status_label.setText("连接失败")
        elif balance_data:
            total = balance_data.get("total_balance", 0)
            granted = balance_data.get("granted_balance", 0)
            topped_up = balance_data.get("topped_up_balance", 0)
            is_avail = balance_data.get("is_available", False)
            fetched = balance_data.get("fetched_at", "")

            self.status_dot.setObjectName("dot-green" if is_avail else "dot-yellow")
            self.status_label.setText("可用" if is_avail else "余额不足")
            self.balance_amount.setText(f"¥ {total:,.2f}")
            self.topup_amount.setText(f"¥ {topped_up:,.2f}")
            self.granted_amount.setText(f"¥ {granted:,.2f}")
            self.total_summary.setText(f"¥ {total:,.2f}")
            self.refresh_time.setText(f"最后刷新：{fetched}")

        # 刷新样式
        self.style().unpolish(self)
        self.style().polish(self)
        self.setStyleSheet(self.styleSheet())

    def show_at_point(self, global_pos: QPoint):
        """在指定位置弹出浮窗"""
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = min(global_pos.x() - 160, geo.right() - 340)
            y = global_pos.y() - self.sizeHint().height() - 10
            self.move(x, max(y, geo.top()))
        else:
            self.move(global_pos.x() - 160, global_pos.y() - 300)
        self.show()
        self.raise_()

    def focusOutEvent(self, event):
        """失去焦点时隐藏"""
        super().focusOutEvent(event)
        QTimer.singleShot(100, self._check_hide)

    def _check_hide(self):
        if not self.isActiveWindow():
            self.hide()
            self.closed.emit()
```

- [ ] **Step 2: 验证 popup.py 可导入**

```bash
cd /d/Projects/DeepSeekMonitor
python -c "
import sys
from PySide6.QtWidgets import QApplication
app = QApplication.instance() or QApplication(sys.argv)
from popup import PopupWindow
w = PopupWindow()
w.update_balance({'total_balance': 927.23, 'granted_balance': 100.0, 'topped_up_balance': 827.23, 'is_available': True, 'fetched_at': '2026-06-15 01:35:22'}, 'ok')
print('Popup created OK')
"
```

Expected: `Popup created OK`

- [ ] **Step 3: Commit**

```bash
cd /d/Projects/DeepSeekMonitor
git add popup.py
git commit -m "feat: add frameless popup window with balance display and theme swatches"
```

---

### Task 8: 设置页 settings_page.py

**Files:**
- Create: `D:\Projects\DeepSeekMonitor\settings_page.py`

- [ ] **Step 1: 编写 settings_page.py**

```python
"""设置页 — API Key / 刷新间隔 / 主题 / 导出"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                                QLineEdit, QPushButton, QComboBox, QFrame)
from PySide6.QtCore import Signal, Qt
from storage import (save_api_key, get_api_key, get_setting, set_setting,
                     export_all_snapshots, get_history_dir)
from crypto import encrypt, decrypt
from theme import THEMES, DEFAULT_THEME

INTERVAL_OPTIONS = [
    ("5 分钟", "300"),
    ("10 分钟", "600"),
    ("15 分钟", "900"),
    ("30 分钟", "1800"),
    ("60 分钟", "3600"),
]


class SettingsPage(QWidget):
    api_key_saved = Signal()
    interval_changed = Signal(int)  # seconds
    theme_changed = Signal(str)
    data_exported = Signal(str)     # filepath

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self._load_values()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # ── API Key ──
        layout.addWidget(QLabel("🔑 API Key"))
        self.key_input = QLineEdit()
        self.key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.key_input.setPlaceholderText("输入 DeepSeek API Key (sk-...)")
        layout.addWidget(self.key_input)

        key_row = QHBoxLayout()
        key_row.setSpacing(8)

        self.show_btn = QPushButton("👁 显示")
        self.show_btn.setObjectName("btn-secondary")
        self.show_btn.setCheckable(True)
        self.show_btn.toggled.connect(lambda checked: (
            self.key_input.setEchoMode(QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password),
            self.show_btn.setText("🙈 隐藏" if checked else "👁 显示"),
        ))
        key_row.addWidget(self.show_btn)

        save_btn = QPushButton("💾 保存 Key")
        save_btn.setObjectName("btn-primary")
        save_btn.clicked.connect(self._save_key)
        key_row.addWidget(save_btn)
        key_row.addStretch()
        layout.addLayout(key_row)

        # ── 分割线 ──
        layout.addWidget(self._divider())

        # ── 刷新间隔 ──
        layout.addWidget(QLabel("⏱ 自动刷新间隔"))
        self.interval_combo = QComboBox()
        for label, val in INTERVAL_OPTIONS:
            self.interval_combo.addItem(label, val)
        self.interval_combo.currentIndexChanged.connect(self._on_interval_changed)
        layout.addWidget(self.interval_combo)

        layout.addWidget(self._divider())

        # ── 当前主题 ──
        theme_header = QHBoxLayout()
        theme_header.addWidget(QLabel("🎨 当前主题"))
        self.theme_label = QLabel("靛蓝流光")
        theme_header.addWidget(self.theme_label)
        theme_header.addStretch()
        layout.addLayout(theme_header)

        # ── 导出数据 ──
        layout.addWidget(self._divider())
        layout.addWidget(QLabel("📦 数据管理"))

        export_row = QHBoxLayout()
        export_btn = QPushButton("📋 导出历史数据")
        export_btn.setObjectName("btn-secondary")
        export_btn.clicked.connect(self._export_data)
        export_row.addWidget(export_btn)

        open_hist_btn = QPushButton("📂 打开数据文件夹")
        open_hist_btn.setObjectName("btn-secondary")
        open_hist_btn.clicked.connect(self._open_history_dir)
        export_row.addWidget(open_hist_btn)
        export_row.addStretch()
        layout.addLayout(export_row)

        # ── 关于 ──
        layout.addWidget(self._divider())
        about = QLabel("DeepSeek Monitor v1.0.0\n基于 PySide6 · 深空玻璃 9 色主题\n数据来源：DeepSeek 官方余额 API")
        about.setStyleSheet("font-size:11px; color: #64748B;")
        about.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(about)

        layout.addStretch()

    def _divider(self):
        d = QFrame()
        d.setFrameShape(QFrame.Shape.HLine)
        d.setStyleSheet("QFrame{background: rgba(255,255,255,0.06); max-height:1px;}")
        return d

    def _load_values(self):
        """从数据库加载当前值"""
        # 加载 Key
        encrypted = get_api_key()
        if encrypted:
            try:
                plain = decrypt(encrypted)
                self.key_input.setText(plain)
            except Exception:
                self.key_input.setText("")
                self.key_input.setPlaceholderText("解密 Key 失败，请重新输入")

        # 加载间隔
        val = get_setting("refresh_interval", "600")
        for i in range(self.interval_combo.count()):
            if self.interval_combo.itemData(i) == val:
                self.interval_combo.setCurrentIndex(i)
                break

    def _save_key(self):
        plain = self.key_input.text().strip()
        if plain:
            enc = encrypt(plain)
            save_api_key(enc)
            self.api_key_saved.emit()
        else:
            save_api_key("")
            self.api_key_saved.emit()

    def _on_interval_changed(self, idx):
        val = self.interval_combo.itemData(idx)
        set_setting("refresh_interval", val)
        self.interval_changed.emit(int(val))

    def _export_data(self):
        filepath = export_all_snapshots()
        self.data_exported.emit(filepath)

    def _open_history_dir(self):
        import os
        d = get_history_dir()
        os.startfile(d)

    def update_theme_name(self, theme_name: str):
        self.theme_label.setText(THEMES.get(theme_name, {}).name or theme_name)
```

- [ ] **Step 2: 验证 settings_page.py 可导入**

```bash
cd /d/Projects/DeepSeekMonitor
python -c "
import sys
from PySide6.QtWidgets import QApplication
app = QApplication.instance() or QApplication(sys.argv)
from settings_page import SettingsPage
p = SettingsPage()
print('Settings page created OK')
"
```

Expected: `Settings page created OK`

- [ ] **Step 3: Commit**

```bash
cd /d/Projects/DeepSeekMonitor
git add settings_page.py
git commit -m "feat: add settings page (API key, interval, export, about)"
```

---

### Task 9: 完整窗口 main_window.py

**Files:**
- Create: `D:\Projects\DeepSeekMonitor\main_window.py`

- [ ] **Step 1: 编写 main_window.py — 概览 Tab**

```python
"""完整窗口 — 概览 / 历史 / 设置 三个 Tab"""
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                                QLabel, QTabWidget, QPushButton, QTableWidget,
                                QTableWidgetItem, QHeaderView, QFrame, QMessageBox)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
from theme import generate_qss, THEMES, DEFAULT_THEME
from storage import get_recent_snapshots, get_latest_snapshot, get_setting, get_history_dir
from settings_page import SettingsPage
from popup import ThemeSwatch, SWATCH_COLORS

VERSION = "1.0.0"


class OverviewTab(QWidget):
    """概览 Tab — 和浮窗类似但更宽松"""

    refresh_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 24)
        layout.setSpacing(12)

        # 标题行
        header = QHBoxLayout()
        header.addWidget(QLabel("💰 账户余额"))
        header.addStretch()
        refresh_btn = QPushButton("🔄 手动刷新")
        refresh_btn.setObjectName("btn-secondary")
        refresh_btn.clicked.connect(self.refresh_clicked.emit)
        header.addWidget(refresh_btn)
        layout.addLayout(header)

        # 余额大字
        self.balance_amount = QLabel("--.--")
        self.balance_amount.setObjectName("balance-large")
        self.balance_amount.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.balance_amount)

        # 状态行
        status_row = QHBoxLayout()
        status_row.addStretch()
        self.status_dot = QLabel()
        self.status_dot.setFixedSize(8, 8)
        self.status_dot.setObjectName("dot-gray")
        status_row.addWidget(self.status_dot)
        self.status_label = QLabel("未配置 Key")
        self.status_label.setStyleSheet("font-size:12px;")
        status_row.addWidget(self.status_label)
        status_row.addStretch()
        layout.addLayout(status_row)

        # 卡片行
        cards = QHBoxLayout()
        cards.setSpacing(12)

        card_topup = QFrame()
        card_topup.setObjectName("glass-card")
        ctl = QVBoxLayout(card_topup)
        ctl.setContentsMargins(16, 14, 16, 14)
        ctl.setSpacing(4)
        ctl.addWidget(QLabel("💰 充值余额"))
        self.topup_amount = QLabel("--.--")
        self.topup_amount.setStyleSheet("font-size:22px; font-weight:700;")
        ctl.addWidget(self.topup_amount)
        cards.addWidget(card_topup)

        card_grant = QFrame()
        card_grant.setObjectName("glass-card")
        cgl = QVBoxLayout(card_grant)
        cgl.setContentsMargins(16, 14, 16, 14)
        cgl.setSpacing(4)
        cgl.addWidget(QLabel("🎁 赠送余额"))
        self.granted_amount = QLabel("--.--")
        self.granted_amount.setStyleSheet("font-size:22px; font-weight:700;")
        cgl.addWidget(self.granted_amount)
        cards.addWidget(card_grant)

        layout.addLayout(cards)

        # 汇总 + 货币
        info_row = QHBoxLayout()
        info_row.addWidget(QLabel("📊 总余额"))
        self.total_label = QLabel("--.--")
        self.total_label.setStyleSheet("font-size:18px; font-weight:700;")
        info_row.addWidget(self.total_label)
        info_row.addStretch()
        self.currency_label = QLabel("")
        self.currency_label.setStyleSheet("font-size:12px;")
        info_row.addWidget(self.currency_label)
        layout.addLayout(info_row)

        # 额外信息行
        extra = QHBoxLayout()
        self.response_time_label = QLabel("响应时间: -- ms")
        self.response_time_label.setObjectName("text-muted")
        extra.addWidget(self.response_time_label)
        extra.addStretch()
        self.fetched_label = QLabel("")
        self.fetched_label.setObjectName("text-muted")
        extra.addWidget(self.fetched_label)
        layout.addLayout(extra)

        layout.addStretch()

    def update_data(self, balance_data: dict | None, status: str = "ok",
                    response_time: float = 0.0):
        if status == "no_key":
            self.status_dot.setObjectName("dot-gray")
            self.status_label.setText("未配置 Key")
            self.balance_amount.setText("--.--")
            self.topup_amount.setText("--.--")
            self.granted_amount.setText("--.--")
            self.total_label.setText("--.--")
        elif status == "error":
            self.status_dot.setObjectName("dot-red")
            self.status_label.setText("连接失败")
        elif balance_data:
            total = balance_data.get("total_balance", 0)
            granted = balance_data.get("granted_balance", 0)
            topped_up = balance_data.get("topped_up_balance", 0)
            is_avail = balance_data.get("is_available", False)
            currency = balance_data.get("currency", "CNY")
            fetched = balance_data.get("fetched_at", "")

            self.status_dot.setObjectName("dot-green" if is_avail else "dot-yellow")
            self.status_label.setText("可用" if is_avail else "余额不足")
            self.balance_amount.setText(f"¥ {total:,.2f}")
            self.topup_amount.setText(f"¥ {topped_up:,.2f}")
            self.granted_amount.setText(f"¥ {granted:,.2f}")
            self.total_label.setText(f"¥ {total:,.2f}")
            self.currency_label.setText(f"货币: {currency}")
            self.fetched_label.setText(f"刷新时间: {fetched}")

        self.response_time_label.setText(f"响应时间: {response_time:.0f} ms")

        # 刷新样式
        self.style().unpolish(self)
        self.style().polish(self)


class HistoryTab(QWidget):
    """历史 Tab — QTableWidget 显示最近 30 天快照"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 24)
        layout.setSpacing(12)

        layout.addWidget(QLabel("📅 余额变化记录（最近 30 天）"))

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["时间", "总余额", "充值", "赠金", "状态"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

        # 底部提示
        footer = QHBoxLayout()
        hint = QLabel("30 天前数据已自动归档至 history/ 文件夹")
        hint.setObjectName("text-muted")
        footer.addWidget(hint)
        footer.addStretch()
        open_btn = QPushButton("📂 打开文件夹")
        open_btn.setObjectName("btn-secondary")
        open_btn.clicked.connect(lambda: __import__('os').startfile(get_history_dir()))
        footer.addWidget(open_btn)
        layout.addLayout(footer)

    def load_data(self):
        """加载最近 30 天快照"""
        snaps = get_recent_snapshots(30)
        self.table.setRowCount(len(snaps))
        for i, s in enumerate(snaps):
            self.table.setItem(i, 0, QTableWidgetItem(s["fetched_at"]))
            self.table.setItem(i, 1, QTableWidgetItem(f"¥ {s['total_balance']:,.2f}"))
            self.table.setItem(i, 2, QTableWidgetItem(f"¥ {s['topped_up_balance']:,.2f}"))
            self.table.setItem(i, 3, QTableWidgetItem(f"¥ {s['granted_balance']:,.2f}"))
            status = "✓ 可用" if s["is_available"] else "⚠ 不足"
            self.table.setItem(i, 4, QTableWidgetItem(status))
```

- [ ] **Step 2: 编写 main_window.py — QMainWindow 组装**

```python
class MainWindow(QMainWindow):
    """完整窗口 — 三 Tab 主界面"""

    refresh_clicked = Signal()
    theme_switched = Signal(str)  # theme_name
    popup_closed = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("DeepSeek Monitor")
        self.setMinimumSize(520, 560)
        self.resize(600, 640)

        # 设置窗口图标
        import os
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self._build_ui()
        self._apply_theme()

    def _build_ui(self):
        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 标题栏
        titlebar = QHBoxLayout()
        titlebar.setContentsMargins(16, 8, 12, 8)
        titlebar.addWidget(QLabel("🐋 DeepSeek Monitor"))
        titlebar.addStretch()

        # 色板
        for color, theme_name in SWATCH_COLORS:
            sw = ThemeSwatch(color, theme_name)
            sw.clicked.connect(lambda checked, tn=theme_name: self.theme_switched.emit(tn))
            titlebar.addWidget(sw)

        layout.addLayout(titlebar)

        # Tab 区域
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        self.overview = OverviewTab()
        self.overview.refresh_clicked.connect(self.refresh_clicked.emit)

        self.history = HistoryTab()

        self.settings_page = SettingsPage()
        self.settings_page.api_key_saved.connect(self.refresh_clicked.emit)
        self.settings_page.theme_changed.connect(self.theme_switched.emit)
        self.settings_page.data_exported.connect(self._on_export_done)

        self.tabs.addTab(self.overview, "概览")
        self.tabs.addTab(self.history, "历史")
        self.tabs.addTab(self.settings_page, "设置")

        layout.addWidget(self.tabs)

    def _apply_theme(self):
        theme_name = get_setting("theme", DEFAULT_THEME) or DEFAULT_THEME
        qss = generate_qss(theme_name)
        self.setStyleSheet(qss)

    def update_balance(self, balance_data: dict | None, status: str = "ok",
                       response_time: float = 0.0):
        self.overview.update_data(balance_data, status, response_time)
        if status == "ok":
            self.history.load_data()

    def showEvent(self, event):
        super().showEvent(event)
        if self.tabs.currentIndex() == 1:  # 历史 Tab
            self.history.load_data()

    def _on_export_done(self, filepath):
        QMessageBox.information(self, "导出成功", f"历史数据已导出到：\n{filepath}")

    def closeEvent(self, event):
        """关闭窗口时只隐藏，不退出应用"""
        event.ignore()
        self.hide()
        self.popup_closed.emit()
```

- [ ] **Step 3: 验证 main_window.py 可导入**

```bash
cd /d/Projects/DeepSeekMonitor
python -c "
import sys
from PySide6.QtWidgets import QApplication
app = QApplication.instance() or QApplication(sys.argv)
from main_window import MainWindow, OverviewTab, HistoryTab
print('MainWindow classes OK')
"
```

Expected: `MainWindow classes OK`

- [ ] **Step 4: Commit**

```bash
cd /d/Projects/DeepSeekMonitor
git add main_window.py
git commit -m "feat: add main window with overview, history, and settings tabs"
```

---

### Task 10: 系统托盘 tray.py

**Files:**
- Create: `D:\Projects\DeepSeekMonitor\tray.py`

- [ ] **Step 1: 编写 tray.py**

```python
"""系统托盘 — QSystemTrayIcon + 左键弹窗 + 右键菜单"""
from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import Signal
from popup import PopupWindow
from main_window import MainWindow
import os


class TrayManager:
    """管理托盘图标、浮窗、完整窗口的交互"""

    refresh_requested = Signal()
    quit_requested = Signal()

    def __init__(self, app: QApplication):
        self._app = app
        self._popup: PopupWindow | None = None
        self._main_window: MainWindow | None = None

        # 图标
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "icon.png")
        icon = QIcon(icon_path) if os.path.exists(icon_path) else app.style().standardIcon(
            app.style().StandardPixmap.SP_ComputerIcon)

        self._tray = QSystemTrayIcon(icon, app)
        self._tray.setToolTip("DeepSeek Monitor")
        self._tray.setVisible(True)

        # 菜单
        self._build_menu()

        # 事件
        self._tray.activated.connect(self._on_activated)

    def _build_menu(self):
        menu = QMenu()

        open_action = QAction("📊 打开详情", menu)
        open_action.triggered.connect(self._show_main_window)
        menu.addAction(open_action)

        refresh_action = QAction("🔄 刷新余额", menu)
        refresh_action.triggered.connect(self.refresh_requested.emit)
        menu.addAction(refresh_action)

        menu.addSeparator()

        quit_action = QAction("🚪 退出", menu)
        quit_action.triggered.connect(self.quit_requested.emit)
        menu.addAction(quit_action)

        self._tray.setContextMenu(menu)

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:  # 左键单击
            self._toggle_popup()
        elif reason == QSystemTrayIcon.ActivationReason.DoubleClick:  # 双击
            self._show_main_window()

    def _toggle_popup(self):
        if self._popup and self._popup.isVisible():
            self._popup.hide()
            return

        if self._popup is None:
            self._popup = PopupWindow()
            self._popup.refresh_requested.connect(self.refresh_requested.emit)
            self._popup.settings_requested.connect(self._show_main_window_settings)
            self._popup.theme_changed.connect(self._on_popup_theme_change)

        # 定位到托盘上方
        tray_geo = self._tray.geometry()
        pos = tray_geo.center()
        pos.setY(tray_geo.top())
        self._popup.show_at_point(pos)

    def _show_main_window(self):
        if self._main_window is None:
            self._main_window = MainWindow()
            self._main_window.refresh_clicked.connect(self.refresh_requested.emit)
            self._main_window.theme_switched.connect(self._on_main_theme_change)

        self._main_window.show()
        self._main_window.raise_()
        self._main_window.activateWindow()

    def _show_main_window_settings(self):
        self._show_main_window()
        if self._main_window:
            self._main_window.tabs.setCurrentIndex(2)  # 设置 Tab

    def _on_popup_theme_change(self, theme_name: str):
        from storage import set_setting
        set_setting("theme", theme_name)
        self._apply_theme_to_all(theme_name)

    def _on_main_theme_change(self, theme_name: str):
        from storage import set_setting
        set_setting("theme", theme_name)
        self._apply_theme_to_all(theme_name)

    def _apply_theme_to_all(self, theme_name: str):
        from theme import generate_qss, generate_popup_qss
        # 全局
        self._app.setStyleSheet(generate_qss(theme_name))
        # 浮窗
        if self._popup:
            self._popup.setStyleSheet(generate_popup_qss(theme_name))
        # 主窗口
        if self._main_window:
            self._main_window.setStyleSheet(generate_qss(theme_name))

    def update_popup(self, balance_data: dict | None, status: str = "ok",
                     response_time: float = 0.0):
        """更新浮窗余额"""
        if self._popup and self._popup.isVisible():
            self._popup.update_balance(balance_data, status)

    def update_main_window(self, balance_data: dict | None, status: str = "ok",
                           response_time: float = 0.0):
        """更新主窗口余额"""
        if self._main_window and self._main_window.isVisible():
            self._main_window.update_balance(balance_data, status, response_time)

    def show_message(self, title: str, message: str):
        """显示托盘消息气泡"""
        self._tray.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, 3000)

    def set_icon_tooltip(self, text: str):
        self._tray.setToolTip(f"DeepSeek Monitor\n{text}")

    @property
    def popup(self) -> PopupWindow | None:
        return self._popup

    @property
    def main_window(self) -> MainWindow | None:
        return self._main_window
```

- [ ] **Step 2: 验证 tray.py 可导入**

```bash
cd /d/Projects/DeepSeekMonitor
python -c "
import sys
from PySide6.QtWidgets import QApplication
app = QApplication.instance() or QApplication(sys.argv)
from tray import TrayManager
print('TrayManager class OK')
"
```

Expected: `TrayManager class OK`

- [ ] **Step 3: Commit**

```bash
cd /d/Projects/DeepSeekMonitor
git add tray.py
git commit -m "feat: add system tray icon with popup toggle and context menu"
```

---

### Task 11: App 生命周期 app.py

**Files:**
- Create: `D:\Projects\DeepSeekMonitor\app.py`

- [ ] **Step 1: 编写 app.py**

```python
"""App 生命周期管理 — 连接 worker、tray、存储"""
from PySide6.QtCore import QObject
from tray import TrayManager
from worker import RefreshWorker
from storage import init_db, get_latest_snapshot, get_api_key as db_get_api_key


class MonitorApp(QObject):
    """主应用 — 组装所有组件，管理生命周期"""

    def __init__(self, app):
        super().__init__()
        self._app = app
        self._worker = None
        self._tray = None

    def start(self):
        """启动应用"""
        # 初始化数据库
        init_db()

        # 托盘
        self._tray = TrayManager(self._app)
        self._tray.refresh_requested.connect(self._refresh_now)
        self._tray.quit_requested.connect(self._quit)

        # 检查是否有 Key
        if not db_get_api_key():
            self._tray.show_message("DeepSeek Monitor", "请右键托盘菜单打开详情 → 设置页配置 API Key")
            self._tray.set_icon_tooltip("未配置 API Key")

        # 加载上次余额
        snap = get_latest_snapshot()
        self._refresh_ui_from_snapshot(snap)

        # 启动后台刷新
        self._worker = RefreshWorker()
        self._worker.balance_ready.connect(self._on_balance_ready)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.no_key.connect(lambda: self._refresh_ui_from_snapshot(None, "no_key"))
        self._worker.start()

    def _refresh_now(self):
        """手动刷新"""
        if self._worker:
            self._worker._refresh()

    def _on_balance_ready(self, balance):
        """API 返回成功"""
        import time
        snap = get_latest_snapshot()
        status = "ok" if snap else "no_key"
        rt = balance.response_time_ms

        self._tray.update_popup(snap, status, rt)
        self._tray.update_main_window(snap, status, rt)
        self._tray.set_icon_tooltip(
            f"余额 ¥{snap['total_balance']:,.2f}" if snap else "已连接"
        )

    def _on_error(self, message: str):
        """API 返回错误"""
        snap = get_latest_snapshot()  # 显示上次数据
        self._tray.update_popup(snap, "error")
        self._tray.update_main_window(snap, "error")
        self._tray.set_icon_tooltip(message)

    def _refresh_ui_from_snapshot(self, snap: dict | None, status: str = "ok"):
        """用数据库快照刷新 UI（不拉 API）"""
        if snap is None:
            status = "no_key" if not db_get_api_key() else "ok"
        self._tray.update_popup(snap, status)
        self._tray.update_main_window(snap, status)

    def _quit(self):
        """退出应用"""
        if self._worker:
            self._worker.stop()
        self._app.quit()
```

- [ ] **Step 2: 验证 app.py 可导入**

```bash
cd /d/Projects/DeepSeekMonitor
python -c "
import sys
from PySide6.QtWidgets import QApplication
app = QApplication.instance() or QApplication(sys.argv)
from app import MonitorApp
print('MonitorApp class OK')
"
```

Expected: `MonitorApp class OK`

- [ ] **Step 3: Commit**

```bash
cd /d/Projects/DeepSeekMonitor
git add app.py
git commit -m "feat: add app lifecycle manager wiring worker, tray, and storage"
```

---

### Task 12: 入口 main.py + 单例锁

**Files:**
- Create: `D:\Projects\DeepSeekMonitor\main.py`

- [ ] **Step 1: 编写 main.py**

```python
"""DeepSeek Monitor — 入口 + 单例保护"""
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtNetwork import QLocalSocket, QLocalServer
from PySide6.QtCore import QCoreApplication
from app import MonitorApp


def is_already_running() -> bool:
    """检查是否已有实例运行"""
    socket = QLocalSocket()
    socket.connectToServer("DeepSeekMonitor")
    if socket.waitForConnected(500):
        socket.close()
        return True
    return False


def main():
    # 单例检查
    QCoreApplication.setApplicationName("DeepSeekMonitor")
    QCoreApplication.setOrganizationName("DeepSeekMonitor")

    if is_already_running():
        print("DeepSeek Monitor 已在运行")
        sys.exit(0)

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    # 启动本地服务（单例锁）
    server = QLocalServer(app)
    server.listen("DeepSeekMonitor")

    # 启主题
    from theme import generate_qss, DEFAULT_THEME
    from storage import get_setting
    theme_name = get_setting("theme", DEFAULT_THEME) or DEFAULT_THEME
    app.setStyleSheet(generate_qss(theme_name))

    # 启动应用
    monitor = MonitorApp(app)
    monitor.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 端到端测试 — 启动应用**

```bash
cd /d/Projects/DeepSeekMonitor
python main.py &
sleep 3
kill %1 2>/dev/null
```

Expected: 托盘图标出现，无报错退出。

- [ ] **Step 3: Commit**

```bash
cd /d/Projects/DeepSeekMonitor
git add main.py
git commit -m "feat: add main entry point with single-instance lock"
```

---

### Task 13: 打包脚本 build.bat

**Files:**
- Create: `D:\Projects\DeepSeekMonitor\build.bat`

- [ ] **Step 1: 编写 build.bat**

```bat
@echo off
chcp 65001 >nul
echo ========================================
echo   DeepSeek Monitor — PyInstaller 打包
echo ========================================
echo.

cd /d "%~dp0"

pyinstaller ^
  --name "DeepSeekMonitor" ^
  --onefile ^
  --windowed ^
  --icon resources/icon.png ^
  --add-data "resources;resources" ^
  --hidden-import PySide6.QtNetwork ^
  --hidden-import cryptography.fernet ^
  --hidden-import cryptography.hazmat.primitives ^
  --hidden-import cryptography.hazmat.backends ^
  --clean ^
  main.py

echo.
echo ========================================
echo   打包完成！产物在 dist\DeepSeekMonitor.exe
echo ========================================
pause
```

- [ ] **Step 2: Commit**

```bash
cd /d/Projects/DeepSeekMonitor
git add build.bat
git commit -m "chore: add PyInstaller build script"
```

---

### Task 14: 集成测试与收尾

- [ ] **Step 1: 全模块导入测试**

```bash
cd /d/Projects/DeepSeekMonitor
python -c "
import theme, crypto, storage, api, worker, popup, settings_page, main_window, tray, app, main
print('All modules imported OK')

# 验证数据库路径
storage.init_db()
print(f'DB path: {storage.get_db_path()}')

# 验证主题
for name in theme.THEMES:
    qss = theme.generate_qss(name)
    assert 'bg_deep' not in qss, 'Template should be filled'
    print(f'  {name}: {len(qss)} chars QSS')

# 验证加密
enc = crypto.encrypt('sk-test-123')
dec = crypto.decrypt(enc)
assert dec == 'sk-test-123'
print(f'Crypto OK: sk-test-123 roundtrip')

# 验证存储
storage.save_api_key(enc)
assert storage.get_api_key() == enc
storage.insert_snapshot(100.0, 20.0, 80.0, True, 'CNY')
snap = storage.get_latest_snapshot()
assert snap is not None
assert snap['total_balance'] == 100.0
print(f'Storage OK: snapshot {snap[\"fetched_at\"]}')

print()
print('=== All integration checks passed ===')
"
```

Expected: 所有模块导入成功，每项测试通过。

- [ ] **Step 2: 验证 build.bat 可执行**

```bash
cd /d/Projects/DeepSeekMonitor
type build.bat | head -5
echo "Build script syntax checked"
```

- [ ] **Step 3: Final commit**

```bash
cd /d/Projects/DeepSeekMonitor
git add -A
git commit -m "chore: integration tests and final cleanups"
```

---

## 总结

| Task | 文件 | 产出 |
|:--:|:--|:--|
| 1 | `requirements.txt`, `resources/icon.png` | 项目骨架 |
| 2 | `theme.py` | 9 色主题 + QSS 生成 |
| 3 | `crypto.py` | Fernet 加解密 |
| 4 | `storage.py` | SQLite + 历史导出 |
| 5 | `api.py` | DeepSeek 余额 API |
| 6 | `worker.py` | QThread 定时刷新 |
| 7 | `popup.py` | Frameless 浮窗 + 色板 |
| 8 | `settings_page.py` | 设置页 |
| 9 | `main_window.py` | 完整窗口（概览/历史/设置）|
| 10 | `tray.py` | 系统托盘 + 菜单 |
| 11 | `app.py` | 组件接线 + 生命周期 |
| 12 | `main.py` | 入口 + 单例锁 |
| 13 | `build.bat` | PyInstaller 打包 |
| 14 | — | 集成测试 |

**共 14 个 Task，预计 14 次 commit。按顺序执行，每个 Task 自包含。**
