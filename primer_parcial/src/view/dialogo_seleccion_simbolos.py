"""Diálogo interactivo para seleccionar qué caracteres del alfabeto se añaden a una conexión."""

from __future__ import annotations
from typing import List, Set

from PyQt6.QtCore import QEvent, Qt, pyqtSignal
from PyQt6.QtGui import QStandardItem, QStandardItemModel
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class DesplegableMultiSeleccion(QComboBox):
    """QComboBox interactivo que permite marcar y desmarcar múltiples opciones con casillas en tiempo real."""

    seleccion_cambiada = pyqtSignal(set)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.modelo = QStandardItemModel(self)
        self.setModel(self.modelo)

        # Editor de solo lectura para mostrar inmediatamente los caracteres seleccionados
        self.line_edit = QLineEdit(self)
        self.line_edit.setReadOnly(True)
        self.line_edit.setPlaceholderText("Seleccione los caracteres del alfabeto...")
        self.line_edit.setToolTip("Caracteres seleccionados actualmente en el desplegable")
        self.setLineEdit(self.line_edit)

        # Interceptar clics en la lista para marcar/desmarcar inmediatamente sin cerrar el menú
        self.view().viewport().installEventFilter(self)
        self.view().installEventFilter(self)
        self.modelo.itemChanged.connect(self._al_cambiar_item)

        self.setToolTip("Despliegue para marcar o desmarcar los caracteres que desea incluir en la conexión.")

    def eventFilter(self, obj, event) -> bool:
        """Permite alternar las casillas al hacer clic o presionar espacio sin cerrar el desplegable."""
        if obj == self.view().viewport():
            if event.type() == QEvent.Type.MouseButtonRelease and event.button() == Qt.MouseButton.LeftButton:
                index = self.view().indexAt(event.pos())
                if index.isValid():
                    item = self.modelo.itemFromIndex(index)
                    if item:
                        nuevo_estado = (
                            Qt.CheckState.Unchecked
                            if item.checkState() == Qt.CheckState.Checked
                            else Qt.CheckState.Checked
                        )
                        item.setCheckState(nuevo_estado)
                        return True
        elif obj == self.view():
            if event.type() == QEvent.Type.KeyPress and event.key() == Qt.Key.Key_Space:
                index = self.view().currentIndex()
                if index.isValid():
                    item = self.modelo.itemFromIndex(index)
                    if item:
                        nuevo_estado = (
                            Qt.CheckState.Unchecked
                            if item.checkState() == Qt.CheckState.Checked
                            else Qt.CheckState.Checked
                        )
                        item.setCheckState(nuevo_estado)
                        return True
        return super().eventFilter(obj, event)

    def _al_cambiar_item(self, item: QStandardItem) -> None:
        """Actualiza el texto visible y emite la señal de cambio inmediatamente."""
        self.actualizar_texto()
        self.seleccion_cambiada.emit(self.obtener_elementos_marcados())

    def agregar_opcion(self, texto: str, marcado: bool = False) -> None:
        """Añade un elemento con casilla de verificación al desplegable."""
        item = QStandardItem(texto)
        item.setCheckable(True)
        item.setCheckState(Qt.CheckState.Checked if marcado else Qt.CheckState.Unchecked)
        self.modelo.appendRow(item)
        self.actualizar_texto()

    def obtener_elementos_marcados(self) -> Set[str]:
        """Obtiene el conjunto de textos de los elementos que están marcados."""
        marcados: Set[str] = set()
        for fila in range(self.modelo.rowCount()):
            item = self.modelo.item(fila)
            if item and item.checkState() == Qt.CheckState.Checked:
                marcados.add(item.text())
        return marcados

    def establecer_todos(self, marcado: bool) -> None:
        """Marca o desmarca todos los elementos del desplegable de inmediato."""
        estado = Qt.CheckState.Checked if marcado else Qt.CheckState.Unchecked
        self.modelo.blockSignals(True)
        for fila in range(self.modelo.rowCount()):
            item = self.modelo.item(fila)
            if item:
                item.setCheckState(estado)
        self.modelo.blockSignals(False)
        self.actualizar_texto()
        self.seleccion_cambiada.emit(self.obtener_elementos_marcados())

    def actualizar_texto(self) -> None:
        """Actualiza el campo de texto del desplegable con los elementos marcados."""
        marcados = sorted(self.obtener_elementos_marcados())
        if marcados:
            self.line_edit.setText(", ".join(marcados))
        else:
            self.line_edit.clear()


