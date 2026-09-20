"""Tema visual claro, limpio y de alto contraste para SimulaAutomata.

Fuerza una paleta clara y reglas de estilo QSS consistentes para evitar
que el modo oscuro del sistema operativo (Windows 11) opaque textos,
invierta fondos o haga ilegibles los controles e inputs.
"""

from __future__ import annotations
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication


ESTILO_TEMA_CLARO = """
/* Reglas globales de la aplicación */
QWidget {
    background-color: #f8fafc;
    color: #0f172a;
    font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    font-size: 13px;
}

/* Ventana Principal y Diálogos */
QMainWindow, QDialog {
    background-color: #f1f5f9;
}

/* Agrupadores y Tarjetas */
QGroupBox {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    margin-top: 14px;
    padding-top: 14px;
    font-weight: 700;
    color: #1e293b;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 14px;
    padding: 0 6px;
    background-color: #ffffff;
    color: #1e293b;
    font-size: 13px;
    font-weight: 700;
}

/* Campos de entrada de texto */
QLineEdit {
    background-color: #ffffff;
    color: #0f172a;
    border: 1.5px solid #cbd5e1;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 13px;
    selection-background-color: #3b82f6;
    selection-color: #ffffff;
}

QLineEdit:focus {
    border: 2px solid #2563eb;
    background-color: #ffffff;
}

QLineEdit:disabled {
    background-color: #f1f5f9;
    color: #94a3b8;
    border-color: #e2e8f0;
}

/* Botones estándar */
QPushButton {
    background-color: #ffffff;
    color: #1e293b;
    border: 1.5px solid #cbd5e1;
    border-radius: 6px;
    padding: 7px 14px;
    font-weight: 600;
    font-size: 12px;
}

QPushButton:hover {
    background-color: #f1f5f9;
    border-color: #94a3b8;
    color: #0f172a;
}

QPushButton:pressed {
    background-color: #e2e8f0;
}

QPushButton:checked {
    background-color: #dbeafe;
    border-color: #2563eb;
    color: #1d4ed8;
    font-weight: 700;
}

QPushButton:disabled {
    background-color: #f8fafc;
    color: #cbd5e1;
    border-color: #e2e8f0;
}

/* Botones primarios (azules) */
QPushButton[clase="primario"] {
    background-color: #2563eb;
    color: #ffffff;
    border: 1.5px solid #1d4ed8;
}

QPushButton[clase="primario"]:hover {
    background-color: #1d4ed8;
}

/* Pestañas (QTabWidget) */
QTabWidget::pane {
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    background-color: #ffffff;
    top: -1px;
}

QTabBar::tab {
    background-color: #e2e8f0;
    color: #475569;
    border: 1px solid #cbd5e1;
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    padding: 8px 16px;
    margin-right: 4px;
    font-weight: 600;
    font-size: 12px;
}

QTabBar::tab:hover {
    background-color: #f1f5f9;
    color: #1e293b;
}

QTabBar::tab:selected {
    background-color: #ffffff;
    color: #2563eb;
    border-color: #cbd5e1;
    font-weight: 700;
}

/* Tablas (QTableWidget) */
QTableWidget {
    background-color: #ffffff;
    color: #0f172a;
    gridline-color: #e2e8f0;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    alternate-background-color: #f8fafc;
    selection-background-color: #dbeafe;
    selection-color: #1e293b;
    font-size: 13px;
}

QHeaderView::section {
    background-color: #f1f5f9;
    color: #334155;
    font-weight: 700;
    font-size: 12px;
    border: 1px solid #e2e8f0;
    padding: 6px 8px;
}

/* Separadores (QSplitter) */
QSplitter::handle {
    background-color: #cbd5e1;
    border-radius: 2px;
}

QSplitter::handle:hover {
    background-color: #3b82f6;
}

/* Barras de desplazamiento */
QScrollBar:vertical {
    background-color: #f8fafc;
    width: 10px;
    border-radius: 5px;
}

QScrollBar::handle:vertical {
    background-color: #cbd5e1;
    border-radius: 5px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #94a3b8;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background-color: #f8fafc;
    height: 10px;
    border-radius: 5px;
}

QScrollBar::handle:horizontal {
    background-color: #cbd5e1;
    border-radius: 5px;
    min-width: 20px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #94a3b8;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* Barra de estado */
QStatusBar {
    background-color: #ffffff;
    color: #475569;
    border-top: 1px solid #e2e8f0;
    font-size: 12px;
}

/* Casillas de verificación (QCheckBox) */
QCheckBox {
    color: #1e293b;
    font-weight: 500;
    spacing: 6px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1.5px solid #94a3b8;
    border-radius: 4px;
    background-color: #ffffff;
}

QCheckBox::indicator:checked {
    background-color: #2563eb;
    border-color: #1d4ed8;
}

/* Cuadros de texto multilínea y visores de ayuda */
QTextBrowser, QTextEdit {
    background-color: #ffffff;
    color: #1e293b;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 10px;
    line-height: 1.5;
}
"""


def aplicar_tema_claro(app: QApplication) -> None:
    """Aplica la paleta y estilos de tema claro para garantizar visibilidad total."""
    app.setStyle("Fusion")

    # Forzar paleta clara en el sistema Qt
    paleta = QPalette()
    paleta.setColor(QPalette.ColorRole.Window, QColor("#f8fafc"))
    paleta.setColor(QPalette.ColorRole.WindowText, QColor("#0f172a"))
    paleta.setColor(QPalette.ColorRole.Base, QColor("#ffffff"))
    paleta.setColor(QPalette.ColorRole.AlternateBase, QColor("#f1f5f9"))
    paleta.setColor(QPalette.ColorRole.ToolTipBase, QColor("#0f172a"))
    paleta.setColor(QPalette.ColorRole.ToolTipText, QColor("#ffffff"))
    paleta.setColor(QPalette.ColorRole.Text, QColor("#0f172a"))
    paleta.setColor(QPalette.ColorRole.Button, QColor("#ffffff"))
    paleta.setColor(QPalette.ColorRole.ButtonText, QColor("#0f172a"))
    paleta.setColor(QPalette.ColorRole.BrightText, QColor("#ef4444"))
    paleta.setColor(QPalette.ColorRole.Highlight, QColor("#2563eb"))
    paleta.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))

    app.setPalette(paleta)
    app.setStyleSheet(ESTILO_TEMA_CLARO)
