"""Componente de interfaz para la definición y validación del alfabeto formal."""

from __future__ import annotations
import re
from typing import List

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QValidator
from PyQt6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.model.alfabeto import ordenar_simbolos_alfabeto


class ValidadorAlfabeto(QValidator):
    """Validador en tiempo real para el campo de entrada del alfabeto formal.

    Reglas de validación:
    1. Solo se permiten letras (A-Z, a-z) o números (0-9).
    2. Cada símbolo debe ser exactamente de un solo carácter.
    3. No se permiten caracteres juntos sin separación (ej. 'ab' o '12' se bloquea al escribir).
    4. Separación por comas: no permite dos comas consecutivas (ej. ',,').
    5. Separación por espacios: no permite dos espacios consecutivos (ej. '  ').
    6. No permite espacio antes de coma (' ,').
    7. No permite iniciar con coma ni con espacio.
    """

    def validate(self, input_str: str, pos: int) -> tuple[QValidator.State, str, int]:
        if not input_str:
            return (QValidator.State.Intermediate, input_str, pos)

        # 1. Solo letras ASCII, dígitos, comas y espacios permitidos
        if not re.fullmatch(r"[a-zA-Z0-9, ]*", input_str):
            return (QValidator.State.Invalid, input_str, pos)

        # 2. No empezar con coma ni con espacio
        if input_str[0] in (",", " "):
            return (QValidator.State.Invalid, input_str, pos)

        # 3. No permitir caracteres juntos sin separación (cada símbolo es de 1 carácter)
        if re.search(r"[a-zA-Z0-9]{2}", input_str):
            return (QValidator.State.Invalid, input_str, pos)

        # 4. No permitir comas consecutivas (incluso con espacios entre ellas)
        if re.search(r",\s*,", input_str):
            return (QValidator.State.Invalid, input_str, pos)

        # 5. No permitir espacios consecutivos
        if "  " in input_str:
            return (QValidator.State.Invalid, input_str, pos)

        # 6. No permitir espacio inmediatamente antes de una coma (' ,')
        if re.search(r"\s,", input_str):
            return (QValidator.State.Invalid, input_str, pos)

        # Si termina en coma o espacio, es una entrada válida pero incompleta
        if input_str[-1] in (",", " "):
            return (QValidator.State.Intermediate, input_str, pos)

        return (QValidator.State.Acceptable, input_str, pos)


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

        # Instrucción clara para el usuario
        self.etiqueta_instruccion = QLabel(
            "Ingrese los símbolos del alfabeto (letras o números de 1 carácter, separados por comas o espacios):"
        )
        layout_principal.addWidget(self.etiqueta_instruccion)

        # Fila de entrada de texto y botón
        layout_entrada = QHBoxLayout()
        self.campo_simbolos = QLineEdit()
        self.campo_simbolos.setPlaceholderText("Sección Alfabeto (Σ): Ingrese símbolos aquí (ej. 0, 1 o a, b)")
        self.campo_simbolos.setToolTip(
            "Sección Alfabeto formal Σ: Solo letras o números de 1 carácter separados por comas o espacios.\n"
            "Ejemplos válidos: '0, 1' o 'a, b, c'. No se admiten caracteres especiales."
        )

        # Asignar el validador en tiempo real
        self.validador = ValidadorAlfabeto(self)
        self.campo_simbolos.setValidator(self.validador)
        self.campo_simbolos.returnPressed.connect(self._al_solicitar_definicion)
        layout_entrada.addWidget(self.campo_simbolos)

        self.boton_establecer = QPushButton("Establecer Alfabeto")
        self.boton_establecer.setToolTip("Guardar y aplicar el conjunto del alfabeto formal Σ a toda la aplicación.")
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
        """Valida rigurosamente la entrada y emite la señal con los símbolos procesados."""
        texto_crudo = self.campo_simbolos.text()
        texto = texto_crudo.strip()

        if not texto:
            self.mostrar_error("Debe ingresar al menos un símbolo para el alfabeto (ejemplo: 0, 1 o a, b).")
            return

        if texto_crudo.endswith(",") or texto_crudo.endswith(" "):
            self.mostrar_error("Entrada incompleta: el alfabeto no puede terminar con una coma o espacio incompleto.")
            return

        # 1. Validación de caracteres permitidos
        if not re.fullmatch(r"[a-zA-Z0-9, ]+", texto):
            self.mostrar_error("Solo se permiten letras o números como símbolos del alfabeto (separados por comas o espacios).")
            return

        # 2. Validación de caracteres juntos sin separación
        if re.search(r"[a-zA-Z0-9]{2,}", texto):
            self.mostrar_error("Solo se permite un carácter por símbolo. No escriba caracteres juntos sin separación (ejemplo: use 'a, b' en vez de 'ab').")
            return

        # 3. Validación de comas consecutivas
        if re.search(r",\s*,", texto):
            self.mostrar_error("No se permiten dos o más comas seguidas sin un símbolo en el medio.")
            return

        # 4. Validación de espacios consecutivos
        if "  " in texto:
            self.mostrar_error("No se permiten dos o más espacios seguidos.")
            return

        # 5. Validación de espacio antes de coma
        if re.search(r"\s,", texto):
            self.mostrar_error("Formato inválido: no debe haber espacio antes de la coma (use 'a, b' o 'a,b').")
            return

        # 6. Extracción y verificación individual de cada símbolo
        partes = [s for s in re.split(r"[, ]+", texto) if s]
        for simbolo in partes:
            if len(simbolo) != 1 or not (simbolo.isalnum() and simbolo.isascii()):
                self.mostrar_error(f"Símbolo no válido: '{simbolo}'. Cada símbolo debe ser exactamente una letra o un número.")
                return

        if not partes:
            self.mostrar_error("No se detectaron símbolos válidos.")
            return

        # Ordenar canónicamente: primero números (0-9), luego letras (a-z)
        simbolos_ordenados = ordenar_simbolos_alfabeto(partes)
        cadena_simbolos = ", ".join(simbolos_ordenados)

        # Actualizar el campo escrito inmediatamente al nuevo orden
        self.campo_simbolos.setText(cadena_simbolos)

        self.limpiar_mensaje()
        self.alfabeto_solicitado.emit(simbolos_ordenados)

    def actualizar_alfabeto(self, simbolos: List[str]) -> None:
        """Actualiza la visualización de los símbolos activos del alfabeto y el campo escrito en orden.

        Args:
            simbolos: Lista de símbolos que componen Sigma.
        """
        simbolos_ordenados = ordenar_simbolos_alfabeto(simbolos)
        cadena_simbolos = ", ".join(simbolos_ordenados)
        self.etiqueta_alfabeto_actual.setText(f"Alfabeto actual: Σ = {{ {cadena_simbolos} }}")
        self.campo_simbolos.setText(cadena_simbolos)
        self.mostrar_exito(f"Alfabeto actualizado correctamente con {len(simbolos_ordenados)} símbolo(s).")

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