class DialogoSeleccionSimbolos(QDialog):
    """Diálogo modal para configurar los caracteres del alfabeto asignados a una conexión."""

    def __init__(
        self,
        origen: str,
        destino: str,
        alfabeto_disponible: List[str],
        simbolos_actuales: Set[str] | List[str] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Configurar Caracteres de la Conexión")
        self.setMinimumWidth(400)

        self.origen = origen
        self.destino = destino
        self.alfabeto_disponible = list(alfabeto_disponible)
        self.simbolos_actuales: Set[str] = set(simbolos_actuales or [])

        self.desplegable: DesplegableMultiSeleccion | None = None
        self.campo_resumen: QLineEdit | None = None

        self._inicializar_ui()

    def _inicializar_ui(self) -> None:
        layout_principal = QVBoxLayout(self)
        layout_principal.setSpacing(14)

        # Encabezado formal de la transición
        grupo_info = QGroupBox("Detalle de la Conexión")
        layout_info = QVBoxLayout(grupo_info)

        etiqueta_detalle = QLabel(
            f"<b>Transición:</b> δ(<code>{self.origen}</code>, σ) = <code>{self.destino}</code>"
        )
        etiqueta_detalle.setStyleSheet("font-size: 13px; color: #1e293b;")
        layout_info.addWidget(etiqueta_detalle)

        if not self.alfabeto_disponible:
            # Caso donde NO hay alfabeto definido: Informar y redirigir a la pantalla principal
            etiqueta_sin_alfabeto = QLabel(
                "⚠ <b>No hay un alfabeto formal (Σ) definido en el autómata.</b><br><br>"
                "No es posible añadir caracteres a la conexión directamente aquí.<br>"
                "Por favor, configure primero los símbolos en la sección "
                "<b>'Definición del Alfabeto (Σ)'</b> de la pantalla principal."
            )
            etiqueta_sin_alfabeto.setStyleSheet(
                "color: #b45309; font-size: 12px; background-color: #fef3c7; "
                "border: 1px solid #f59e0b; border-radius: 6px; padding: 10px;"
            )
            etiqueta_sin_alfabeto.setWordWrap(True)
            layout_info.addWidget(etiqueta_sin_alfabeto)
            layout_principal.addWidget(grupo_info)

            # Botón único para cerrar/entendido
            self.botones_dialogo = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
            boton_cerrar = self.botones_dialogo.button(QDialogButtonBox.StandardButton.Close)
            boton_cerrar.setText("Entendido")
            boton_cerrar.setToolTip("Cerrar este diálogo y definir el alfabeto en la pantalla principal.")
            self.botones_dialogo.rejected.connect(self.reject)
            layout_principal.addWidget(self.botones_dialogo)
            return

        etiqueta_guia = QLabel(
            "Seleccione del desplegable qué caracteres del alfabeto formarán parte de esta conexión:"
        )
        etiqueta_guia.setStyleSheet("color: #64748b; font-size: 11px;")
        etiqueta_guia.setWordWrap(True)
        layout_info.addWidget(etiqueta_guia)
        layout_principal.addWidget(grupo_info)

        # Desplegable de símbolos con casillas de verificación
        self.desplegable = DesplegableMultiSeleccion(self)
        for sim in self.alfabeto_disponible:
            esta_marcado = sim in self.simbolos_actuales
            self.desplegable.agregar_opcion(sim, marcado=esta_marcado)

        self.desplegable.seleccion_cambiada.connect(self._al_cambiar_seleccion)
        layout_principal.addWidget(self.desplegable)

        # Botones auxiliares para selección rápida
        layout_botones_rapidos = QHBoxLayout()
        self.boton_marcar_todos = QPushButton("Marcar Todos")
        self.boton_marcar_todos.setToolTip("Marcar todos los caracteres disponibles del alfabeto")
        self.boton_marcar_todos.clicked.connect(lambda: self._establecer_todos(True))
        layout_botones_rapidos.addWidget(self.boton_marcar_todos)

        self.boton_desmarcar_todos = QPushButton("Desmarcar Todos")
        self.boton_desmarcar_todos.setToolTip("Desmarcar todos los caracteres")
        self.boton_desmarcar_todos.clicked.connect(lambda: self._establecer_todos(False))
        layout_botones_rapidos.addWidget(self.boton_desmarcar_todos)

        layout_principal.addLayout(layout_botones_rapidos)

        # Campo de vista previa de los símbolos seleccionados en tiempo real
        self.campo_resumen = QLineEdit()
        self.campo_resumen.setReadOnly(True)
        self.campo_resumen.setPlaceholderText("Ningún carácter seleccionado (la conexión quedará vacía)")
        self.campo_resumen.setToolTip("Muestra en tiempo real los caracteres seleccionados que se aplicarán a la conexión.")
        self.campo_resumen.setStyleSheet("background-color: #f8fafc; font-weight: bold; color: #2563eb;")
        layout_principal.addWidget(self.campo_resumen)

        self._actualizar_resumen()

        # Botones Aceptar / Cancelar
        self.botones_dialogo = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.botones_dialogo.button(QDialogButtonBox.StandardButton.Ok).setText("Aplicar a Conexión")
        self.botones_dialogo.button(QDialogButtonBox.StandardButton.Ok).setToolTip(
            "Guardar los caracteres seleccionados y actualizar la flecha de transición"
        )
        self.botones_dialogo.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        self.botones_dialogo.button(QDialogButtonBox.StandardButton.Cancel).setToolTip(
            "Cerrar sin modificar la conexión"
        )

        self.botones_dialogo.accepted.connect(self.accept)
        self.botones_dialogo.rejected.connect(self.reject)
        layout_principal.addWidget(self.botones_dialogo)

    def _al_cambiar_seleccion(self, seleccionados: Set[str] | None = None) -> None:
        """Actualiza el campo de resumen inmediatamente cuando el usuario marca o desmarca."""
        self._actualizar_resumen()

    def _establecer_todos(self, marcado: bool) -> None:
        """Marca o desmarca todos los elementos y actualiza el resumen inmediatamente."""
        if self.desplegable:
            self.desplegable.establecer_todos(marcado)
        self._actualizar_resumen()

    def _actualizar_resumen(self) -> None:
        """Refresca el texto en el campo resumen con los símbolos activos."""
        if not self.campo_resumen:
            return
        seleccionados = self.obtener_simbolos_seleccionados()
        if seleccionados:
            texto = ", ".join(sorted(seleccionados))
            self.campo_resumen.setText(f"Caracteres a añadir: {texto}")
        else:
            self.campo_resumen.clear()

    def obtener_simbolos_seleccionados(self) -> Set[str]:
        """Retorna el conjunto de caracteres seleccionados por el usuario."""
        if self.desplegable:
            return self.desplegable.obtener_elementos_marcados()
        return set()
