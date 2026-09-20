"""Pruebas unitarias para los modelos Automata y Alfabeto."""

import pytest
from src.model.alfabeto import Alfabeto, ErrorAlfabeto
from src.model.automata import Automata, ErrorAutomata, PasoTraza, ResultadoTraza


# ==============================================================================
# Pruebas del Alfabeto
# ==============================================================================

def test_creacion_alfabeto():
    alfabeto = Alfabeto(["0", "1"])
    assert alfabeto.simbolos == ["0", "1"]
    assert len(alfabeto) == 2
    assert "0" in alfabeto
    assert "1" in alfabeto
    assert "2" not in alfabeto


def test_alfabeto_rechaza_simbolo_vacio():
    alfabeto = Alfabeto()
    with pytest.raises(ErrorAlfabeto, match="no puede ser una cadena vacía"):
        alfabeto.agregar_simbolo("")


def test_alfabeto_unicidad_y_orden():
    alfabeto = Alfabeto(["a", "b", "a", "c", "b"])
    assert alfabeto.simbolos == ["a", "b", "c"]
    assert len(alfabeto) == 3


def test_alfabeto_eliminar_simbolo():
    alfabeto = Alfabeto(["a", "b"])
    alfabeto.eliminar_simbolo("a")
    assert "a" not in alfabeto
    assert alfabeto.simbolos == ["b"]
    with pytest.raises(ErrorAlfabeto):
        alfabeto.eliminar_simbolo("no_existente")


def test_alfabeto_validacion_cadenas():
    alfabeto = Alfabeto(["0", "1"])
    assert alfabeto.validar_cadena("") is True
    assert alfabeto.validar_cadena("01011") is True
    assert alfabeto.validar_cadena("0102") is False

    alfabeto.verificar_cadena("0011")
    with pytest.raises(ErrorAlfabeto, match="Símbolo no válido '2'"):
        alfabeto.verificar_cadena("0012")


# ==============================================================================
# Pruebas de Estructura y Estados del Autómata
# ==============================================================================

def test_automata_gestion_estados():
    dfa = Automata(alfabeto=["0", "1"])
    dfa.agregar_estado("q0", es_inicial=True)
    dfa.agregar_estado("q1", es_aceptacion=True)

    assert dfa.estados == ["q0", "q1"]
    assert dfa.estado_inicial == "q0"
    assert dfa.estados_aceptacion == {"q1"}

    dfa.eliminar_estado("q1")
    assert dfa.estados == ["q0"]
    assert dfa.estados_aceptacion == set()


def test_automata_gestion_transiciones():
    dfa = Automata(alfabeto=["0", "1"], estados=["q0", "q1"], estado_inicial="q0")
    dfa.agregar_transicion("q0", "0", "q1")
    dfa.agregar_transicion("q0", "1", "q0")

    assert dfa.obtener_transicion("q0", "0") == "q1"
    assert dfa.obtener_transicion("q0", "1") == "q0"
    assert dfa.obtener_transicion("q1", "0") is None

    dfa.eliminar_transicion("q0", "0")
    assert dfa.obtener_transicion("q0", "0") is None


def test_automata_transiciones_invalidas():
    dfa = Automata(alfabeto=["0", "1"], estados=["q0"])

    # Estado destino no está en Q
    with pytest.raises(ErrorAutomata, match="El estado destino"):
        dfa.agregar_transicion("q0", "0", "q1")

    # Estado origen no está en Q
    with pytest.raises(ErrorAutomata, match="El estado origen"):
        dfa.agregar_transicion("q1", "0", "q0")

    # Símbolo no está en Sigma
    with pytest.raises(ErrorAutomata, match="no pertenece al alfabeto"):
        dfa.agregar_transicion("q0", "2", "q0")


def test_automata_eliminar_estado_limpia_transiciones():
    dfa = Automata(
        alfabeto=["a"],
        estados=["q0", "q1", "q2"],
        estado_inicial="q0"
    )
    dfa.agregar_transicion("q0", "a", "q1")
    dfa.agregar_transicion("q1", "a", "q2")

    dfa.eliminar_estado("q1")
    assert dfa.obtener_transicion("q0", "a") is None
    assert dfa.obtener_transiciones_desde("q1") == {}


def test_automata_validacion():
    # Autómata vacío
    dfa = Automata()
    assert not dfa.es_valido()
    assert "El autómata no tiene estados definidos." in dfa.validar()

    # Autómata consistente
    dfa.alfabeto.agregar_simbolo("a")
    dfa.agregar_estado("q0", es_inicial=True, es_aceptacion=True)
    dfa.agregar_transicion("q0", "a", "q0")
    assert dfa.es_valido()
    assert dfa.validar() == []
    assert dfa.es_completo()


# ==============================================================================
# Pruebas de Evaluación de Cadenas DFA
# ==============================================================================

def test_dfa_ceros_pares():
    """Lenguaje: Cadenas binarias con un número par de '0's."""
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

    assert dfa.es_completo()

    # Epsilon (cadena vacía tiene 0 ceros, 0 es par)
    assert dfa.evaluar_cadena("") is True
    # Cadenas aceptadas
    assert dfa.evaluar_cadena("1") is True
    assert dfa.evaluar_cadena("11") is True
    assert dfa.evaluar_cadena("00") is True
    assert dfa.evaluar_cadena("10101") is True
    assert dfa.evaluar_cadena("0000") is True
    assert dfa.evaluar_cadena("1001001") is True

    # Cadenas rechazadas
    assert dfa.evaluar_cadena("0") is False
    assert dfa.evaluar_cadena("10") is False
    assert dfa.evaluar_cadena("000") is False
    assert dfa.evaluar_cadena("101") is False


