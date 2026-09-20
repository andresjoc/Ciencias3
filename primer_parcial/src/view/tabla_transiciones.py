"""Componente visual para la edición y visualización de la tabla de transiciones."""

from __future__ import annotations
import re
from typing import Dict, List, Optional, Set

from PyQt6.QtCore import QRegularExpression, Qt, pyqtSignal
from PyQt6.QtGui import QRegularExpressionValidator
from PyQt6.QtWidgets import (
    QCheckBox,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class TablaTransiciones(QGroupBox):
    """Panel con vista matricial (QTableWidget) para la tabla de transiciones del autómata.

    Las filas corresponden a los estados Q y las columnas a los símbolos del alfabeto Sigma.

    Señales:
        transicion_modificada (str, str, str): Se emite con (estado_origen, simbolo, estado_destino)
            cuando una celda de la tabla es editada por el usuario.
        estado_agregado (str, bool, bool): Se emite con (nombre_estado, es_inicial, es_aceptacion)
            cuando el usuario añade un estado desde la interfaz.
        estado_eliminado (str): Se emite con el identificador del estado a eliminar.
    """

    transicion_modificada = pyqtSignal(str, str, str)
    estado_agregado = pyqtSignal(str, bool, bool)
    estado_eliminado = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Tabla de Transiciones (δ)", parent)
        self._estados: List[str] = []
        self._simbolos: List[str] = []
        self._transiciones_cache: Dict[str, Dict[str, str]] = {}
        self._estado_inicial_cache: Optional[str] = None
        self._estados_aceptacion_cache: Set[str] = set()
        self._actualizando_internamente = False
        self._inicializar_ui()

    def _inicializar_ui(self) -> None:
        """Construye los controles de la tabla y la barra de gestión de estados."""
        layout_principal = QVBoxLayout()
        layout_principal.setSpacing(10)

        # Fila para agregar nuevos estados
        layout_gestion_estados = QHBoxLayout()
        layout_gestion_estados.setSpacing(8)

        self.campo_nombre_estado = QLineEdit()
        self.campo_nombre_estado.setPlaceholderText("Sección Matriz δ: Nombre de estado (ej. q0, q1)")
        self.campo_nombre_estado.setToolTip(
            "Sección Matriz de Transiciones: Ingrese el identificador alfanumérico del nuevo estado formal (ej. q0)."
        )
        self.campo_nombre_estado.setValidator(QRegularExpressionValidator(QRegularExpression(r"[a-zA-Z0-9]*"), self))
        self.campo_nombre_estado.returnPressed.connect(self._al_agregar_estado)
        layout_gestion_estados.addWidget(self.campo_nombre_estado)

        self.check_inicial = QCheckBox("Inicial (q₀)")
        self.check_inicial.setToolTip("Marcar si este nuevo estado será el estado inicial formal q₀ del autómata.")
        layout_gestion_estados.addWidget(self.check_inicial)

        self.check_aceptacion = QCheckBox("Aceptación (F)")
        self.check_aceptacion.setToolTip("Marcar si este estado formará parte del conjunto de estados de aceptación F.")
        layout_gestion_estados.addWidget(self.check_aceptacion)

        self.boton_agregar_estado = QPushButton("Agregar Estado")
        self.boton_agregar_estado.setToolTip("Registrar el nuevo estado formal en el autómata y la matriz.")
        self.boton_agregar_estado.clicked.connect(self._al_agregar_estado)
        layout_gestion_estados.addWidget(self.boton_agregar_estado)

        self.boton_eliminar_estado = QPushButton("Eliminar Estado")
        self.boton_eliminar_estado.setStyleSheet("color: #b91c1c;")
        self.boton_eliminar_estado.setToolTip("Eliminar de la matriz y del autómata el estado seleccionado.")
        self.boton_eliminar_estado.clicked.connect(self._al_eliminar_estado)
        layout_gestion_estados.addWidget(self.boton_eliminar_estado)

        layout_principal.addLayout(layout_gestion_estados)

        # Tabla matricial (QTableWidget)
        self.tabla = QTableWidget()
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setToolTip(
            "Matriz formal de transiciones δ(q, σ):\n"
            "Doble clic en una celda para editar el estado destino (o varios separados por comas para NFA)."
        )
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla.cellChanged.connect(self._al_cambiar_celda)
        layout_principal.addWidget(self.tabla)

        # Mensaje de ayuda o advertencias de validación
        self.etiqueta_estado_tabla = QLabel("Convención: → estado inicial | * estado de aceptación")
        self.etiqueta_estado_tabla.setStyleSheet("color: #475569; font-size: 11px;")
        layout_principal.addWidget(self.etiqueta_estado_tabla)

        self.setLayout(layout_principal)

    def _al_agregar_estado(self) -> None:
        """Valida y emite la señal para agregar un nuevo estado."""
        nombre = self.campo_nombre_estado.text().strip()
        if not nombre:
            self.mostrar_advertencia("Debe especificar un nombre para el estado.")
            return

        if not (nombre.isalnum() and nombre.isascii()):
            self.mostrar_advertencia("El nombre del estado solo puede contener letras y números sin caracteres especiales.")
            return

        es_inicial = self.check_inicial.isChecked()
        es_aceptacion = self.check_aceptacion.isChecked()

        self.limpiar_advertencia()
        self.estado_agregado.emit(nombre, es_inicial, es_aceptacion)
        self.campo_nombre_estado.clear()
        self.check_inicial.setChecked(False)
        self.check_aceptacion.setChecked(False)

    def _al_eliminar_estado(self) -> None:
        """Determina el estado seleccionado y emite la señal para su eliminación."""
        fila_actual = self.tabla.currentRow()
        if fila_actual < 0 or fila_actual >= len(self._estados):
            self.mostrar_advertencia("Seleccione un estado en la tabla para eliminar.")
            return

        estado = self._estados[fila_actual]
        self.limpiar_advertencia()
        self.estado_eliminado.emit(estado)

    def _al_cambiar_celda(self, fila: int, columna: int) -> None:
        """Maneja la edición manual de una celda por parte del usuario."""
        if self._actualizando_internamente:
            return

        if fila >= len(self._estados) or columna >= len(self._simbolos):
            return

        estado_origen = self._estados[fila]
        simbolo = self._simbolos[columna]
        item = self.tabla.item(fila, columna)
        nuevo_destino = item.text().strip() if item else ""

        # Validar caracteres especiales: solo alfanumérico, comas o espacios para destinos
        if nuevo_destino and not re.fullmatch(r"[a-zA-Z0-9, ]*", nuevo_destino):
            self.mostrar_advertencia("Los estados destino solo pueden contener letras y números sin caracteres especiales.")
            self.actualizar_datos(
                self._estados,
                self._simbolos,
                self._transiciones_cache,
                self._estado_inicial_cache,
                self._estados_aceptacion_cache,
            )
            return

        self.limpiar_advertencia()
        self.transicion_modificada.emit(estado_origen, simbolo, nuevo_destino)

    def actualizar_datos(
        self,
        estados: List[str],
        simbolos: List[str],
        transiciones: Dict[str, Dict[str, str]],
        estado_inicial: Optional[str],
        estados_aceptacion: Set[str],
    ) -> None:
        """Sincroniza y repuebla la tabla de transiciones con el modelo.

        Args:
            estados: Lista de estados Q en orden.
            simbolos: Lista de símbolos Sigma en orden.
            transiciones: Diccionario delta(origen, simbolo) = destino.
            estado_inicial: Estado q0.
            estados_aceptacion: Conjunto de estados F.
        """
        self._actualizando_internamente = True
        self._estados = list(estados)
        self._simbolos = list(simbolos)
        self._transiciones_cache = {
            orig: dict(t) for orig, t in transiciones.items()
        }
        self._estado_inicial_cache = estado_inicial
        self._estados_aceptacion_cache = set(estados_aceptacion)

        self.tabla.setRowCount(len(estados))
        self.tabla.setColumnCount(len(simbolos))

        # Encabezados de columnas (Símbolos Sigma)
        self.tabla.setHorizontalHeaderLabels(simbolos)

        # Encabezados de filas (Estados Q con prefijos formales)
        etiquetas_filas = []
        for estado in estados:
            prefijo = ""
            if estado == estado_inicial:
                prefijo += "→ "
            if estado in estados_aceptacion:
                prefijo += "* "
            etiquetas_filas.append(f"{prefijo}{estado}")

        self.tabla.setVerticalHeaderLabels(etiquetas_filas)

        # Llenar celdas con el estado destino correspondiente
        for fila, estado in enumerate(estados):
            trans_estado = transiciones.get(estado, {})
            for col, simbolo in enumerate(simbolos):
                destino = trans_estado.get(simbolo, "")
                if isinstance(destino, (set, list)):
                    texto_celda = ", ".join(sorted(destino)) if destino else ""
                else:
                    texto_celda = str(destino) if destino else ""
                item = QTableWidgetItem(texto_celda)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabla.setItem(fila, col, item)

        self._actualizando_internamente = False

    def mostrar_advertencia(self, mensaje: str) -> None:
        """Muestra una advertencia visual de validación."""
        self.etiqueta_estado_tabla.setStyleSheet(
            "color: #dc2626; font-size: 12px; font-weight: 500;"
        )
        self.etiqueta_estado_tabla.setText(f"⚠ {mensaje}")

    def limpiar_advertencia(self) -> None:
        """Restaura el mensaje predeterminado de la tabla."""
        self.etiqueta_estado_tabla.setStyleSheet("color: #475569; font-size: 11px;")
        self.etiqueta_estado_tabla.setText(
            "Convención: → estado inicial | * estado de aceptación"
        )
