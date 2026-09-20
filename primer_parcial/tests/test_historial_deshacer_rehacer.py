import os
from PyQt6.QtCore import QPointF
from PyQt6.QtWidgets import QApplication
import pytest

from src.controller.controlador_automata import ControladorAutomata
from src.model.automata import Automata
from src.model.automata_nfa import AutomataNFA
from src.model.conversion_nfa_dfa import ConvertidorSubconjuntos
from src.view.ventana_principal import VentanaPrincipal


@pytest.fixture(scope="session")
def aplicacion_qt():
    """Fixture que proporciona una instancia de QApplication para pruebas sin pantalla."""
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    app = QApplication.instance()
    if app is None:
        app = QApplication(["", "-platform", "offscreen"])
    yield app


@pytest.fixture
def entorno_app(aplicacion_qt):
    """Fixture que crea un modelo DFA inicial, la ventana principal y el controlador."""
    modelo = Automata()
    modelo.definir_alfabeto(["a", "b"])
    vista = VentanaPrincipal()
    controlador = ControladorAutomata(modelo=modelo, vista=vista)
    return modelo, vista, controlador


def test_estado_inicial_historial(entorno_app):
    """Verifica que al iniciar no hay acciones en la pila de deshacer ni rehacer."""
    _, vista, controlador = entorno_app

    assert not controlador.deshacer()
    assert not controlador.rehacer()
    assert not vista.barra_herramientas_grafo.boton_deshacer.isEnabled()
    assert not vista.barra_herramientas_grafo.boton_rehacer.isEnabled()


def test_deshacer_rehacer_estados_y_transiciones(entorno_app):
    """Verifica que agregar estados y transiciones se puede deshacer y rehacer."""
    _, vista, controlador = entorno_app

    # 1. Agregar estado q0
    controlador.al_agregar_estado("q0", es_inicial=True, es_aceptacion=False)
    assert "q0" in controlador.modelo.estados
    assert vista.barra_herramientas_grafo.boton_deshacer.isEnabled()
    assert not vista.barra_herramientas_grafo.boton_rehacer.isEnabled()

    # 2. Agregar estado q1
    controlador.al_agregar_estado("q1", es_inicial=False, es_aceptacion=True)
    assert "q1" in controlador.modelo.estados

    # 3. Modificar transición q0 --a--> q1
    controlador.al_modificar_transicion("q0", "a", "q1")
    assert controlador.modelo.obtener_transicion("q0", "a") == "q1"

    # 4. Deshacer la transición
    assert controlador.deshacer()
    assert controlador.modelo.obtener_transicion("q0", "a") is None
    assert vista.barra_herramientas_grafo.boton_rehacer.isEnabled()

    # 5. Deshacer el estado q1
    assert controlador.deshacer()
    assert "q1" not in controlador.modelo.estados
    assert "q0" in controlador.modelo.estados

    # 6. Rehacer el estado q1
    assert controlador.rehacer()
    assert "q1" in controlador.modelo.estados
    assert controlador.modelo.obtener_transicion("q0", "a") is None

    # 7. Rehacer la transición q0 --a--> q1
    assert controlador.rehacer()
    assert controlador.modelo.obtener_transicion("q0", "a") == "q1"
    assert not vista.barra_herramientas_grafo.boton_rehacer.isEnabled()


