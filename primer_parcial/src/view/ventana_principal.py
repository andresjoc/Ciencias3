"""Ventana principal de la aplicación en PyQt6 con Editor de Grafos y Simulador."""

from __future__ import annotations

from PyQt6.QtCore import Qt
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

    def __init__(self) -> None:
        super().__init__()
        self._inicializar_ui()

    def _inicializar_ui(self) -> None:
        """Inicializa la interfaz gráfica, título, dimensiones y componentes."""
        self.setWindowTitle("SimulaAutomata — Editor Visual y Simulador de Autómatas (DFA / NFA)")
        self.resize(1280, 840)
        self.setMinimumSize(960, 640)

        widget_central = QWidget(self)
        layout_central = QVBoxLayout(widget_central)
        layout_central.setContentsMargins(14, 12, 14, 12)
        layout_central.setSpacing(10)

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
        caja_grafo = QGroupBox("🎨 Editor Visual de Grafo (Arrastrar estados y conectar flechas)")
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
        self.barra_herramientas_grafo.auto_organizar_solicitado.connect(self.lienzo_grafo.auto_organizar_nodos)
        self.barra_herramientas_grafo.limpiar_solicitado.connect(self.lienzo_grafo.limpiar_grafo)
        self.barra_herramientas_grafo.ayuda_solicitada.connect(
            lambda: self.pestanas_derecha.setCurrentWidget(self.panel_guia_uso)
        )
        self.lienzo_grafo.mensaje_solicitado.connect(self.mostrar_mensaje_estado)

        # --- Panel Derecho: Pestañas con Guía, Simulación de Cinta y Matriz de Transiciones ---
        self.pestanas_derecha = QTabWidget()

        # Pestaña 1: Panel de Simulación y Visualizador de Cinta y Traza
        self.panel_simulacion = PanelSimulacion(self)
        self.pestanas_derecha.addTab(self.panel_simulacion, "📼 Simulador de Cinta y Traza")

        # Pestaña 2: Tabla Matricial de Transiciones
        self.tabla_transiciones = TablaTransiciones(self)
        self.pestanas_derecha.addTab(self.tabla_transiciones, "📋 Matriz de Transiciones")

        # Pestaña 3: Guía Rápida de Uso e Instrucciones
        self.panel_guia_uso = PanelGuiaUso(self)
        self.pestanas_derecha.addTab(self.panel_guia_uso, "📖 Guía de Uso")

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

    def mostrar_mensaje_estado(self, mensaje: str, duracion_ms: int = 0) -> None:
        """Muestra un mensaje en la barra de estado de la ventana."""
        self.barra_estado.showMessage(mensaje, duracion_ms)
