"""Componente de interfaz para la definición y validación del alfabeto formal."""

from __future__ import annotations
import re
from typing import List

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class PanelAlfabeto(QGroupBox):
    """Panel visual para ingresar, validar y gestionar el alfabeto Sigma.

    Señales:
        alfabeto_solicitado (list): Se emite con la lista de símbolos ingresados
            cuando el usuario solicita establecer el alfabeto.
    """

    alfabeto_solicitado = pyqtSignal(list)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Definición del Alfabeto (Σ)", parent)
        self._inicializar_ui()

    def _inicializar_ui(self) -> None:
        """Configura los controles visuales y el layout del panel."""
        layout_principal = QVBoxLayout()
        layout_principal.setSpacing(8)

        # Instrucción para el usuario
        self.etiqueta_instruccion = QLabel(
            "Ingrese los símbolos del alfabeto separados por comas o espacios:"
        )
        layout_principal.addWidget(self.etiqueta_instruccion)

        # Fila de entrada de texto y botón
        layout_entrada = QHBoxLayout()
        self.campo_simbolos = QLineEdit()
        self.campo_simbolos.setPlaceholderText("Ejemplo: 0, 1 o a, b, c")
        self.campo_simbolos.returnPressed.connect(self._al_solicitar_definicion)
        layout_entrada.addWidget(self.campo_simbolos)

        self.boton_establecer = QPushButton("Establecer Alfabeto")
        self.boton_establecer.clicked.connect(self._al_solicitar_definicion)
        layout_entrada.addWidget(self.boton_establecer)

        layout_principal.addLayout(layout_entrada)

        # Etiqueta para mostrar el alfabeto actual formalmente
        self.etiqueta_alfabeto_actual = QLabel("Alfabeto actual: Σ = { }")
        self.etiqueta_alfabeto_actual.setStyleSheet(
            "font-weight: bold; font-size: 13px; color: #1e293b;"
        )
        layout_principal.addWidget(self.etiqueta_alfabeto_actual)

        # Etiqueta para mensajes de validación / error
        self.etiqueta_mensaje = QLabel("")
        self.etiqueta_mensaje.setWordWrap(True)
        layout_principal.addWidget(self.etiqueta_mensaje)

        self.setLayout(layout_principal)

    def _al_solicitar_definicion(self) -> None:
        """Procesa el texto ingresado en el campo y emite la señal si es válido."""
        texto = self.campo_simbolos.text().strip()
        if not texto:
            self.mostrar_error("Debe ingresar al menos un símbolo para el alfabeto.")
            return

        # Dividir por comas o espacios
        partes = [s.strip() for s in re.split(r"[,;\s]+", texto) if s.strip()]

        if not partes:
            self.mostrar_error("No se detectaron símbolos válidos.")
            return

        self.limpiar_mensaje()
        self.alfabeto_solicitado.emit(partes)

    def actualizar_alfabeto(self, simbolos: List[str]) -> None:
        """Actualiza la visualización de los símbolos activos del alfabeto.

        Args:
            simbolos: Lista de símbolos que componen Sigma.
        """
        cadena_simbolos = ", ".join(simbolos)
        self.etiqueta_alfabeto_actual.setText(f"Alfabeto actual: Σ = {{ {cadena_simbolos} }}")
        self.mostrar_exito(f"Alfabeto actualizado correctamente con {len(simbolos)} símbolo(s).")

    def mostrar_error(self, mensaje: str) -> None:
        """Muestra un mensaje de error estilizado en rojo."""
        self.etiqueta_mensaje.setStyleSheet("color: #dc2626; font-size: 12px; font-weight: 500;")
        self.etiqueta_mensaje.setText(f"⚠ {mensaje}")

    def mostrar_exito(self, mensaje: str) -> None:
        """Muestra un mensaje de éxito estilizado en verde."""
        self.etiqueta_mensaje.setStyleSheet("color: #16a34a; font-size: 12px; font-weight: 500;")
        self.etiqueta_mensaje.setText(f"✓ {mensaje}")

    def limpiar_mensaje(self) -> None:
        """Limpia la etiqueta de mensajes."""
        self.etiqueta_mensaje.setText("")

    def obtener_texto_entrada(self) -> str:
        """Retorna el texto actual del campo de entrada."""
        return self.campo_simbolos.text()

    def establecer_texto_entrada(self, texto: str) -> None:
        """Define el texto en el campo de entrada."""
        self.campo_simbolos.setText(texto)
