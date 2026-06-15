from __future__ import annotations


INK_BLUE = "#4169E1"
READY_GREEN = "#12B76A"
MISSING_YELLOW = "#F79009"
ERROR_RED = "#F04438"
TEXT = "#1D2433"
MUTED = "#667085"
BACKGROUND = "#F7F8FA"
PANEL = "#FFFFFF"
BORDER = "#E4E7EC"


LIGHT_QSS = f"""
QMainWindow {{
    background: {BACKGROUND};
}}
QWidget {{
    color: {TEXT};
    font-family: "Segoe UI", "Microsoft JhengHei UI", sans-serif;
    font-size: 10pt;
}}
QFrame#Panel {{
    background: {PANEL};
    border: 1px solid {BORDER};
    border-radius: 8px;
}}
QLabel#Muted {{
    color: {MUTED};
}}
QPushButton {{
    background: {PANEL};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 6px 10px;
}}
QPushButton:hover {{
    border-color: {INK_BLUE};
}}
QPushButton#PrimaryButton {{
    background: {INK_BLUE};
    border-color: {INK_BLUE};
    color: white;
}}
QLineEdit {{
    background: {PANEL};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 6px 8px;
}}
QGraphicsView {{
    background: #ECEFF3;
    border: 1px solid {BORDER};
    border-radius: 8px;
}}
"""

