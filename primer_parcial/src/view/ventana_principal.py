"""Ventana principal de la aplicación en PyQt6 con Editor de Grafos y Simulador."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QMainWindow,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.view.barra_herramientas_grafo import BarraHerramientasGrafo
from src.view.lienzo_grafo import LienzoGrafo
from src.view.panel_alfabeto import PanelAlfabeto
from src.view.panel_guia_uso import PanelGuiaUso
from src.view.panel_paso_a_paso_conversion import PanelPasoAPasoConversion
from src.view.panel_simulacion import PanelSimulacion
from src.view.tabla_transiciones import TablaTransiciones


class VentanaPrincipal(QMainWindow):
    """Ventana principal del simulador y editor visual de autómatas finitos (DFA / NFA).

    Organiza:
    - Barra superior: Configuración de Alfabeto Sigma + Barra de Herramientas del Grafo.
    - Área central dividida (Splitter horizontal):
      * Panel Izquierdo: Editor visual e interactivo de grafos estilo Draw.io (LienzoGrafo).
      * Panel Derecho (Pestañas):
        - Pestaña 1: Simulador de Cinta y Traza paso a paso (PanelSimulacion).
        - Pestaña 2: Matriz editable de Transiciones (TablaTransiciones).
    """

    deshacer_solicitado = pyqtSignal()
    rehacer_solicitado = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self._inicializar_ui()

    def _inicializar_ui(self) -> None:
        """Inicializa la interfaz gráfica, título, dimensiones y componentes."""
        self.setWindowTitle("SimulaAutomata — Editor Visual y Simulador de Autómatas (DFA / NFA)")
        self.resize(1240, 700)
        self.setMinimumSize(900, 580)

        widget_central = QWidget(self)
        layout_central = QVBoxLayout(widget_central)
        layout_central.setContentsMargins(10, 8, 10, 8)
        layout_central.setSpacing(6)

        # 1. Zona Superior: Panel del Alfabeto
        self.panel_alfabeto = PanelAlfabeto(self)
        layout_central.addWidget(self.panel_alfabeto)

        # 2. Barra de Herramientas interactiva del Grafo
        self.barra_herramientas_grafo = BarraHerramientasGrafo(self)
        layout_central.addWidget(self.barra_herramientas_grafo)

        # 3. Contenedor dividido central (QSplitter)
        divisor_central = QSplitter(Qt.Orientation.Horizontal)
        divisor_central.setHandleWidth(6)
        divisor_central.setStyleSheet(
            "QSplitter::handle { background-color: #e2e8f0; border-radius: 3px; }"
            "QSplitter::handle:hover { background-color: #94a3b8; }"
        )

        # --- Panel Izquierdo: Editor de Grafo estilo Draw.io ---
        caja_grafo = QGroupBox("✎ Editor Visual de Grafo (Arrastrar estados y conectar flechas)")
        caja_grafo.setStyleSheet(
            "QGroupBox { font-weight: bold; color: #1e293b; border: 1px solid #cbd5e1; "
            "border-radius: 8px; margin-top: 8px; padding-top: 10px; background-color: #ffffff; }"
            "QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 4px; }"
        )
        layout_grafo = QVBoxLayout(caja_grafo)
        layout_grafo.setContentsMargins(8, 8, 8, 8)

        self.lienzo_grafo = LienzoGrafo(caja_grafo)
        layout_grafo.addWidget(self.lienzo_grafo)
        divisor_central.addWidget(caja_grafo)

        # Conectar barra de herramientas con el lienzo del grafo
        self.barra_herramientas_grafo.modo_cambiado.connect(self.lienzo_grafo.establecer_modo)
        self.barra_herramientas_grafo.limpiar_solicitado.connect(self.lienzo_grafo.limpiar_grafo)
        self.barra_herramientas_grafo.zoom_acercar_solicitado.connect(self.lienzo_grafo.zoom_acercar)
        self.barra_herramientas_grafo.zoom_alejar_solicitado.connect(self.lienzo_grafo.zoom_alejar)
        self.barra_herramientas_grafo.zoom_restablecer_solicitado.connect(self.lienzo_grafo.zoom_restablecer)
        self.barra_herramientas_grafo.ayuda_solicitada.connect(
            lambda: self.pestanas_derecha.setCurrentWidget(self.panel_guia_uso)
        )
        self.barra_herramientas_grafo.deshacer_solicitado.connect(self.deshacer_solicitado.emit)
        self.barra_herramientas_grafo.rehacer_solicitado.connect(self.rehacer_solicitado.emit)
        self.lienzo_grafo.mensaje_solicitado.connect(self.mostrar_mensaje_estado)

        # Atajos de teclado globales para Deshacer (Ctrl+Z) y Rehacer (Ctrl+Y / Ctrl+Shift+Z)
        self._atajo_deshacer = QShortcut(QKeySequence.StandardKey.Undo, self)
        self._atajo_deshacer.activated.connect(self.deshacer_solicitado.emit)

        self._atajo_rehacer = QShortcut(QKeySequence.StandardKey.Redo, self)
        self._atajo_rehacer.activated.connect(self.rehacer_solicitado.emit)

        self._atajo_rehacer_alt = QShortcut(QKeySequence("Ctrl+Shift+Z"), self)
        self._atajo_rehacer_alt.activated.connect(self.rehacer_solicitado.emit)

        # --- Panel Derecho: Pestañas con Guía, Simulación de Cinta y Matriz de Transiciones ---
        self.pestanas_derecha = QTabWidget()

        # Pestaña 1: Panel de Simulación y Visualizador de Cinta y Traza
        self.panel_simulacion = PanelSimulacion(self)
        self.pestanas_derecha.addTab(self.panel_simulacion, "📼 Simulador de Cinta y Traza")

        # Pestaña 2: Tabla Matricial de Transiciones
        self.tabla_transiciones = TablaTransiciones(self)
        self.pestanas_derecha.addTab(self.tabla_transiciones, "📋 Matriz de Transiciones")

        # Pestaña 3: Proceso de Conversión Paso a Paso (AFN → AFD) - Al lado de la matriz
        self.panel_paso_a_paso = PanelPasoAPasoConversion(self)
        self.pestanas_derecha.addTab(self.panel_paso_a_paso, "📐 Paso a Paso (AFN → AFD)")
        self.pestanas_derecha.setTabVisible(2, False)  # Oculta inicialmente hasta que haya conversión
        self.tabla_transiciones.ver_paso_a_paso_solicitado.connect(self.activar_pestana_paso_a_paso)

        # Pestaña 4: Guía Rápida de Uso e Instrucciones
        self.panel_guia_uso = PanelGuiaUso(self)
        self.pestanas_derecha.addTab(self.panel_guia_uso, "💡 Guía de Uso")

        divisor_central.addWidget(self.pestanas_derecha)

        # Proporción inicial: 55% para el lienzo del grafo, 45% para pestañas derecha
        divisor_central.setSizes([680, 560])

        layout_central.addWidget(divisor_central, stretch=1)
        self.setCentralWidget(widget_central)

        # Barra de estado inferior
        self.barra_estado = QStatusBar()
        self.setStatusBar(self.barra_estado)
        self.mostrar_mensaje_estado(
            "Listo. Puede dibujar estados y transiciones en el lienzo o ingresar el alfabeto."
        )

    def mostrar_paso_a_paso_conversion(self, resultado) -> None:
        """Muestra la pestaña y activa el botón de ver paso a paso con el resultado cargado."""
        self.panel_paso_a_paso.cargar_resultado(resultado)
        idx = self.pestanas_derecha.indexOf(self.panel_paso_a_paso)
        if idx != -1:
            self.pestanas_derecha.setTabVisible(idx, True)
        self.tabla_transiciones.boton_ver_paso_a_paso.setVisible(True)

    def ocultar_paso_a_paso_conversion(self) -> None:
        """Oculta la pestaña y el botón de paso a paso (ej. al deshacer la conversión)."""
        idx = self.pestanas_derecha.indexOf(self.panel_paso_a_paso)
        if idx != -1:
            self.pestanas_derecha.setTabVisible(idx, False)
        self.tabla_transiciones.boton_ver_paso_a_paso.setVisible(False)
        self.panel_paso_a_paso.limpiar()

    def activar_pestana_paso_a_paso(self) -> None:
        """Cambia el foco del panel derecho hacia la pestaña del paso a paso."""
        idx = self.pestanas_derecha.indexOf(self.panel_paso_a_paso)
        if idx != -1:
            self.pestanas_derecha.setTabVisible(idx, True)
            self.pestanas_derecha.setCurrentWidget(self.panel_paso_a_paso)

    def mostrar_mensaje_estado(self, mensaje: str, duracion_ms: int = 0) -> None:
        """Muestra un mensaje en la barra de estado de la ventana."""
        self.barra_estado.showMessage(mensaje, duracion_ms)
