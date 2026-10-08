"""Modern dark stylesheet and visual tokens for Flash Automator."""

DARK_THEME_QSS = """
/* Global Window & Fonts */
QMainWindow, QDialog, QWidget {
    background-color: #12141a;
    color: #e2e8f0;
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, 'Roboto', sans-serif;
    font-size: 13px;
}

/* Sidebar */
#SidebarWidget {
    background-color: #181b24;
    border-right: 1px solid #262b3a;
    min-width: 220px;
    max-width: 220px;
}

#AppTitleLabel {
    color: #38bdf8;
    font-size: 18px;
    font-weight: 800;
    letter-spacing: 0.5px;
    padding: 18px 12px 10px 16px;
}

#AppSubtitleLabel {
    color: #64748b;
    font-size: 11px;
    font-weight: 500;
    padding: 0px 12px 16px 16px;
}

/* Nav Buttons */
QPushButton.nav-btn {
    text-align: left;
    padding: 10px 16px;
    background-color: transparent;
    border: none;
    border-radius: 8px;
    color: #94a3b8;
    font-size: 13px;
    font-weight: 600;
    margin: 3px 10px;
}

QPushButton.nav-btn:hover {
    background-color: #222736;
    color: #f1f5f9;
}

QPushButton.nav-btn:checked, QPushButton.nav-btn.active {
    background-color: #2563eb;
    color: #ffffff;
}

/* Cards & Panels */
QFrame.card {
    background-color: #1a1e29;
    border: 1px solid #282f42;
    border-radius: 10px;
    padding: 16px;
}

QFrame.card-highlight {
    background-color: #1e2433;
    border: 1px solid #3b82f6;
    border-radius: 10px;
    padding: 16px;
}

QLabel.card-title {
    color: #f8fafc;
    font-size: 15px;
    font-weight: 700;
}

QLabel.card-subtitle {
    color: #94a3b8;
    font-size: 12px;
}

QLabel.stat-value {
    color: #38bdf8;
    font-size: 28px;
    font-weight: 800;
}

/* Standard Buttons */
QPushButton {
    background-color: #242a3a;
    color: #e2e8f0;
    border: 1px solid #333c52;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #2d354a;
    border-color: #475569;
}

QPushButton:pressed {
    background-color: #1e2330;
}

QPushButton.btn-primary {
    background-color: #2563eb;
    color: #ffffff;
    border: none;
}

QPushButton.btn-primary:hover {
    background-color: #1d4ed8;
}

QPushButton.btn-success {
    background-color: #059669;
    color: #ffffff;
    border: none;
}

QPushButton.btn-success:hover {
    background-color: #047857;
}

QPushButton.btn-danger {
    background-color: #dc2626;
    color: #ffffff;
    border: none;
}

QPushButton.btn-danger:hover {
    background-color: #b91c1c;
}

QPushButton.btn-variable {
    background-color: #7c3aed;
    color: #ffffff;
    border: none;
    font-weight: 700;
}

QPushButton.btn-variable:hover {
    background-color: #6d28d9;
}

/* Inputs & Edits */
QLineEdit, QComboBox, QSpinBox, QDateEdit, QTextEdit {
    background-color: #161922;
    border: 1px solid #2d3447;
    border-radius: 6px;
    padding: 7px 10px;
    color: #f1f5f9;
    selection-background-color: #2563eb;
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDateEdit:focus, QTextEdit:focus {
    border-color: #38bdf8;
}

QComboBox::drop-down {
    border: none;
    padding-right: 8px;
}

/* Tables & Lists */
QTableWidget, QTreeWidget, QListWidget {
    background-color: #161922;
    border: 1px solid #282f42;
    border-radius: 8px;
    gridline-color: #232838;
    color: #e2e8f0;
    selection-background-color: #25334d;
    selection-color: #ffffff;
}

QHeaderView::section {
    background-color: #1e2330;
    color: #94a3b8;
    padding: 8px;
    font-weight: 700;
    border: none;
    border-bottom: 1px solid #2b3347;
}

QTableWidget::item {
    padding: 6px;
    border-bottom: 1px solid #1c202d;
}

/* ScrollBars */
QScrollBar:vertical {
    border: none;
    background: #141720;
    width: 8px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #2e3549;
    border-radius: 4px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background: #475569;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Progress Bar */
QProgressBar {
    background-color: #1a1e2b;
    border: 1px solid #282f42;
    border-radius: 6px;
    text-align: center;
    color: #ffffff;
    font-weight: 700;
    height: 18px;
}

QProgressBar::chunk {
    background-color: #2563eb;
    border-radius: 5px;
}

/* Tab Widget */
QTabWidget::pane {
    border: 1px solid #282f42;
    background-color: #161922;
    border-radius: 6px;
}

QTabBar::tab {
    background-color: #1e2330;
    color: #94a3b8;
    padding: 8px 16px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 4px;
}

QTabBar::tab:selected {
    background-color: #2563eb;
    color: #ffffff;
}
"""