def test_dfa_termina_en_ab():
    """Lenguaje: Cadenas sobre {a, b} que terminan en 'ab'."""
    dfa = Automata(
        alfabeto=["a", "b"],
        estados=["q0", "q1", "q2"],
        estado_inicial="q0",
        estados_aceptacion=["q2"],
    )
    # q0: estado base / último no fue 'a'
    dfa.agregar_transicion("q0", "a", "q1")
    dfa.agregar_transicion("q0", "b", "q0")
    # q1: último fue 'a'
    dfa.agregar_transicion("q1", "a", "q1")
    dfa.agregar_transicion("q1", "b", "q2")
    # q2: terminó en 'ab'
    dfa.agregar_transicion("q2", "a", "q1")
    dfa.agregar_transicion("q2", "b", "q0")

    assert dfa.evaluar_cadena("") is False
    assert dfa.evaluar_cadena("a") is False
    assert dfa.evaluar_cadena("b") is False
    assert dfa.evaluar_cadena("ab") is True
    assert dfa.evaluar_cadena("aab") is True
    assert dfa.evaluar_cadena("bab") is True
    assert dfa.evaluar_cadena("aba") is False
    assert dfa.evaluar_cadena("abb") is False
    assert dfa.evaluar_cadena("abab") is True


def test_dfa_simbolo_invalido_lanza_error_alfabeto():
    dfa = Automata(
        alfabeto=["0", "1"],
        estados=["q0"],
        estado_inicial="q0",
        estados_aceptacion=["q0"],
    )
    dfa.agregar_transicion("q0", "0", "q0")
    dfa.agregar_transicion("q0", "1", "q0")

    with pytest.raises(ErrorAlfabeto, match="Símbolo no válido 'x'"):
        dfa.evaluar_cadena("010x1")


def test_dfa_sin_estado_inicial_lanza_error_automata():
    dfa = Automata(alfabeto=["0", "1"], estados=["q0"])
    with pytest.raises(ErrorAutomata, match="el estado inicial q0 no está definido"):
        dfa.evaluar_cadena("0")


# ==============================================================================
# Pruebas del Motor de Traza (para la visualización de Cinta y Control)
# ==============================================================================

def test_dfa_generar_traza_detalles():
    dfa = Automata(
        alfabeto=["a", "b"],
        estados=["q0", "q1"],
        estado_inicial="q0",
        estados_aceptacion=["q1"],
    )
    dfa.agregar_transicion("q0", "a", "q1")
    dfa.agregar_transicion("q1", "b", "q0")

    traza = dfa.generar_traza("ab")
    assert traza.aceptada is False
    assert traza.cadena_entrada == "ab"
    assert traza.camino == ["q0", "q1", "q0"]
    assert traza.estado_final == "q0"

    # Verificación de pasos individuales
    # Paso 0: en q0, lee 'a', pasa a q1
    assert traza.pasos[0].indice_paso == 0
    assert traza.pasos[0].estado_actual == "q0"
    assert traza.pasos[0].simbolo == "a"
    assert traza.pasos[0].estado_siguiente == "q1"
    assert traza.pasos[0].es_aceptacion is False

    # Paso 1: en q1, lee 'b', pasa a q0
    assert traza.pasos[1].indice_paso == 1
    assert traza.pasos[1].estado_actual == "q1"
    assert traza.pasos[1].simbolo == "b"
    assert traza.pasos[1].estado_siguiente == "q0"
    assert traza.pasos[1].es_aceptacion is True

    # Paso 2: en q0, delimitador de fin (simbolo=None)
    assert traza.pasos[2].indice_paso == 2
    assert traza.pasos[2].estado_actual == "q0"
    assert traza.pasos[2].simbolo is None
    assert traza.pasos[2].es_aceptacion is False


def test_dfa_generar_traza_transicion_indefinida():
    dfa = Automata(
        alfabeto=["0", "1"],
        estados=["q0", "q1"],
        estado_inicial="q0",
        estados_aceptacion=["q1"],
    )
    # Solo se define transición con '0', '1' queda indefinida
    dfa.agregar_transicion("q0", "0", "q1")

    traza = dfa.generar_traza("01")
    assert traza.aceptada is False
    assert "Transición indefinida" in traza.motivo_rechazo
    assert traza.estado_final is None
    assert traza.camino == ["q0", "q1"]


# ==============================================================================
# Pruebas de Serialización (Diccionario / JSON)
# ==============================================================================

def test_automata_serializacion_diccionario():
    dfa = Automata(
        alfabeto=["0", "1"],
        estados=["q0", "q1"],
        estado_inicial="q0",
        estados_aceptacion=["q1"],
    )
    dfa.agregar_transicion("q0", "1", "q1")
    dfa.agregar_transicion("q1", "0", "q0")

    datos = dfa.a_diccionario()
    assert datos["alfabeto"] == ["0", "1"]
    assert datos["estados"] == ["q0", "q1"]
    assert datos["estado_inicial"] == "q0"
    assert datos["estados_aceptacion"] == ["q1"]
    assert datos["transiciones"] == {"q0": {"1": "q1"}, "q1": {"0": "q0"}}

    reconstruido = Automata.desde_diccionario(datos)
    assert reconstruido.alfabeto.simbolos == ["0", "1"]
    assert reconstruido.estados == ["q0", "q1"]
    assert reconstruido.estado_inicial == "q0"
    assert reconstruido.estados_aceptacion == {"q1"}
    assert reconstruido.evaluar_cadena("1") is True
    assert reconstruido.evaluar_cadena("10") is False
    assert reconstruido.evaluar_cadena("101") is True
