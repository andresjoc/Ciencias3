"""Barra de herramientas flotante o integrada para el editor de grafos estilo Draw.io."""

from __future__ import annotations
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
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
            "QFrame { background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 3px; }"
            "QPushButton { background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px; "
            "padding: 4px 8px; font-weight: 600; font-size: 11px; color: #334155; }"
            "QPushButton:hover { background-color: #f1f5f9; border-color: #94a3b8; }"
            "QPushButton:checked { background-color: #d1fae5; border-color: #059669; color: #065f46; font-weight: 700; }"
        )
        self._inicializar_ui()

    def _inicializar_ui(self) -> None:
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(6, 4, 6, 4)
        layout_principal.setSpacing(4)

        # Fila 1: Herramientas de Edición, Navegación, Historial y Zoom
        layout_fila1 = QHBoxLayout()
        layout_fila1.setSpacing(6)

        etiqueta_herramientas = QLabel("Edición:")
        etiqueta_herramientas.setStyleSheet("font-weight: bold; color: #64748b; font-size: 11px;")
        layout_fila1.addWidget(etiqueta_herramientas)

        self.grupo_botones = QButtonGroup(self)
        self.grupo_botones.setExclusive(True)

        self.boton_seleccionar = QPushButton("🖱️ Cursor")
        self.boton_seleccionar.setCheckable(True)
        self.boton_seleccionar.setChecked(True)
        self.boton_seleccionar.setToolTip(
            "Barra de Herramientas: Modo Cursor / Selección (Esc).\n"
            "Arrastra estados, selecciona elementos o haz clic sobre una conexión para editar caracteres."
        )
        self.boton_seleccionar.clicked.connect(lambda: self.modo_cambiado.emit("seleccion"))
        self.grupo_botones.addButton(self.boton_seleccionar)
        layout_fila1.addWidget(self.boton_seleccionar)

        self.boton_desplazar = QPushButton("✋ Desplazar")
        self.boton_desplazar.setCheckable(True)
        self.boton_desplazar.setToolTip(
            "Barra de Herramientas: Modo Mano / Desplazar Vista.\n"
            "Mantenga el clic izquierdo presionado y arrastre para mover la vista de la pizarra en cualquier dirección."
        )
        self.boton_desplazar.clicked.connect(lambda: self.modo_cambiado.emit("desplazar"))
        self.grupo_botones.addButton(self.boton_desplazar)
        layout_fila1.addWidget(self.boton_desplazar)

        self.boton_crear_estado = QPushButton("➕ Estado")
        self.boton_crear_estado.setCheckable(True)
        self.boton_crear_estado.setToolTip(
            "Barra de Herramientas: Modo Crear Estado.\nHaz clic sobre la pizarra para plantar un nuevo nodo."
        )
        self.boton_crear_estado.clicked.connect(lambda: self.modo_cambiado.emit("crear_estado"))
        self.grupo_botones.addButton(self.boton_crear_estado)
        layout_fila1.addWidget(self.boton_crear_estado)

        self.boton_conectar = QPushButton("➔ Conectar")
        self.boton_conectar.setCheckable(True)
        self.boton_conectar.setToolTip(
            "Barra de Herramientas: Modo Conectar Transición.\n"
            "Haz clic en el estado de origen y luego en el de destino para trazar una flecha y elegir sus caracteres."
        )
        self.boton_conectar.clicked.connect(lambda: self.modo_cambiado.emit("conectar"))
        self.grupo_botones.addButton(self.boton_conectar)
        layout_fila1.addWidget(self.boton_conectar)

        self.boton_borrar = QPushButton("🗑️ Borrar")
        self.boton_borrar.setCheckable(True)
        self.boton_borrar.setToolTip(
            "Barra de Herramientas: Modo Borrar (Supr).\nHaz clic en cualquier estado o flecha para eliminarlo."
        )
        self.boton_borrar.clicked.connect(lambda: self.modo_cambiado.emit("borrar"))
        self.grupo_botones.addButton(self.boton_borrar)
        layout_fila1.addWidget(self.boton_borrar)

        layout_fila1.addSpacing(6)

        # Botones de Historial: Deshacer (Ctrl+Z) y Rehacer (Ctrl+Y)
        self.boton_deshacer = QPushButton("↶ Deshacer")
        self.boton_deshacer.setToolTip("Deshacer última acción (Ctrl+Z).\nPermite revertir creaciones, eliminaciones o conversiones.")
        self.boton_deshacer.setEnabled(False)
        self.boton_deshacer.clicked.connect(self.deshacer_solicitado.emit)
        layout_fila1.addWidget(self.boton_deshacer)

        self.boton_rehacer = QPushButton("↷ Rehacer")
        self.boton_rehacer.setToolTip("Rehacer acción deshecha (Ctrl+Y / Ctrl+Shift+Z).")
        self.boton_rehacer.setEnabled(False)
        self.boton_rehacer.clicked.connect(self.rehacer_solicitado.emit)
        layout_fila1.addWidget(self.boton_rehacer)

        layout_fila1.addSpacing(6)

        # Controles de Zoom (In / Out / 100%)
        etiqueta_zoom = QLabel("Zoom:")
        etiqueta_zoom.setStyleSheet("font-weight: bold; color: #64748b; font-size: 11px;")
        layout_fila1.addWidget(etiqueta_zoom)

        self.boton_zoom_acercar = QPushButton("＋ Zoom")
        self.boton_zoom_acercar.setToolTip(
            "Barra de Herramientas: Acercar zoom (+).\nO use la rueda del ratón hacia arriba sobre la pizarra."
        )
        self.boton_zoom_acercar.clicked.connect(self.zoom_acercar_solicitado.emit)
        layout_fila1.addWidget(self.boton_zoom_acercar)

        self.boton_zoom_alejar = QPushButton("－ Zoom")
        self.boton_zoom_alejar.setToolTip(
            "Barra de Herramientas: Alejar zoom (-).\nO use la rueda del ratón hacia abajo sobre la pizarra."
        )
        self.boton_zoom_alejar.clicked.connect(self.zoom_alejar_solicitado.emit)
        layout_fila1.addWidget(self.boton_zoom_alejar)

        self.boton_zoom_restablecer = QPushButton("⟲ 100%")
        self.boton_zoom_restablecer.setToolTip("Barra de Herramientas: Restablecer zoom al 100% (escala normal 1:1).")
        self.boton_zoom_restablecer.clicked.connect(self.zoom_restablecer_solicitado.emit)
        layout_fila1.addWidget(self.boton_zoom_restablecer)

        layout_fila1.addStretch(1)

        # Indicador de atajos
        etiqueta_atajos = QLabel("Atajos: Supr (Borrar) | Esc (Cursor) | Rueda (Zoom)")
        etiqueta_atajos.setStyleSheet("color: #64748b; font-size: 11px; font-weight: 500;")
        layout_fila1.addWidget(etiqueta_atajos)

        layout_principal.addLayout(layout_fila1)

        # Fila 2: Acciones Globales, Conversión y Ayuda
        layout_fila2 = QHBoxLayout()
        layout_fila2.setSpacing(6)

        etiqueta_acciones = QLabel("Acciones:")
        etiqueta_acciones.setStyleSheet("font-weight: bold; color: #64748b; font-size: 11px;")
        layout_fila2.addWidget(etiqueta_acciones)

        self.boton_auto_organizar = QPushButton("⟳ Auto-distribuir")
        self.boton_auto_organizar.setToolTip(
            "Barra de Herramientas: Auto-distribuir.\n"
            "Ordena automáticamente todos los estados en un círculo geométrico armónico."
        )
        self.boton_auto_organizar.clicked.connect(self.auto_organizar_solicitado.emit)
        layout_fila2.addWidget(self.boton_auto_organizar)

        self.boton_limpiar = QPushButton("🧹 Limpiar Grafo")
        self.boton_limpiar.setStyleSheet(
            "QPushButton { background-color: #fef2f2; border-color: #fca5a5; color: #b91c1c; font-weight: 600; padding: 4px 10px; font-size: 11px; border-radius: 6px; }"
            "QPushButton:hover { background-color: #fee2e2; border-color: #f87171; }"
        )
        self.boton_limpiar.setToolTip(
            "Barra de Herramientas: Limpiar Grafo e Historial.\n"
            "Elimina todos los nodos, flechas, tabla de transiciones y simulación activa."
        )
        self.boton_limpiar.clicked.connect(self.limpiar_solicitado.emit)
        layout_fila2.addWidget(self.boton_limpiar)

        layout_fila2.addSpacing(6)

        # Botón de Conversión de AFN a AFD
        self.boton_convertir_dfa = QPushButton("⚡ Convertir AFN a AFD")
        self.boton_convertir_dfa.setStyleSheet(
            "QPushButton { background-color: #fef3c7; border: 1.5px solid #fde047; color: #b45309; font-weight: bold; padding: 4px 12px; font-size: 11px; border-radius: 6px; }"
            "QPushButton:hover { background-color: #fde68a; border-color: #f59e0b; }"
        )
        self.boton_convertir_dfa.setToolTip(
            "Barra de Herramientas: Conversión de AFN a AFD.\n"
            "Convierte el autómata no determinista a determinista mostrando la tabla de proceso paso a paso."
        )
        self.boton_convertir_dfa.clicked.connect(self.conversion_dfa_solicitada.emit)
        layout_fila2.addWidget(self.boton_convertir_dfa)

        layout_fila2.addSpacing(6)

        self.boton_ayuda = QPushButton("💡 ¿Cómo usar el programa?")
        self.boton_ayuda.setStyleSheet(
            "QPushButton { background-color: #ecfdf5; border: 1.5px solid #a7f3d0; color: #047857; font-weight: bold; padding: 4px 12px; font-size: 11px; border-radius: 6px; }"
            "QPushButton:hover { background-color: #d1fae5; border-color: #6ee7b7; }"
        )
        self.boton_ayuda.setToolTip(
            "Barra de Herramientas: Ayuda.\nAbre la guía de uso interactiva con explicaciones detalladas."
        )
        self.boton_ayuda.clicked.connect(self.ayuda_solicitada.emit)
        layout_fila2.addWidget(self.boton_ayuda)

        layout_fila2.addStretch(1)

        layout_principal.addLayout(layout_fila2)

    def activar_modo_seleccion(self) -> None:
        """Fuerza la activación del botón de modo selección."""
        self.boton_seleccionar.setChecked(True)
        self.modo_cambiado.emit("seleccion")

    def actualizar_estado_no_deterministico(self, es_nfa: bool) -> None:
        """Actualiza el aspecto visual y el bloqueo del botón de conversión según si el autómata es AFN."""
        self.boton_convertir_dfa.setEnabled(es_nfa)
        if es_nfa:
            self.boton_convertir_dfa.setText("⚡ Convertir AFN a AFD")
            self.boton_convertir_dfa.setStyleSheet(
                "QPushButton { background-color: #d97706; border: 1.5px solid #b45309; color: #ffffff; "
                "font-weight: bold; padding: 4px 12px; border-radius: 6px; font-size: 11px; }"
                "QPushButton:hover { background-color: #b45309; }"
                "QPushButton:pressed { background-color: #92400e; }"
            )
            self.boton_convertir_dfa.setToolTip(
                "¡Autómata No Determinista detectado!\n"
                "Haz clic para convertir a AFD determinista y ver el proceso paso a paso."
            )
        else:
            self.boton_convertir_dfa.setText("⚡ Convertir a AFD")
            self.boton_convertir_dfa.setStyleSheet(
                "QPushButton { background-color: #f1f5f9; border: 1px solid #cbd5e1; color: #94a3b8; "
                "font-weight: 500; padding: 4px 12px; border-radius: 6px; font-size: 11px; }"
            )
            self.boton_convertir_dfa.setToolTip(
                "El autómata actual es Determinista (AFD). La conversión solo se habilita cuando existan conexiones no deterministas (AFN)."
            )

    def actualizar_estado_historial(self, puede_deshacer: bool, puede_rehacer: bool) -> None:
        """Habilita o deshabilita los botones de deshacer y rehacer según el historial."""
        self.boton_deshacer.setEnabled(puede_deshacer)
        self.boton_rehacer.setEnabled(puede_rehacer)

