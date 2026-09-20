"""Pruebas unitarias para el motor de simulación, traza y renderizado de cinta (Fase 4)."""

import os
import pytest
from PyQt6.QtWidgets import QApplication

from src.controller.controlador_automata import ControladorAutomata
from src.model.automata import Automata
from src.view.lienzo_cinta import LienzoCinta
from src.view.panel_simulacion import PanelSimulacion
from src.view.ventana_principal import VentanaPrincipal


@pytest.fixture(scope="session")
def aplicacion_qt():
    """Fixture que provee la instancia de QApplication para pruebas sin pantalla."""
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    app = QApplication.instance()
    if app is None:
        app = QApplication(["", "-platform", "offscreen"])
    yield app


@pytest.fixture
def dfa_ceros_pares():
    """Autómata que reconoce cadenas con número par de '0's."""
    dfa = Automata(
        alfabeto=["0", "1"],
        estados=["par", "impar"],
        estado_inicial="par",
        estados_aceptacion=["par"],
    )
    dfa.agregar_transicion("par", "0", "impar")
    dfa.agregar_transicion("par", "1", "par")
    dfa.agregar_transicion("impar", "0", "par")
    dfa.agregar_transicion("impar", "1", "impar")
    return dfa


def test_simulacion_inicio_exitoso(aplicacion_qt, dfa_ceros_pares):
    vista = VentanaPrincipal()
    controlador = ControladorAutomata(modelo=dfa_ceros_pares, vista=vista)

    exito = controlador.al_solicitar_evaluacion("00")
    assert exito is True
    assert controlador._traza_actual is not None
    assert controlador._paso_actual == 0

    panel = vista.panel_simulacion
    assert "EN PROGRESO" in panel.insignia_estado.text()
    assert panel.boton_siguiente.isEnabled() is True
    assert panel.boton_anterior.isEnabled() is False


def test_simulacion_navegacion_paso_a_paso(aplicacion_qt, dfa_ceros_pares):
    vista = VentanaPrincipal()
    controlador = ControladorAutomata(modelo=dfa_ceros_pares, vista=vista)

    controlador.al_solicitar_evaluacion("00")
    # "00" tiene 3 pasos: paso 0 (lee '0'), paso 1 (lee '0'), paso 2 (delimitador ≡)
    assert len(controlador._traza_actual.pasos) == 3

    # Avanzar al paso 1
    controlador.al_avanzar_paso()
    assert controlador._paso_actual == 1
    assert vista.panel_simulacion.boton_anterior.isEnabled() is True
    assert vista.panel_simulacion.boton_siguiente.isEnabled() is True

    # Avanzar al paso final 2 (delimitador)
    controlador.al_avanzar_paso()
    assert controlador._paso_actual == 2
    assert "ACEPTADA" in vista.panel_simulacion.insignia_estado.text()
    assert vista.panel_simulacion.boton_siguiente.isEnabled() is False

    # Retroceder al paso 1
    controlador.al_retroceder_paso()
    assert controlador._paso_actual == 1
    assert "EN PROGRESO" in vista.panel_simulacion.insignia_estado.text()

    # Reiniciar al paso 0
    controlador.al_reiniciar_simulacion()
    assert controlador._paso_actual == 0


def test_simulacion_ejecutar_todo(aplicacion_qt, dfa_ceros_pares):
    vista = VentanaPrincipal()
    controlador = ControladorAutomata(modelo=dfa_ceros_pares, vista=vista)

    controlador.al_solicitar_evaluacion("00")
    controlador.al_ejecutar_todo()

    assert controlador._paso_actual == 2
    assert "ACEPTADA" in vista.panel_simulacion.insignia_estado.text()


def test_simulacion_cadena_rechazada(aplicacion_qt, dfa_ceros_pares):
    vista = VentanaPrincipal()
    controlador = ControladorAutomata(modelo=dfa_ceros_pares, vista=vista)

    controlador.al_solicitar_evaluacion("0")
    controlador.al_ejecutar_todo()

    assert "RECHAZADA" in vista.panel_simulacion.insignia_estado.text()


def test_simulacion_error_simbolo_invalido(aplicacion_qt, dfa_ceros_pares):
    vista = VentanaPrincipal()
    controlador = ControladorAutomata(modelo=dfa_ceros_pares, vista=vista)

    exito = controlador.al_solicitar_evaluacion("012")
    assert exito is False
    assert "ERROR DE ENTRADA" in vista.panel_simulacion.insignia_estado.text()
    assert "Símbolo no válido" in vista.panel_simulacion.etiqueta_detalle_paso.text()


def test_simulacion_error_sin_estado_inicial(aplicacion_qt):
    dfa = Automata(alfabeto=["a"], estados=["q0"])
    vista = VentanaPrincipal()
    controlador = ControladorAutomata(modelo=dfa, vista=vista)

    exito = controlador.al_solicitar_evaluacion("a")
    assert exito is False
    assert "estado inicial" in vista.panel_simulacion.etiqueta_detalle_paso.text()


def test_lienzo_cinta_elementos_escena(aplicacion_qt, dfa_ceros_pares):
    """Verifica que el lienzo gráfico renderice la llave, celdas, delimitador y estados."""
    lienzo = LienzoCinta()
    traza = dfa_ceros_pares.generar_traza("01")

    lienzo.establecer_traza(traza, paso_actual=1)
    items = lienzo.scene().items()

    # Debe haber múltiples elementos gráficos: rectángulos de celdas, textos, líneas y flechas
    assert len(items) > 10

    # Verificar que el texto del delimitador '≡' y de los puntos suspensivos '…' estén presentes
    textos = [item.toPlainText() for item in items if hasattr(item, "toPlainText")]
    assert "≡" in textos
    assert "…" in textos
    assert "u" in textos
    assert "0" in textos
    assert "1" in textos


def test_lienzo_cinta_estado_espera(aplicacion_qt):
    """Verifica que sin traza se muestre el texto indicativo de espera."""
    lienzo = LienzoCinta()
    lienzo.establecer_traza(None)
    items = lienzo.scene().items()
    textos = [item.toPlainText() for item in items if hasattr(item, "toPlainText")]
    assert any("Ingrese una cadena" in t for t in textos)
