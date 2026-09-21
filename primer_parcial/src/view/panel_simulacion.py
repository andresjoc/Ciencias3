"""Panel de control y visualización de la simulación paso a paso de la traza."""

from __future__ import annotations
from typing import Optional, Union

from PyQt6.QtCore import QRegularExpression, pyqtSignal
from PyQt6.QtGui import QRegularExpressionValidator
from PyQt6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.model.automata import ResultadoTraza
from src.model.automata_nfa import ResultadoTrazaNFA
from src.view.lienzo_cinta import LienzoCinta


class PanelSimulacion(QGroupBox):
    """Panel contenedor de la simulación DFA paso a paso y el lienzo gráfico.

    Señales:
        evaluacion_solicitada (str): Emite la cadena de entrada u a simular.
        avanzar_paso_solicitado (): Solicita avanzar al siguiente paso.
        retroceder_paso_solicitado (): Solicita retroceder al paso previo.
        ejecutar_todo_solicitado (): Solicita ir directamente al paso final.
        reiniciar_simulacion_solicitado (): Reinicia la simulación actual al inicio.
    """

    evaluacion_solicitada = pyqtSignal(str)
    avanzar_paso_solicitado = pyqtSignal()
    retroceder_paso_solicitado = pyqtSignal()
    ejecutar_todo_solicitado = pyqtSignal()
    reiniciar_simulacion_solicitado = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Simulación: Cinta y Traza de Ejecución (DFA)", parent)
        self._inicializar_ui()

    def _inicializar_ui(self) -> None:
        """Construye los controles de entrada de cadena, botones y el lienzo gráfico."""
        layout_principal = QVBoxLayout()
        layout_principal.setSpacing(10)

        # Fila 1: Entrada de cadena u y botón de inicio
        layout_entrada = QHBoxLayout()
        etiqueta_entrada = QLabel("Cadena (u):")
        layout_entrada.addWidget(etiqueta_entrada)

        self.campo_cadena = QLineEdit()
        self.campo_cadena.setPlaceholderText("Sección Cinta: Ingrese la palabra u a evaluar (ej. 0101 o ab)")
        self.campo_cadena.setToolTip("Sección Simulador: Palabra u a simular en la cinta formal paso a paso.")
        self.campo_cadena.setValidator(QRegularExpressionValidator(QRegularExpression(r"[a-zA-Z0-9]*"), self))
        self.campo_cadena.returnPressed.connect(self._al_iniciar)
        layout_entrada.addWidget(self.campo_cadena)

        self.boton_iniciar = QPushButton("Iniciar")
        self.boton_iniciar.setStyleSheet("font-weight: 600; padding: 5px 10px; font-size: 11px;")
        self.boton_iniciar.setToolTip("Cargar la palabra u en la cinta y preparar la traza de ejecución.")
        self.boton_iniciar.clicked.connect(self._al_iniciar)
        layout_entrada.addWidget(self.boton_iniciar)

        layout_principal.addLayout(layout_entrada)

        # Fila 2: Botones de control paso a paso y ejecución completa
        layout_controles = QHBoxLayout()
        layout_controles.setSpacing(6)

        estilo_controles = "QPushButton { padding: 5px 8px; font-size: 11px; font-weight: 600; }"

        self.boton_anterior = QPushButton("◀ Anterior")
        self.boton_anterior.setStyleSheet(estilo_controles)
        self.boton_anterior.setToolTip("Retroceder un paso en la lectura de la cinta y volver al estado previo.")
        self.boton_anterior.clicked.connect(self.retroceder_paso_solicitado.emit)
        self.boton_anterior.setEnabled(False)
        layout_controles.addWidget(self.boton_anterior)

        self.boton_siguiente = QPushButton("Siguiente ▶")
        self.boton_siguiente.setStyleSheet(estilo_controles)
        self.boton_siguiente.setToolTip("Avanzar un paso: leer el símbolo actual y transicionar al siguiente estado.")
        self.boton_siguiente.clicked.connect(self.avanzar_paso_solicitado.emit)
        self.boton_siguiente.setEnabled(False)
        layout_controles.addWidget(self.boton_siguiente)

        self.boton_ejecutar_todo = QPushButton("Ejecutar Todo ⏭")
        self.boton_ejecutar_todo.setStyleSheet(estilo_controles)
        self.boton_ejecutar_todo.setToolTip("Recorrer toda la cinta automáticamente paso a paso con animación temporizada.")
        self.boton_ejecutar_todo.clicked.connect(self.ejecutar_todo_solicitado.emit)
        self.boton_ejecutar_todo.setEnabled(False)
        layout_controles.addWidget(self.boton_ejecutar_todo)

        self.boton_reiniciar = QPushButton("Reiniciar ↺")
        self.boton_reiniciar.setStyleSheet(estilo_controles)
        self.boton_reiniciar.setToolTip("Regresar la cinta y el cabezal lector al estado inicial q₀.")
        self.boton_reiniciar.clicked.connect(self.reiniciar_simulacion_solicitado.emit)
        self.boton_reiniciar.setEnabled(False)
        layout_controles.addWidget(self.boton_reiniciar)

        layout_principal.addLayout(layout_controles)

        # Fila 3: Indicador de estado y detalles de ejecución
        layout_estado = QHBoxLayout()
        self.insignia_estado = QLabel("ESTADO: Esperando cadena")
        self.insignia_estado.setStyleSheet(
            "background-color: #f1f5f9; color: #475569; padding: 4px 10px; "
            "border-radius: 6px; font-weight: bold; font-size: 12px;"
        )
        layout_estado.addWidget(self.insignia_estado)

        self.etiqueta_detalle_paso = QLabel("")
        self.etiqueta_detalle_paso.setStyleSheet("color: #334155; font-size: 12px;")
        layout_estado.addWidget(self.etiqueta_detalle_paso, stretch=1)

        layout_principal.addLayout(layout_estado)

        # Fila 4: Lienzo gráfico de Cinta y Control
        self.lienzo = LienzoCinta(self)
        self.lienzo.setToolTip("Visualizador gráfico: Muestra las celdas de la cinta, el cabezal lector y la unidad de control.")
        layout_principal.addWidget(self.lienzo, stretch=1)

        self.setLayout(layout_principal)

    def _al_iniciar(self) -> None:
        """Emite la solicitud para comenzar la simulación de la cadena ingresada."""
        cadena = self.campo_cadena.text().strip()
        self.evaluacion_solicitada.emit(cadena)

    def actualizar_estado(
        self,
        traza: Optional[Union[ResultadoTraza, ResultadoTrazaNFA]],
        paso_actual: int,
        total_pasos: int,
    ) -> None:
        """Actualiza las insignias de estado, etiquetas informativas y el lienzo.

        Args:
            traza: Resultado de la traza de ejecución (DFA o NFA).
            paso_actual: Índice del paso activo (0-indexado).
            total_pasos: Cantidad total de pasos de la traza.
        """
        if traza is None or total_pasos == 0:
            self.insignia_estado.setText("ESTADO: Esperando cadena")
            self.insignia_estado.setStyleSheet(
                "background-color: #f1f5f9; color: #475569; padding: 4px 10px; "
                "border-radius: 6px; font-weight: bold;"
            )
            self.etiqueta_detalle_paso.setText("")
            self.boton_anterior.setEnabled(False)
            self.boton_siguiente.setEnabled(False)
            self.boton_ejecutar_todo.setEnabled(False)
            self.boton_reiniciar.setEnabled(False)
            self.lienzo.establecer_traza(None)
            return

        es_ultimo_paso = (paso_actual >= total_pasos - 1)
        puede_retroceder = (paso_actual > 0)
        puede_avanzar = (paso_actual < total_pasos - 1)

        self.boton_anterior.setEnabled(puede_retroceder)
        self.boton_siguiente.setEnabled(puede_avanzar)
        self.boton_ejecutar_todo.setEnabled(puede_avanzar)
        self.boton_reiniciar.setEnabled(True)

        if isinstance(traza, ResultadoTrazaNFA):
            if es_ultimo_paso:
                if traza.aceptada:
                    self.insignia_estado.setText("✓ ACEPTADA (NFA)")
                    self.insignia_estado.setStyleSheet(
                        "background-color: #dcfce7; color: #15803d; padding: 4px 12px; "
                        "border-radius: 6px; font-weight: bold; font-size: 13px;"
                    )
                    self.etiqueta_detalle_paso.setText(
                        f"Fin de cinta (≡). Ramas totales: {len(traza.ramas)} | "
                        f"Aceptadas: {len(traza.ramas_aceptadas)} | "
                        f"Abortadas (∅): {len(traza.ramas_abortadas)}"
                    )
                else:
                    self.insignia_estado.setText("✗ RECHAZADA (NFA)")
                    self.insignia_estado.setStyleSheet(
                        "background-color: #fee2e2; color: #b91c1c; padding: 4px 12px; "
                        "border-radius: 6px; font-weight: bold; font-size: 13px;"
                    )
                    self.etiqueta_detalle_paso.setText(
                        f"Fin de cinta (≡). Ninguna rama alcanzó aceptación. "
                        f"Ramas totales: {len(traza.ramas)} | Abortadas (∅): {len(traza.ramas_abortadas)}"
                    )
            else:
                self.insignia_estado.setText(f"EN PROGRESO (NFA) — Paso {paso_actual + 1} de {total_pasos}")
                self.insignia_estado.setStyleSheet(
                    "background-color: #eff6ff; color: #1d4ed8; padding: 4px 10px; "
                    "border-radius: 6px; font-weight: bold;"
                )
                ramas_activas_en_paso = [
                    r for r in traza.ramas
                    if any(p.indice_paso == paso_actual and not (r.es_abortada and p.indice_paso == r.indice_aborto)
                           for p in r.pasos)
                ]
                self.etiqueta_detalle_paso.setText(
                    f"Ramas activas en paso actual: {len(ramas_activas_en_paso)} de {len(traza.ramas)} | "
                    f"Abortadas acumuladas (∅): {len([r for r in traza.ramas if r.es_abortada and (r.indice_aborto or 0) <= paso_actual])}"
                )
        else:
            paso_info = traza.pasos[paso_actual]

            if es_ultimo_paso:
                if traza.aceptada:
                    self.insignia_estado.setText("✓ ACEPTADA")
                    self.insignia_estado.setStyleSheet(
                        "background-color: #dcfce7; color: #15803d; padding: 4px 12px; "
                        "border-radius: 6px; font-weight: bold; font-size: 13px;"
                    )
                    self.etiqueta_detalle_paso.setText(
                        f"Fin de cinta (≡) alcanzado. Estado final '{paso_info.estado_actual}' pertenece a F."
                    )
                else:
                    self.insignia_estado.setText("✗ RECHAZADA")
                    self.insignia_estado.setStyleSheet(
                        "background-color: #fee2e2; color: #b91c1c; padding: 4px 12px; "
                        "border-radius: 6px; font-weight: bold; font-size: 13px;"
                    )
                    motivo = traza.motivo_rechazo or f"Estado final '{paso_info.estado_actual}' no pertenece a F."
                    self.etiqueta_detalle_paso.setText(f"{motivo}")
            else:
                self.insignia_estado.setText(f"EN PROGRESO — Paso {paso_actual + 1} de {total_pasos}")
                self.insignia_estado.setStyleSheet(
                    "background-color: #eff6ff; color: #1d4ed8; padding: 4px 10px; "
                    "border-radius: 6px; font-weight: bold;"
                )
                simbolo_leido = paso_info.simbolo
                self.etiqueta_detalle_paso.setText(
                    f"Estado actual: {paso_info.estado_actual} | "
                    f"Símbolo leído: '{simbolo_leido}' → "
                    f"Próximo estado: {paso_info.estado_siguiente}"
                )

        # Actualizar el lienzo gráfico
        self.lienzo.establecer_traza(traza, paso_actual=paso_actual)

    def mostrar_error_evaluacion(self, mensaje: str) -> None:
        """Muestra un mensaje de error cuando la cadena no puede evaluarse."""
        self.insignia_estado.setText("⚠ ERROR DE ENTRADA")
        self.insignia_estado.setStyleSheet(
            "background-color: #fee2e2; color: #b91c1c; padding: 4px 10px; "
            "border-radius: 6px; font-weight: bold;"
        )
        self.etiqueta_detalle_paso.setText(mensaje)
        self.lienzo.establecer_traza(None)
        self.boton_anterior.setEnabled(False)
        self.boton_siguiente.setEnabled(False)
        self.boton_ejecutar_todo.setEnabled(False)
        self.boton_reiniciar.setEnabled(False)

    def limpiar(self) -> None:
        """Limpia el campo de texto y reinicia el estado y lienzo de la simulación."""
        self.campo_cadena.clear()
        self.actualizar_estado(None, 0, 0)