def test_deshacer_rehacer_conversion_afn_a_afd(entorno_app):
    """Verifica que convertir un AFN a AFD se puede deshacer recuperando el AFN intacto y rehacer."""
    _, vista, controlador = entorno_app

    # Configurar AFN no determinista
    controlador.convertir_modelo_a_nfa()
    controlador.al_agregar_estado("q0", es_inicial=True, es_aceptacion=False)
    controlador.al_agregar_estado("q1", es_inicial=False, es_aceptacion=True)
    controlador.al_modificar_transicion("q0", "a", "q0, q1")

    assert isinstance(controlador.modelo, AutomataNFA)
    assert controlador.modelo.es_no_deterministico()
    assert controlador.modelo.obtener_transiciones("q0", "a") == {"q0", "q1"}
    assert "Convertir AFN a AFD" in vista.barra_herramientas_grafo.boton_convertir_dfa.text()

    # Realizar conversión a AFD
    resultado = ConvertidorSubconjuntos.convertir(controlador.modelo)
    controlador.al_aplicar_conversion_dfa(resultado)

    # Debe ser AFD ahora
    assert not controlador.modelo.es_no_deterministico()
    assert "Convertir a DFA" in vista.barra_herramientas_grafo.boton_convertir_dfa.text()

    # Deshacer conversión (Ctrl+Z)
    assert controlador.deshacer()

    # El modelo debe volver a ser AutomataNFA con todas sus transiciones intactas
    assert isinstance(controlador.modelo, AutomataNFA)
    assert controlador.modelo.es_no_deterministico()
    assert controlador.modelo.obtener_transiciones("q0", "a") == {"q0", "q1"}
    assert "Convertir AFN a AFD" in vista.barra_herramientas_grafo.boton_convertir_dfa.text()

    # Rehacer la conversión (Ctrl+Y)
    assert controlador.rehacer()
    assert not controlador.modelo.es_no_deterministico()
    assert "Convertir a DFA" in vista.barra_herramientas_grafo.boton_convertir_dfa.text()


def test_deshacer_limpiar_grafo(entorno_app):
    """Verifica que limpiar el grafo se puede deshacer restaurando todos los estados y transiciones."""
    _, vista, controlador = entorno_app

    controlador.al_agregar_estado("q0", es_inicial=True, es_aceptacion=False)
    controlador.al_agregar_estado("q1", es_inicial=False, es_aceptacion=True)
    controlador.al_modificar_transicion("q0", "a", "q1")

    # Limpiar grafo completo
    controlador.al_limpiar_grafo_completo()
    assert len(controlador.modelo.estados) == 0

    # Deshacer limpieza
    assert controlador.deshacer()
    assert "q0" in controlador.modelo.estados
    assert "q1" in controlador.modelo.estados
    assert controlador.modelo.obtener_transicion("q0", "a") == "q1"


def test_deshacer_auto_organizar_nodos(entorno_app):
    """Verifica que auto-organizar restaura las posiciones visuales de los nodos en el lienzo."""
    _, vista, controlador = entorno_app

    controlador.al_agregar_estado("q0", es_inicial=True, es_aceptacion=False)
    nodo = vista.lienzo_grafo.nodos["q0"]
    nodo.setPos(QPointF(50.0, 75.0))

    # Auto-distribuir nodos
    controlador.al_auto_organizar_grafo()
    pos_auto = nodo.pos()

    # Deshacer auto-distribución
    assert controlador.deshacer()
    nodo_restaurado = vista.lienzo_grafo.nodos["q0"]
    assert abs(nodo_restaurado.pos().x() - 50.0) < 1.0
    assert abs(nodo_restaurado.pos().y() - 75.0) < 1.0


def test_nueva_accion_limpia_pila_rehacer(entorno_app):
    """Verifica que realizar una nueva acción descarta el historial de rehacer pendiente."""
    _, vista, controlador = entorno_app

    controlador.al_agregar_estado("q0", es_inicial=True, es_aceptacion=False)
    controlador.al_agregar_estado("q1", es_inicial=False, es_aceptacion=True)

    # Deshacer q1 -> q1 no existe, rehacer disponible
    controlador.deshacer()
    assert "q1" not in controlador.modelo.estados
    assert vista.barra_herramientas_grafo.boton_rehacer.isEnabled()

    # Realizar nueva acción: agregar q2 en lugar de rehacer q1
    controlador.al_agregar_estado("q2", es_inicial=False, es_aceptacion=False)
    assert "q2" in controlador.modelo.estados

    # La pila de rehacer debió limpiarse
    assert not vista.barra_herramientas_grafo.boton_rehacer.isEnabled()
    assert not controlador.rehacer()


def test_limite_maximo_historial_deshacer(entorno_app):
    """Verifica que el historial no crece indefinidamente y se limita a 50 snapshots."""
    _, _, controlador = entorno_app

    for i in range(60):
        controlador.registrar_snapshot(f"Snapshot {i}")

    assert len(controlador._historial_deshacer) == 50

