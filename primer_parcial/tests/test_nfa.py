"""Pruebas unitarias para el modelo NFA, traza ramificada y soporte MVC (Phase 5)."""

import pytest
from PyQt6.QtWidgets import QApplication

from src.model.alfabeto import Alfabeto, ErrorAlfabeto
from src.model.automata import Automata, ErrorAutomata
from src.model.automata_nfa import (
    AutomataNFA,
    PasoRamaNFA,
    RamaTrazaNFA,
    ResultadoTrazaNFA,
)
from src.view.lienzo_cinta import LienzoCinta
from src.view.ventana_principal import VentanaPrincipal
from src.controller.controlador_automata import ControladorAutomata


@pytest.fixture(scope="session")
def qapp():
    """Provee la instancia de QApplication para pruebas de interfaz gráfica."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


# ==============================================================================
# Pruebas del Modelo AutomataNFA
# ==============================================================================

def test_creacion_nfa_y_estados():
    """Verifica la creación básica de un NFA, sus estados y atributos formales."""
    nfa = AutomataNFA(
        alfabeto=["0", "1"],
        estados=["q0", "q1", "q2"],
        estado_inicial="q0",
        estados_aceptacion=["q2"],
    )

    assert nfa.estados == ["q0", "q1", "q2"]
    assert nfa.estado_inicial == "q0"
    assert nfa.estados_aceptacion == {"q2"}
    assert nfa.alfabeto.simbolos == ["0", "1"]
    assert nfa.es_valido()


def test_transiciones_no_deterministas_multiples():
    """Verifica que delta(q, a) soporte múltiples estados destino en NFA."""
    nfa = AutomataNFA(alfabeto=["a", "b"], estados=["q0", "q1", "q2"], estado_inicial="q0")

    # Agregar dos transiciones con el mismo símbolo 'a' desde 'q0'
    nfa.agregar_transicion("q0", "a", "q0")
    nfa.agregar_transicion("q0", "a", "q1")

    destinos = nfa.obtener_transiciones("q0", "a")
    assert destinos == {"q0", "q1"}

    # Transición no existente retorna conjunto vacío ∅
    assert nfa.obtener_transiciones("q0", "b") == set()

    # Copia de transiciones
    todas = nfa.transiciones
    assert todas["q0"]["a"] == {"q0", "q1"}


def test_agregar_transiciones_multiples_metodo():
    """Verifica el método helper agregar_transiciones_multiples."""
    nfa = AutomataNFA(alfabeto=["x"], estados=["q0", "q1", "q2", "q3"], estado_inicial="q0")
    nfa.agregar_transiciones_multiples("q0", "x", ["q1", "q2", "q3"])

    assert nfa.obtener_transiciones("q0", "x") == {"q1", "q2", "q3"}


def test_eliminar_transicion_nfa():
    """Verifica la eliminación de un destino puntual o de todo el símbolo."""
    nfa = AutomataNFA(alfabeto=["a"], estados=["q0", "q1", "q2"], estado_inicial="q0")
    nfa.agregar_transiciones_multiples("q0", "a", ["q1", "q2"])

    # Eliminar únicamente q1
    nfa.eliminar_transicion("q0", "a", destino="q1")
    assert nfa.obtener_transiciones("q0", "a") == {"q2"}

    # Eliminar toda la entrada del símbolo 'a'
    nfa.eliminar_transicion("q0", "a")
    assert nfa.obtener_transiciones("q0", "a") == set()


def test_eliminar_estado_en_nfa():
    """Verifica que eliminar un estado en NFA limpie transiciones salientes y entrantes."""
    nfa = AutomataNFA(alfabeto=["0"], estados=["q0", "q1", "q2"], estado_inicial="q0")
    nfa.agregar_transicion("q0", "0", "q1")
    nfa.agregar_transicion("q1", "0", "q2")

    nfa.eliminar_estado("q1")
    assert "q1" not in nfa.estados
    assert nfa.obtener_transiciones("q0", "0") == set()
    assert "q1" not in nfa.transiciones


def test_definir_alfabeto_purga_transiciones_nfa():
    """Verifica que al redefinir el alfabeto se eliminen transiciones con símbolos obsoletos."""
    nfa = AutomataNFA(alfabeto=["0", "1"], estados=["q0", "q1"], estado_inicial="q0")
    nfa.agregar_transicion("q0", "1", "q1")

    nfa.definir_alfabeto(["0"])  # Símbolo '1' ya no pertenece
    assert nfa.obtener_transiciones("q0", "1") == set()


# ==============================================================================
# Pruebas de Conversión DFA a NFA
# ==============================================================================

def test_conversion_dfa_a_nfa_equivalente():
    """Verifica que un DFA pueda convertirse a un NFA manteniendo su lenguaje."""
    dfa = Automata(
        alfabeto=["0", "1"],
        estados=["p0", "p1"],
        estado_inicial="p0",
        estados_aceptacion=["p1"],
    )
    dfa.agregar_transicion("p0", "0", "p0")
    dfa.agregar_transicion("p0", "1", "p1")
    dfa.agregar_transicion("p1", "0", "p0")
    dfa.agregar_transicion("p1", "1", "p1")

    nfa = dfa.convertir_a_nfa()
    assert isinstance(nfa, AutomataNFA)
    assert nfa.estados == dfa.estados
    assert nfa.estado_inicial == "p0"
    assert nfa.estados_aceptacion == {"p1"}
    assert nfa.obtener_transiciones("p0", "1") == {"p1"}
    assert nfa.obtener_transiciones("p0", "0") == {"p0"}

    # Probar evaluación de cadenas equivalentes
    cadenas_prueba = ["1", "01", "111", "00", "10", ""]
    for cad in cadenas_prueba:
        assert nfa.evaluar_cadena(cad) == dfa.evaluar_cadena(cad)


def test_metodo_desde_dfa():
    """Verifica el método de clase AutomataNFA.desde_dfa."""
    dfa = Automata(alfabeto=["a"], estados=["q0"], estado_inicial="q0", estados_aceptacion=["q0"])
    dfa.agregar_transicion("q0", "a", "q0")

    nfa = AutomataNFA.desde_dfa(dfa)
    assert isinstance(nfa, AutomataNFA)
    assert nfa.obtener_transiciones("q0", "a") == {"q0"}
    assert nfa.evaluar_cadena("a") is True


# ==============================================================================
# Pruebas de Evaluación de Cadenas y Traza Ramificada (NFA)
# ==============================================================================

def test_nfa_evaluacion_caminos_multiples_subcadena():
    """NFA clásico que reconoce palabras con la subcadena '01'."""
    nfa = AutomataNFA(
        alfabeto=["0", "1"],
        estados=["q0", "q1", "q2"],
        estado_inicial="q0",
        estados_aceptacion=["q2"],
    )
    # q0 con '0' o '1' hace bucle en q0, pero ante '0' también puede pasar a q1 (no-determinismo)
    nfa.agregar_transicion("q0", "0", "q0")
    nfa.agregar_transicion("q0", "0", "q1")
    nfa.agregar_transicion("q0", "1", "q0")

    # q1 con '1' va a q2 (estado de aceptación)
    nfa.agregar_transicion("q1", "1", "q2")

    # q2 con cualquier símbolo se queda en q2
    nfa.agregar_transicion("q2", "0", "q2")
    nfa.agregar_transicion("q2", "1", "q2")

    # Cadenas que contienen '01' -> Aceptadas
    assert nfa.evaluar_cadena("01") is True
    assert nfa.evaluar_cadena("001") is True
    assert nfa.evaluar_cadena("11010") is True

    # Cadenas que NO contienen '01' -> Rechazadas
    assert nfa.evaluar_cadena("0") is False
    assert nfa.evaluar_cadena("000") is False
    assert nfa.evaluar_cadena("111") is False


def test_nfa_trazas_ramificadas_y_ramas_abortadas_en_vacio():
    """Verifica que ramas sin transición se trunquen prematuramente ante ∅."""
    nfa = AutomataNFA(
        alfabeto=["a", "b"],
        estados=["q0", "q1", "q2"],
        estado_inicial="q0",
        estados_aceptacion=["q2"],
    )
    # q0 con 'a' bifurca en q0 y q1
    nfa.agregar_transicion("q0", "a", "q0")
    nfa.agregar_transicion("q0", "a", "q1")

    # q1 únicamente tiene transición con 'b' hacia q2
    nfa.agregar_transicion("q1", "b", "q2")
    # q1 NO tiene transición con 'a' (delta(q1, a) = ∅)

    # Evaluar cadena 'aa'
    traza = nfa.generar_traza("aa")
    assert isinstance(traza, ResultadoTrazaNFA)
    assert traza.cadena_entrada == "aa"
    assert traza.total_pasos == 3  # pasos 0, 1 y delimitador 2 (≡)

    # Debe haber ramas abortadas
    abortadas = traza.ramas_abortadas
    assert len(abortadas) >= 1

    rama_abortada = abortadas[0]
    assert rama_abortada.es_abortada is True
    assert rama_abortada.indice_aborto == 1  # se abortó en el segundo símbolo 'a'
    assert rama_abortada.simbolo_aborto == "a"
    assert "∅" in str(rama_abortada.motivo_aborto)

    # Verificamos ramas totales
    assert len(traza.ramas) >= 2


def test_nfa_cadena_vacia():
    """Verifica la evaluación de la cadena vacía en un NFA."""
    nfa_no_acepta_vacia = AutomataNFA(
        alfabeto=["0", "1"],
        estados=["q0", "q1"],
        estado_inicial="q0",
        estados_aceptacion=["q1"],
    )
    assert nfa_no_acepta_vacia.evaluar_cadena("") is False

    nfa_acepta_vacia = AutomataNFA(
        alfabeto=["0", "1"],
        estados=["q0", "q1"],
        estado_inicial="q0",
        estados_aceptacion=["q0"],
    )
    assert nfa_acepta_vacia.evaluar_cadena("") is True


def test_nfa_rechazo_cuando_todas_ramas_fallan():
    """Verifica que una cadena sea rechazada cuando todas las ramas se extinguen o no aceptan."""
    nfa = AutomataNFA(
        alfabeto=["x", "y"],
        estados=["q0", "q1"],
        estado_inicial="q0",
        estados_aceptacion=["q1"],
    )
    nfa.agregar_transicion("q0", "x", "q0")

    traza = nfa.generar_traza("xy")
    assert traza.aceptada is False
    assert len(traza.ramas_aceptadas) == 0
    # En 'y' la única rama aborta por ∅
    assert len(traza.ramas_abortadas) >= 1


# ==============================================================================
# Pruebas de Integración con Vista (LienzoCinta) y Controlador
# ==============================================================================

def test_lienzo_cinta_renderiza_traza_nfa(qapp):
    """Verifica que LienzoCinta dibuje adecuadamente una traza NFA sin errores."""
    nfa = AutomataNFA(
        alfabeto=["0", "1"],
        estados=["q0", "q1"],
        estado_inicial="q0",
        estados_aceptacion=["q1"],
    )
    nfa.agregar_transicion("q0", "0", "q0")
    nfa.agregar_transicion("q0", "0", "q1")

    traza = nfa.generar_traza("0")
    lienzo = LienzoCinta()
    lienzo.establecer_traza(traza, paso_actual=1)

    items = lienzo._escena.items()
    assert len(items) > 0

    # Cambiar paso al delimitador ≡
    lienzo.establecer_traza(traza, paso_actual=1)
    assert len(lienzo._escena.items()) > 0


def test_controlador_con_nfa_simulacion_paso_a_paso(qapp):
    """Verifica el flujo completo del controlador con un modelo AutomataNFA."""
    nfa = AutomataNFA(
        alfabeto=["a", "b"],
        estados=["q0", "q1"],
        estado_inicial="q0",
        estados_aceptacion=["q1"],
    )
    nfa.agregar_transicion("q0", "a", "q0")
    nfa.agregar_transicion("q0", "a", "q1")

    vista = VentanaPrincipal()
    controlador = ControladorAutomata(modelo=nfa, vista=vista)

    # Iniciar simulación de 'a'
    exito = controlador.al_solicitar_evaluacion("a")
    assert exito is True
    assert controlador._paso_actual == 0
    assert isinstance(controlador._traza_actual, ResultadoTrazaNFA)

    # Avanzar al paso 1 (celda ≡)
    controlador.al_avanzar_paso()
    assert controlador._paso_actual == 1

    # Retroceder al paso 0
    controlador.al_retroceder_paso()
    assert controlador._paso_actual == 0

    # Ejecutar todo
    controlador.al_ejecutar_todo()
    assert controlador._paso_actual == 1

    # Reiniciar simulación
    controlador.al_reiniciar_simulacion()
    assert controlador._paso_actual == 0


def test_controlador_edicion_transicion_nfa(qapp):
    """Verifica la edición de celdas con transiciones múltiples en NFA desde el controlador."""
    nfa = AutomataNFA(
        alfabeto=["0", "1"],
        estados=["q0", "q1", "q2"],
        estado_inicial="q0",
    )
    vista = VentanaPrincipal()
    controlador = ControladorAutomata(modelo=nfa, vista=vista)

    # Editar celda para asignar múltiples destinos "q1, q2"
    resultado = controlador.al_modificar_transicion("q0", "0", "q1, q2")
    assert resultado is True
    assert nfa.obtener_transiciones("q0", "0") == {"q1", "q2"}

    # Intentar asignar un estado inexistente
    resultado_invalido = controlador.al_modificar_transicion("q0", "0", "q1, q_fantasma")
    assert resultado_invalido is False
    assert nfa.obtener_transiciones("q0", "0") == {"q1", "q2"}


def test_controlador_convertir_modelo_a_nfa(qapp):
    """Verifica que el controlador pueda convertir un DFA a NFA dinámicamente."""
    dfa = Automata(
        alfabeto=["x"],
        estados=["s0", "s1"],
        estado_inicial="s0",
        estados_aceptacion=["s1"],
    )
    dfa.agregar_transicion("s0", "x", "s1")

    vista = VentanaPrincipal()
    controlador = ControladorAutomata(modelo=dfa, vista=vista)

    assert not isinstance(controlador.modelo, AutomataNFA)

    nfa_convertido = controlador.convertir_modelo_a_nfa()
    assert isinstance(nfa_convertido, AutomataNFA)
    assert isinstance(controlador.modelo, AutomataNFA)
    assert controlador.modelo.obtener_transiciones("s0", "x") == {"s1"}
