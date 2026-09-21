"""Pruebas unitarias para la conversión de AFN a AFD según el Método del Profesor (guiiadeconversionAFNtoAFN.md)."""

import pytest
from PyQt6.QtWidgets import QApplication

from src.controller.controlador_automata import ControladorAutomata
from src.model.automata import Automata
from src.model.automata_nfa import AutomataNFA
from src.model.conversion_nfa_dfa import (
    ConvertidorSubconjuntos,
    ResultadoConversionMetodoProfe,
)
from src.view.dialogo_conversion_dfa import DialogoConversionDFA
from src.view.ventana_principal import VentanaPrincipal


@pytest.fixture(scope="session")
def qapp():
    """Instancia global de QApplication para pruebas de interfaz gráfica."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_deteccion_no_deterministico():
    """Verifica que es_no_deterministico distinga correctamente entre DFA y AFN."""
    # 1. DFA estándar
    dfa = Automata(alfabeto=["a", "b"], estados=["q0", "q1"], estado_inicial="q0")
    dfa.agregar_transicion("q0", "a", "q1")
    dfa.agregar_transicion("q0", "b", "q0")
    dfa.agregar_transicion("q1", "a", "q1")
    dfa.agregar_transicion("q1", "b", "q0")
    assert dfa.es_no_deterministico() is False

    # 2. AFN con transiciones múltiples (|δ(q, a)| > 1)
    nfa = AutomataNFA(alfabeto=["0", "1"], estados=["q0", "q1", "q2"], estado_inicial="q0")
    nfa.agregar_transicion("q0", "0", "q0")
    nfa.agregar_transicion("q0", "0", "q1")
    assert nfa.tiene_transiciones_multiples() is True
    assert nfa.es_no_deterministico() is True


def test_metodo_profe_caso_guia_exacto():
    """Reproduce el ejercicio del apunte 'guiiadeconversionAFNtoAFN.md'.

    AFN:
    Q = {q0, q1, q2, q3}
    Sigma = {a, b}
    q0 = q0
    F = {q1}
    δ(q0, a) = {q1, q2}
    δ(q1, b) = {q0}
    δ(q2, b) = {q3}
    δ(q3, a) = {q0}
    """
    nfa = AutomataNFA(
        alfabeto=["a", "b"],
        estados=["q0", "q1", "q2", "q3"],
        estado_inicial="q0",
        estados_aceptacion=["q1"],
    )
    nfa.agregar_transicion("q0", "a", "q1")
    nfa.agregar_transicion("q0", "a", "q2")
    nfa.agregar_transicion("q1", "b", "q0")
    nfa.agregar_transicion("q2", "b", "q3")
    nfa.agregar_transicion("q3", "a", "q0")

    resultado = ConvertidorSubconjuntos.convertir(nfa)
    assert isinstance(resultado, ResultadoConversionMetodoProfe)

    # 1. Paso 1: Tabla 1 debe tener 4 filas (los 4 estados del AFN)
    assert len(resultado.tabla1_afn) == 4
    fila_q0 = next(f for f in resultado.tabla1_afn if f.estado == "q0")
    assert fila_q0.es_inicial is True
    assert fila_q0.transiciones["a"] == {"q1", "q2"}
    assert fila_q0.transiciones["b"] == set()

    # 2. Paso 2: Tabla 2 debe contener los estados simples y los compuestos generados
    subconjuntos_exp = [f.subconjunto for f in resultado.tabla2_expansion]
    assert {"q1", "q2"} in subconjuntos_exp

    # 3. Paso 3: Mapeo Kn
    # K0 = {q0}, K1 = {q1}, K2 = {q2}, K3 = {q3}, K4 = {q1, q2}
    dict_kn = {f.etiqueta: f.subconjunto for f in resultado.mapeo_kn}
    assert dict_kn["K0"] == {"q0"}
    assert dict_kn["K1"] == {"q1"}
    assert dict_kn["K2"] == {"q2"}
    assert dict_kn["K3"] == {"q3"}
    assert dict_kn["K4"] == {"q1", "q2"}

    # 4. Paso 4: Criterio de aceptación para estados finales
    # Como F = {q1}, K1 es final y K4 (que contiene q1) también es final
    fila_k0 = next(f for f in resultado.mapeo_kn if f.etiqueta == "K0")
    assert fila_k0.es_final is False

    fila_k1 = next(f for f in resultado.mapeo_kn if f.etiqueta == "K1")
    assert fila_k1.es_final is True
    assert "q1" in fila_k1.estados_finales_contenidos

    fila_k4 = next(f for f in resultado.mapeo_kn if f.etiqueta == "K4")
    assert fila_k4.es_final is True
    assert "q1" in fila_k4.estados_finales_contenidos

    # 5. Paso 6: Accesibilidad desde K0
    # K0 -> a -> K4 -> ...
    # K1 y K2 no tienen transiciones entrantes desde K0, por lo que quedan inalcanzables
    assert "K0" in resultado.accesibilidad.estados_alcanzables
    assert "K4" in resultado.accesibilidad.estados_alcanzables
    assert "K1" in resultado.accesibilidad.estados_inalcanzables
    assert "K2" in resultado.accesibilidad.estados_inalcanzables

    # 6. Tabla 4: AFD final simplificado
    estados_t4 = [f.etiqueta for f in resultado.tabla4_final]
    assert "K0" in estados_t4
    assert "K4" in estados_t4
    assert "K1" not in estados_t4
    assert "K2" not in estados_t4

    # El autómata dfa_final debe coincidir con los estados accesibles
    assert set(resultado.dfa_final.estados) == set(resultado.accesibilidad.estados_alcanzables)
    assert resultado.dfa_final.estado_inicial == "K0"


def test_dialogo_conversion_interfaz_pestanas(qapp):
    """Verifica que el diálogo renderice las 3 pestañas con las tablas del método del profesor."""
    nfa = AutomataNFA(
        alfabeto=["0", "1"],
        estados=["q0", "q1"],
        estado_inicial="q0",
        estados_aceptacion=["q1"],
    )
    nfa.agregar_transicion("q0", "0", "q0")
    nfa.agregar_transicion("q0", "0", "q1")

    dialogo = DialogoConversionDFA(nfa)
    assert dialogo.resultado is not None

    # Debe contener las 3 pestañas del método
    assert dialogo.pestanas.count() == 3
    assert "Pasos 1 y 2" in dialogo.pestanas.tabText(0)
    assert "Pasos 3 y 4" in dialogo.pestanas.tabText(1)
    assert "Pasos 5 y 6" in dialogo.pestanas.tabText(2)

    # Verificar emisión al hacer clic en aplicar
    recibido = []
    dialogo.aplicar_afd_solicitado.connect(lambda res: recibido.append(res))
    dialogo.boton_aplicar.click()
    assert len(recibido) == 1
    assert isinstance(recibido[0], ResultadoConversionMetodoProfe)


def test_controlador_flujo_conversion_completo_kn(qapp):
    """Verifica la sustitución del AFN por el AFD simplificado con nombres Kn en el controlador."""
    modelo = AutomataNFA(alfabeto=["a", "b"], estados=["q0", "q1"], estado_inicial="q0")
    modelo.agregar_transicion("q0", "a", "q0")
    modelo.agregar_transicion("q0", "a", "q1")
    modelo.agregar_estado_aceptacion("q1")

    vista = VentanaPrincipal()
    controlador = ControladorAutomata(modelo=modelo, vista=vista)

    # El botón de la barra de herramientas debe estar resaltado para AFN
    boton_toolbar = vista.barra_herramientas_grafo.boton_convertir_dfa
    assert "AFN" in boton_toolbar.text()

    # El botón de la tabla de transiciones debe estar visible (no oculto)
    assert vista.tabla_transiciones.boton_convertir_dfa.isHidden() is False

    # Ejecutar conversión aplicando el resultado del profesor
    resultado = ConvertidorSubconjuntos.convertir(modelo)
    controlador.al_aplicar_conversion_dfa(resultado)

    # Ahora el modelo debe ser un DFA determinista con la notación Kn
    assert isinstance(controlador.modelo, Automata)
    assert controlador.modelo.es_no_deterministico() is False
    assert "K0" in controlador.modelo.estados

    # El botón de la tabla ahora debe ocultarse porque ya es DFA
    assert vista.tabla_transiciones.boton_convertir_dfa.isHidden() is True


def test_dialogo_grafo_tabla3_estados_inalcanzables(qapp):
    """Verifica que el visor del grafo de la Tabla 3 en el diálogo marque en rojo los estados inalcanzables."""
    nfa = AutomataNFA(alfabeto=["0", "1"], estados=["q0", "q1"], estado_inicial="q0")
    nfa.agregar_transicion("q0", "0", "q0")
    nfa.agregar_transicion("q0", "0", "q1")
    nfa.agregar_estado_aceptacion("q1")

    dialogo = DialogoConversionDFA(nfa)
    assert hasattr(dialogo, "lienzo_tabla3")
    lienzo = dialogo.lienzo_tabla3
    assert lienzo.solo_lectura is True

    # Verificar presencia de nodos
    assert "K0" in lienzo.nodos
    assert "K1" in lienzo.nodos

    # K0 debe ser alcanzable (False) y K1 inalcanzable (True)
    assert lienzo.nodos["K0"].es_inalcanzable is False
    assert lienzo.nodos["K1"].es_inalcanzable is True

