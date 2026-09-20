"""Barra de herramientas flotante o integrada para el editor de grafos estilo Draw.io."""

from __future__ import annotations
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
)


class BarraHerramientasGrafo(QFrame):
    """Barra de herramientas superior con botones de acción para editar el grafo.

    Señales:
        modo_cambiado (str): Emite el modo activo ('seleccion', 'crear_estado', 'conectar', 'borrar').
        auto_organizar_solicitado (): Emite cuando se solicita reordenar los nodos.
        limpiar_solicitado (): Emite cuando se solicita limpiar todo el lienzo.
    """

    modo_cambiado = pyqtSignal(str)
    auto_organizar_solicitado = pyqtSignal()
    limpiar_solicitado = pyqtSignal()
    ayuda_solicitada = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setStyleSheet(
            "QFrame { background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 4px; }"
            "QPushButton { background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px; "
            "padding: 6px 12px; font-weight: 600; font-size: 12px; color: #334155; }"
            "QPushButton:hover { background-color: #f1f5f9; border-color: #94a3b8; }"
            "QPushButton:checked { background-color: #dbeafe; border-color: #2563eb; color: #1d4ed8; }"
        )
        self._inicializar_ui()

    def _inicializar_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(8)

        etiqueta_herramientas = QLabel("Herramientas:")
        etiqueta_herramientas.setStyleSheet("font-weight: bold; color: #64748b; font-size: 11px;")
        layout.addWidget(etiqueta_herramientas)

        self.grupo_botones = QButtonGroup(self)
        self.grupo_botones.setExclusive(True)

        self.boton_seleccionar = QPushButton("🖱️ Mover / Cursor")
        self.boton_seleccionar.setCheckable(True)
        self.boton_seleccionar.setChecked(True)
        self.boton_seleccionar.setToolTip("Arrastrar estados y seleccionar elementos (Esc)")
        self.boton_seleccionar.clicked.connect(lambda: self.modo_cambiado.emit("seleccion"))
        self.grupo_botones.addButton(self.boton_seleccionar)
        layout.addWidget(self.boton_seleccionar)

        self.boton_crear_estado = QPushButton("➕⭕ Crear Estado")
        self.boton_crear_estado.setCheckable(True)
        self.boton_crear_estado.setToolTip("Haga clic en el lienzo para plantar un nuevo estado")
        self.boton_crear_estado.clicked.connect(lambda: self.modo_cambiado.emit("crear_estado"))
        self.grupo_botones.addButton(self.boton_crear_estado)
        layout.addWidget(self.boton_crear_estado)

        self.boton_conectar = QPushButton("➔ Conectar Flecha")
        self.boton_conectar.setCheckable(True)
        self.boton_conectar.setToolTip("Haga clic en un estado origen y arrastre hacia el destino")
        self.boton_conectar.clicked.connect(lambda: self.modo_cambiado.emit("conectar"))
        self.grupo_botones.addButton(self.boton_conectar)
        layout.addWidget(self.boton_conectar)

        self.boton_borrar = QPushButton("🗑️ Borrar")
        self.boton_borrar.setCheckable(True)
        self.boton_borrar.setToolTip("Haga clic en un estado o flecha para eliminarlo (o use tecla Supr)")
        self.boton_borrar.clicked.connect(lambda: self.modo_cambiado.emit("borrar"))
        self.grupo_botones.addButton(self.boton_borrar)
        layout.addWidget(self.boton_borrar)

        layout.addSpacing(12)

        self.boton_auto_organizar = QPushButton("🔄 Auto-distribuir")
        self.boton_auto_organizar.setToolTip("Organiza los estados automáticamente en círculo estético")
        self.boton_auto_organizar.clicked.connect(self.auto_organizar_solicitado.emit)
        layout.addWidget(self.boton_auto_organizar)

        self.boton_limpiar = QPushButton("🧹 Limpiar Grafo")
        self.boton_limpiar.setStyleSheet(
            "QPushButton { background-color: #fef2f2; border-color: #fca5a5; color: #b91c1c; }"
            "QPushButton:hover { background-color: #fee2e2; border-color: #f87171; }"
        )
        self.boton_limpiar.clicked.connect(self.limpiar_solicitado.emit)
        layout.addWidget(self.boton_limpiar)

        layout.addSpacing(12)

        self.boton_ayuda = QPushButton("📖 ¿Cómo usar el programa?")
        self.boton_ayuda.setStyleSheet(
            "QPushButton { background-color: #eff6ff; border-color: #93c5fd; color: #1d4ed8; font-weight: bold; }"
            "QPushButton:hover { background-color: #dbeafe; border-color: #60a5fa; }"
        )
        self.boton_ayuda.setToolTip("Ver la guía de uso y manual rápido de instrucciones")
        self.boton_ayuda.clicked.connect(self.ayuda_solicitada.emit)
        layout.addWidget(self.boton_ayuda)

        layout.addStretch(1)

        # Indicador de atajos
        etiqueta_atajos = QLabel("Atajos: Supr (Eliminar) | Esc (Cursor)")
        etiqueta_atajos.setStyleSheet("color: #64748b; font-size: 11px; font-weight: 500;")
        layout.addWidget(etiqueta_atajos)

    def activar_modo_seleccion(self) -> None:
        """Fuerza la activación del botón de modo selección."""
        self.boton_seleccionar.setChecked(True)
        self.modo_cambiado.emit("seleccion")
