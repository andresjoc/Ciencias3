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
    zoom_acercar_solicitado = pyqtSignal()
    zoom_alejar_solicitado = pyqtSignal()
    zoom_restablecer_solicitado = pyqtSignal()
    conversion_dfa_solicitada = pyqtSignal()
    deshacer_solicitado = pyqtSignal()
    rehacer_solicitado = pyqtSignal()

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
        self.boton_seleccionar.setToolTip(
            "Barra de Herramientas: Modo Cursor (Esc).\n"
            "Arrastra estados, selecciona elementos o haz clic sobre una conexión para abrir el selector de caracteres."
        )
        self.boton_seleccionar.clicked.connect(lambda: self.modo_cambiado.emit("seleccion"))
        self.grupo_botones.addButton(self.boton_seleccionar)
        layout.addWidget(self.boton_seleccionar)

        self.boton_desplazar = QPushButton("✋ Desplazar Vista")
        self.boton_desplazar.setCheckable(True)
        self.boton_desplazar.setToolTip(
            "Barra de Herramientas: Modo Mano / Desplazar Vista.\n"
            "Mantenga el clic izquierdo presionado y arrastre para mover la vista de la pizarra en cualquier dirección."
        )
        self.boton_desplazar.clicked.connect(lambda: self.modo_cambiado.emit("desplazar"))
        self.grupo_botones.addButton(self.boton_desplazar)
        layout.addWidget(self.boton_desplazar)

        self.boton_crear_estado = QPushButton("➕⭕ Crear Estado")
        self.boton_crear_estado.setCheckable(True)
        self.boton_crear_estado.setToolTip(
            "Barra de Herramientas: Modo Crear Estado.\nHaz clic sobre la pizarra para plantar un nuevo nodo."
        )
        self.boton_crear_estado.clicked.connect(lambda: self.modo_cambiado.emit("crear_estado"))
        self.grupo_botones.addButton(self.boton_crear_estado)
        layout.addWidget(self.boton_crear_estado)

        self.boton_conectar = QPushButton("➔ Conectar Flecha")
        self.boton_conectar.setCheckable(True)
        self.boton_conectar.setToolTip(
            "Barra de Herramientas: Modo Conectar Transición.\n"
            "Haz clic en el estado de origen y luego en el de destino para trazar una flecha y elegir sus caracteres."
        )
        self.boton_conectar.clicked.connect(lambda: self.modo_cambiado.emit("conectar"))
        self.grupo_botones.addButton(self.boton_conectar)
        layout.addWidget(self.boton_conectar)

        self.boton_borrar = QPushButton("🗑️ Borrar")
        self.boton_borrar.setCheckable(True)
        self.boton_borrar.setToolTip(
            "Barra de Herramientas: Modo Borrar (Supr).\nHaz clic en cualquier estado o flecha para eliminarlo."
        )
        self.boton_borrar.clicked.connect(lambda: self.modo_cambiado.emit("borrar"))
        self.grupo_botones.addButton(self.boton_borrar)
        layout.addWidget(self.boton_borrar)

        layout.addSpacing(6)

        # Botones de Historial: Deshacer (Ctrl+Z) y Rehacer (Ctrl+Y)
        self.boton_deshacer = QPushButton("↶ Deshacer")
        self.boton_deshacer.setToolTip("Deshacer última acción (Ctrl+Z).\nPermite revertir creaciones, eliminaciones o conversiones.")
        self.boton_deshacer.setEnabled(False)
        self.boton_deshacer.clicked.connect(self.deshacer_solicitado.emit)
        layout.addWidget(self.boton_deshacer)

        self.boton_rehacer = QPushButton("↷ Rehacer")
        self.boton_rehacer.setToolTip("Rehacer acción deshecha (Ctrl+Y / Ctrl+Shift+Z).")
        self.boton_rehacer.setEnabled(False)
        self.boton_rehacer.clicked.connect(self.rehacer_solicitado.emit)
        layout.addWidget(self.boton_rehacer)

        layout.addSpacing(8)

        # Controles de Zoom (In / Out / 100%)
        etiqueta_zoom = QLabel("Zoom:")
        etiqueta_zoom.setStyleSheet("font-weight: bold; color: #64748b; font-size: 11px;")
        layout.addWidget(etiqueta_zoom)

        self.boton_zoom_acercar = QPushButton("🔍+ Acercar")
        self.boton_zoom_acercar.setToolTip(
            "Barra de Herramientas: Acercar zoom (+).\nO use la rueda del ratón hacia arriba sobre la pizarra."
        )
        self.boton_zoom_acercar.clicked.connect(self.zoom_acercar_solicitado.emit)
        layout.addWidget(self.boton_zoom_acercar)

        self.boton_zoom_alejar = QPushButton("🔍- Alejar")
        self.boton_zoom_alejar.setToolTip(
            "Barra de Herramientas: Alejar zoom (-).\nO use la rueda del ratón hacia abajo sobre la pizarra."
        )
        self.boton_zoom_alejar.clicked.connect(self.zoom_alejar_solicitado.emit)
        layout.addWidget(self.boton_zoom_alejar)

        self.boton_zoom_restablecer = QPushButton("⟲ 100%")
        self.boton_zoom_restablecer.setToolTip("Barra de Herramientas: Restablecer zoom al 100% (escala normal 1:1).")
        self.boton_zoom_restablecer.clicked.connect(self.zoom_restablecer_solicitado.emit)
        layout.addWidget(self.boton_zoom_restablecer)

        layout.addSpacing(8)

        self.boton_auto_organizar = QPushButton("🔄 Auto-distribuir")
        self.boton_auto_organizar.setToolTip(
            "Barra de Herramientas: Auto-distribuir.\n"
            "Ordena automáticamente todos los estados en un círculo geométrico armónico."
        )
        self.boton_auto_organizar.clicked.connect(self.auto_organizar_solicitado.emit)
        layout.addWidget(self.boton_auto_organizar)

        self.boton_limpiar = QPushButton("🧹 Limpiar Grafo")
        self.boton_limpiar.setStyleSheet(
            "QPushButton { background-color: #fef2f2; border-color: #fca5a5; color: #b91c1c; }"
            "QPushButton:hover { background-color: #fee2e2; border-color: #f87171; }"
        )
        self.boton_limpiar.setToolTip(
            "Barra de Herramientas: Limpiar Grafo e Historial.\n"
            "Elimina todos los nodos, flechas, tabla de transiciones y simulación activa."
        )
        self.boton_limpiar.clicked.connect(self.limpiar_solicitado.emit)
        layout.addWidget(self.boton_limpiar)

        layout.addSpacing(8)

        # Botón de Conversión de AFN a AFD (Construcción de Subconjuntos)
        self.boton_convertir_dfa = QPushButton("⚡ Convertir AFN a AFD")
        self.boton_convertir_dfa.setStyleSheet(
            "QPushButton { background-color: #f5f3ff; border: 1.5px solid #c4b5fd; color: #6d28d9; font-weight: bold; }"
            "QPushButton:hover { background-color: #ede9fe; border-color: #8b5cf6; }"
        )
        self.boton_convertir_dfa.setToolTip(
            "Barra de Herramientas: Conversión de AFN a AFD (Construcción de Subconjuntos).\n"
            "Convierte el autómata no determinista a determinista mostrando la tabla de proceso paso a paso."
        )
        self.boton_convertir_dfa.clicked.connect(self.conversion_dfa_solicitada.emit)
        layout.addWidget(self.boton_convertir_dfa)

        layout.addSpacing(8)

        self.boton_ayuda = QPushButton("📖 ¿Cómo usar el programa?")
        self.boton_ayuda.setStyleSheet(
            "QPushButton { background-color: #eff6ff; border-color: #93c5fd; color: #1d4ed8; font-weight: bold; }"
            "QPushButton:hover { background-color: #dbeafe; border-color: #60a5fa; }"
        )
        self.boton_ayuda.setToolTip(
            "Barra de Herramientas: Ayuda.\nAbre la guía de uso interactiva con explicaciones detalladas."
        )
        self.boton_ayuda.clicked.connect(self.ayuda_solicitada.emit)
        layout.addWidget(self.boton_ayuda)

        layout.addStretch(1)

        # Indicador de atajos
        etiqueta_atajos = QLabel("Atajos: Supr (Borrar) | Esc (Cursor) | Rueda (Zoom)")
        etiqueta_atajos.setStyleSheet("color: #64748b; font-size: 11px; font-weight: 500;")
        layout.addWidget(etiqueta_atajos)

    def activar_modo_seleccion(self) -> None:
        """Fuerza la activación del botón de modo selección."""
        self.boton_seleccionar.setChecked(True)
        self.modo_cambiado.emit("seleccion")

    def actualizar_estado_no_deterministico(self, es_nfa: bool) -> None:
        """Actualiza el aspecto visual del botón de conversión según si el autómata es AFN."""
        if es_nfa:
            self.boton_convertir_dfa.setText("⚡ Convertir AFN a AFD")
            self.boton_convertir_dfa.setStyleSheet(
                "QPushButton { background-color: #7c3aed; border: 1.5px solid #6d28d9; color: #ffffff; "
                "font-weight: bold; padding: 6px 14px; border-radius: 6px; font-size: 12px; }"
                "QPushButton:hover { background-color: #6d28d9; }"
                "QPushButton:pressed { background-color: #5b21b6; }"
            )
            self.boton_convertir_dfa.setToolTip(
                "¡Autómata No Determinista detectado!\n"
                "Haz clic para convertir a AFD determinista y ver la tabla de proceso de subconjuntos."
            )
        else:
            self.boton_convertir_dfa.setText("⚡ Convertir a DFA")
            self.boton_convertir_dfa.setStyleSheet(
                "QPushButton { background-color: #f8fafc; border: 1px solid #cbd5e1; color: #94a3b8; font-weight: 500; }"
                "QPushButton:hover { background-color: #f1f5f9; color: #64748b; }"
            )
            self.boton_convertir_dfa.setToolTip(
                "El autómata actual es Determinista (AFD). Si agrega transiciones múltiples se activará la conversión."
            )

    def actualizar_estado_historial(self, puede_deshacer: bool, puede_rehacer: bool) -> None:
        """Habilita o deshabilita los botones de deshacer y rehacer según el historial."""
        self.boton_deshacer.setEnabled(puede_deshacer)
        self.boton_rehacer.setEnabled(puede_rehacer)

