"""Pruebas unitarias para el editor de tabla de transiciones y su integración MVC."""

import os
import pytest
from PyQt6.QtWidgets import QApplication

from src.controller.controlador_automata import ControladorAutomata
from src.model.automata import Automata
from src.view.ventana_principal import VentanaPrincipal


@pytest.fixture(scope="session")
def aplicacion_qt():
    """Fixture que provee la instancia de QApplication para pruebas sin interfaz de pantalla."""
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    app = QApplication.instance()
    if app is None:
        app = QApplication(["", "-platform", "offscreen"])
    yield app


def test_tabla_inicializacion_vacia(aplicacion_qt):
    modelo = Automata()
    vista = VentanaPrincipal()
    _controlador = ControladorAutomata(modelo=modelo, vista=vista)

    tabla = vista.tabla_transiciones.tabla
    assert tabla.rowCount() == 0
    assert tabla.columnCount() == 0


def test_tabla_columnas_se_actualizan_con_alfabeto(aplicacion_qt):
    modelo = Automata()
    vista = VentanaPrincipal()
    controlador = ControladorAutomata(modelo=modelo, vista=vista)

    controlador.al_definir_alfabeto(["0", "1"])

    tabla = vista.tabla_transiciones.tabla
    assert tabla.columnCount() == 2
    assert tabla.horizontalHeaderItem(0).text() == "0"
    assert tabla.horizontalHeaderItem(1).text() == "1"


def test_tabla_agregar_estados(aplicacion_qt):
    modelo = Automata(alfabeto=["a", "b"])
    vista = VentanaPrincipal()
    controlador = ControladorAutomata(modelo=modelo, vista=vista)

    # Agregar estado inicial q0
    controlador.al_agregar_estado("q0", es_inicial=True, es_aceptacion=False)
    # Agregar estado de aceptación q1
    controlador.al_agregar_estado("q1", es_inicial=False, es_aceptacion=True)

    assert modelo.estados == ["q0", "q1"]
    assert modelo.estado_inicial == "q0"
    assert modelo.estados_aceptacion == {"q1"}

    tabla = vista.tabla_transiciones.tabla
    assert tabla.rowCount() == 2
    assert "→ q0" in tabla.verticalHeaderItem(0).text()
    assert "* q1" in tabla.verticalHeaderItem(1).text()


def test_tabla_edicion_transicion_valida(aplicacion_qt):
    modelo = Automata(alfabeto=["0", "1"])
    vista = VentanaPrincipal()
    controlador = ControladorAutomata(modelo=modelo, vista=vista)

    controlador.al_agregar_estado("q0", es_inicial=True, es_aceptacion=False)
    controlador.al_agregar_estado("q1", es_inicial=False, es_aceptacion=True)

    # Modificar transición: delta(q0, 0) = q1
    exito = controlador.al_modificar_transicion("q0", "0", "q1")
    assert exito is True
    assert modelo.obtener_transicion("q0", "0") == "q1"

    # Verificar que la celda de la tabla tenga 'q1'
    tabla = vista.tabla_transiciones.tabla
    assert tabla.item(0, 0).text() == "q1"


def test_tabla_edicion_transicion_invalida_rechazada(aplicacion_qt):
    """Validación estricta: si el estado destino no existe en Q, se rechaza y advierte."""
    modelo = Automata(alfabeto=["0", "1"])
    vista = VentanaPrincipal()
    controlador = ControladorAutomata(modelo=modelo, vista=vista)

    controlador.al_agregar_estado("q0", es_inicial=True, es_aceptacion=False)

    # Intentar asignar como destino un estado inexistente 'q_fantasma'
    exito = controlador.al_modificar_transicion("q0", "0", "q_fantasma")
    assert exito is False
    assert modelo.obtener_transicion("q0", "0") is None

    # Verifica advertencia en la vista
    assert "no existe en Q" in vista.tabla_transiciones.etiqueta_estado_tabla.text()
    assert "Validación rechazada" in vista.barra_estado.currentMessage()

    # Verifica que la celda no guarde el valor inválido
    tabla = vista.tabla_transiciones.tabla
    assert tabla.item(0, 0).text() == ""


def test_tabla_edicion_transicion_vacia_elimina(aplicacion_qt):
    modelo = Automata(alfabeto=["0", "1"])
    vista = VentanaPrincipal()
    controlador = ControladorAutomata(modelo=modelo, vista=vista)

    controlador.al_agregar_estado("q0", es_inicial=True, es_aceptacion=False)
    controlador.al_agregar_estado("q1", es_inicial=False, es_aceptacion=True)
    controlador.al_modificar_transicion("q0", "0", "q1")
    assert modelo.obtener_transicion("q0", "0") == "q1"

    # Dejar celda vacía para eliminar la transición
    exito = controlador.al_modificar_transicion("q0", "0", "")
    assert exito is True
    assert modelo.obtener_transicion("q0", "0") is None
    assert vista.tabla_transiciones.tabla.item(0, 0).text() == ""


def test_tabla_eliminar_estado(aplicacion_qt):
    modelo = Automata(alfabeto=["0"])
    vista = VentanaPrincipal()
    controlador = ControladorAutomata(modelo=modelo, vista=vista)

    controlador.al_agregar_estado("q0", es_inicial=True, es_aceptacion=False)
    controlador.al_agregar_estado("q1", es_inicial=False, es_aceptacion=True)
    controlador.al_modificar_transicion("q0", "0", "q1")

    # Eliminar q1
    exito = controlador.al_eliminar_estado("q1")
    assert exito is True
    assert modelo.estados == ["q0"]
    assert modelo.obtener_transicion("q0", "0") is None
    assert vista.tabla_transiciones.tabla.rowCount() == 1


def test_tabla_senales_emision(aplicacion_qt):
    """Verifica que la interacción visual de la tabla emita las señales adecuadas."""
    modelo = Automata(alfabeto=["a"])
    vista = VentanaPrincipal()
    _controlador = ControladorAutomata(modelo=modelo, vista=vista)

    panel_tabla = vista.tabla_transiciones
    eventos_modificacion = []
    panel_tabla.transicion_modificada.connect(
        lambda o, s, d: eventos_modificacion.append((o, s, d))
    )

    # Agregar estado para tener una fila
    panel_tabla.campo_nombre_estado.setText("q0")
    panel_tabla._al_agregar_estado()

    # Editar celda programáticamente simulando usuario
    item = panel_tabla.tabla.item(0, 0)
    item.setText("q0")

    assert len(eventos_modificacion) == 1
    assert eventos_modificacion[0] == ("q0", "a", "q0")
