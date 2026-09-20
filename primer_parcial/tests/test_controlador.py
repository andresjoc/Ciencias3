"""Pruebas unitarias para el controlador y la interacción MVC."""

import os
import sys
import pytest
from PyQt6.QtWidgets import QApplication

from src.controller.controlador_automata import ControladorAutomata
from src.model.automata import Automata
from src.view.panel_alfabeto import PanelAlfabeto
from src.view.ventana_principal import VentanaPrincipal


@pytest.fixture(scope="session")
def aplicacion_qt():
    """Fixture que proporciona una instancia de QApplication para pruebas sin pantalla."""
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    app = QApplication.instance()
    if app is None:
        app = QApplication(["", "-platform", "offscreen"])
    yield app


def test_inicializacion_controlador(aplicacion_qt):
    modelo = Automata()
    vista = VentanaPrincipal()
    controlador = ControladorAutomata(modelo=modelo, vista=vista)

    assert controlador.modelo is modelo
    assert controlador.vista is vista
    assert "Σ = { }" in vista.panel_alfabeto.etiqueta_alfabeto_actual.text()


def test_controlador_sincroniza_modelo_existente(aplicacion_qt):
    modelo = Automata(alfabeto=["0", "1"])
    vista = VentanaPrincipal()
    _controlador = ControladorAutomata(modelo=modelo, vista=vista)

    assert "0, 1" in vista.panel_alfabeto.etiqueta_alfabeto_actual.text()


def test_controlador_definir_alfabeto_valido(aplicacion_qt):
    modelo = Automata()
    vista = VentanaPrincipal()
    controlador = ControladorAutomata(modelo=modelo, vista=vista)

    exito = controlador.al_definir_alfabeto(["a", "b", "c"])
    assert exito is True
    assert modelo.alfabeto.simbolos == ["a", "b", "c"]
    assert "a, b, c" in vista.panel_alfabeto.etiqueta_alfabeto_actual.text()
    assert "éxito" in vista.barra_estado.currentMessage().lower()


def test_controlador_definir_alfabeto_simbolo_invalido(aplicacion_qt):
    modelo = Automata()
    vista = VentanaPrincipal()
    controlador = ControladorAutomata(modelo=modelo, vista=vista)

    # Cadena vacía como símbolo
    exito = controlador.al_definir_alfabeto([""])
    assert exito is False
    assert "no puede ser una cadena vacía" in vista.panel_alfabeto.etiqueta_mensaje.text()
    assert "Error" in vista.barra_estado.currentMessage()


def test_panel_alfabeto_emision_de_senales(aplicacion_qt):
    panel = PanelAlfabeto()
    simbolos_capturados = []

    panel.alfabeto_solicitado.connect(lambda s: simbolos_capturados.extend(s))

    # Entrada separada por comas y espacios
    panel.establecer_texto_entrada("0, 1, 2")
    panel._al_solicitar_definicion()

    assert simbolos_capturados == ["0", "1", "2"]
    assert panel.etiqueta_mensaje.text() == ""


def test_panel_alfabeto_entrada_vacia_error(aplicacion_qt):
    panel = PanelAlfabeto()
    senales_emitidas = []
    panel.alfabeto_solicitado.connect(lambda s: senales_emitidas.append(s))

    panel.establecer_texto_entrada("   ")
    panel._al_solicitar_definicion()

    assert len(senales_emitidas) == 0
    assert "Debe ingresar al menos un símbolo" in panel.etiqueta_mensaje.text()
