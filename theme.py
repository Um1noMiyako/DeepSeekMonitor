"""DeepSeek Monitor — 皓白流光主题 → PySide6 QSS"""
from dataclasses import dataclass
import os, sys, re


@dataclass
class ThemeColors:
    name: str
    bg_deep: str; bg_surface: str; bg_elevated: str
    glass_bg: str; glass_border: str; glass_border_hover: str
    accent_1: str; accent_2: str; accent_3: str; accent_light: str
    gradient: str; glow: str; glow_pulse: str
    text_primary: str; text_secondary: str; text_muted: str
    btn_primary_bg: str; btn_primary_hover: str; btn_primary_color: str
    badge_bg: str; badge_border: str; badge_dot: str
    input_bg: str; input_border: str; input_focus: str


THEME = ThemeColors(
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
)


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
    background-color: {bg_elevated};
    border: 1px solid {glass_border};
    color: {text_primary};
    selection-background-color: {accent_light};
    selection-color: {text_primary};
    outline: none;
}}
QComboBox QAbstractItemView::item {{
    background-color: {bg_elevated};
    color: {text_primary};
    padding: 6px 12px;
}}
QComboBox QAbstractItemView::item:selected {{
    background-color: {accent_light};
    color: {accent_1};
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

/* === 状态点 === */
QLabel.dot-green {{
    background: #22C55E;
    border-radius: 4px;
    min-width: 8px; max-width: 8px; min-height: 8px; max-height: 8px;
}}
QLabel.dot-yellow {{
    background: #F59E0B;
    border-radius: 4px;
    min-width: 8px; max-width: 8px; min-height: 8px; max-height: 8px;
}}
QLabel.dot-red {{
    background: #EF4444;
    border-radius: 4px;
    min-width: 8px; max-width: 8px; min-height: 8px; max-height: 8px;
}}
QLabel.dot-gray {{
    background: #6B7280;
    border-radius: 4px;
    min-width: 8px; max-width: 8px; min-height: 8px; max-height: 8px;
}}

/* === 大余额文字 === */
QLabel.balance-large {{
    font-size: 32px;
    font-weight: 700;
    color: {accent_1};
}}

/* === 浮窗标题 === */
QLabel#popup-title {{
    font-weight: 600;
    font-size: 13px;
    color: {text_primary};
}}

QPushButton#popup-refresh, QPushButton#popup-settings {{
    background: transparent; border: none; font-size: 16px; color: {text_secondary};
}}
QPushButton#popup-refresh:hover, QPushButton#popup-settings:hover {{
    color: {text_primary};
}}
QPushButton#popup-close {{
    background: transparent; border: none; font-size: 14px; color: {text_secondary};
}}
QPushButton#popup-close:hover {{ color: #EF4444; }}

/* === 余额区域 === */
QLabel#balance-header {{ font-size: 13px; font-weight: 500; color: {text_primary}; }}
QLabel#status-text {{ font-size: 12px; color: {text_secondary}; }}
QLabel#card-amount {{ font-size: 18px; font-weight: 700; color: {text_primary}; }}
QLabel#summary-label {{ font-size: 12px; color: {text_primary}; }}
QLabel#summary-amount {{ font-size: 16px; font-weight: 700; color: {text_primary}; }}
QLabel#refresh-time {{ font-size: 10px; color: {text_muted}; }}

/* === 概览 Tab === */
QPushButton#overview-refresh {{
    background: {glass_bg}; color: {text_primary};
    border: 1px solid {glass_border}; border-radius: 10px;
    padding: 8px 16px; font-size: 13px;
}}
QPushButton#overview-refresh:hover {{ background: {bg_elevated}; border-color: {glass_border_hover}; }}
QLabel#overview-header {{ font-size: 14px; font-weight: 500; color: {text_primary}; }}
QLabel#overview-balance {{ font-size: 32px; font-weight: 700; color: {accent_1}; }}
QLabel#overview-card-amount {{ font-size: 22px; font-weight: 700; color: {text_primary}; }}
QLabel#overview-total {{ font-size: 18px; font-weight: 700; color: {text_primary}; }}
QLabel#overview-currency {{ font-size: 12px; color: {text_secondary}; }}
QLabel#overview-fetched {{ font-size: 11px; color: {text_muted}; }}
QLabel#overview-response-time {{ font-size: 11px; color: {text_muted}; }}
QLabel#overview-status {{ font-size: 12px; color: {text_secondary}; }}
QLabel#overview-card-label {{ font-size: 13px; color: {text_secondary}; }}

/* === 历史 Tab === */
QLabel#history-title {{ font-size: 14px; font-weight: 500; color: {text_primary}; }}
QLabel#history-hint {{ font-size: 11px; color: {text_muted}; }}
QPushButton#history-open {{
    background: {glass_bg}; color: {text_primary};
    border: 1px solid {glass_border}; border-radius: 10px; padding: 8px 16px;
}}
QPushButton#history-open:hover {{ background: {bg_elevated}; border-color: {glass_border_hover}; }}

/* === 设置页 === */
QLabel#about-text {{ font-size: 11px; color: {text_muted}; }}
QLabel#preset-hint {{ font-size: 11px; color: {text_muted}; }}
QFrame#settings-divider {{ background: {glass_border}; max-height: 1px; }}
QDialog {{ background: {bg_surface}; color: {text_primary}; }}

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

POPUP_QSS = ""

COMBO_DROPDOWN = """
QAbstractItemView {{
    background-color: {bg_elevated};
    border: 1px solid {glass_border};
    color: {text_primary};
    font-size: 13px;
    outline: none;
}}
QAbstractItemView::item {{
    background-color: {bg_elevated};
    color: {text_primary};
    padding: 6px 12px;
}}
QAbstractItemView::item:selected {{
    background-color: {accent_light};
    color: {accent_1};
}}
"""


def generate_qss() -> str:
    vals = dict(THEME.__dict__)
    return GLOBAL_QSS.format(**vals)


def generate_combo_dropdown_qss() -> str:
    """专门给 QComboBox.view().setStyleSheet() 用的下拉样式"""
    vals = dict(THEME.__dict__)
    return COMBO_DROPDOWN.format(**vals)


def generate_popup_qss() -> str:
    return generate_qss()
