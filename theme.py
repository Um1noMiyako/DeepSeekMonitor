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
