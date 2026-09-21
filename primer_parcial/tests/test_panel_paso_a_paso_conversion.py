from PyQt6.QtCore import QPoint, QPointF, Qt
from PyQt6.QtGui import QWheelEvent
from PyQt6.QtWidgets import QGraphicsItem, QGraphicsView, QPushButton

import pytest
from PyQt6.QtWidgets import QApplication

from src.controller.controlador_automata import ControladorAutomata
from src.model.automata_nfa import AutomataNFA
from src.model.conversion_nfa_dfa import ConvertidorSubconjuntos
from src.view.dialogo_conversion_dfa import DialogoConversionDFA
from src.view.lienzo_grafo import LienzoGrafo
from src.view.panel_paso_a_paso_conversion import PanelPasoAPasoConversion
from src.view.ventana_principal import VentanaPrincipal


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_lienzo_modo_estatico_bloquea_movimiento_y_zoom(qapp):
    """Verifica que un LienzoGrafo en modo estático impida mover nodos y hacer zoom."""
    lienzo = LienzoGrafo(solo_lectura=True, modo_estatico=True)
    nodo = lienzo.agregar_nodo_visual("K0", 0, 0, es_inicial=True)

    # El nodo no debe tener las banderas de movimiento ni selección ni aceptar clics de ratón
    assert not (nodo.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
    assert not (nodo.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
    assert nodo.acceptedMouseButtons() == Qt.MouseButton.NoButton

    # El lienzo debe estar en modo ScrollHandDrag para permitir arrastrar la vista
    assert lienzo.dragMode() == QGraphicsView.DragMode.ScrollHandDrag

    # Las operaciones de zoom deben ser ignoradas
    zoom_inicial = lienzo.factor_zoom
    lienzo.zoom_acercar()
    assert lienzo.factor_zoom == zoom_inicial
    lienzo.zoom_alejar()
    assert lienzo.factor_zoom == zoom_inicial

    # Simular evento de rueda del ratón
    evento_rueda = QWheelEvent(
        QPointF(100.0, 100.0),
        QPointF(100.0, 100.0),
        QPoint(0, 0),
        QPoint(0, 120),
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
        Qt.ScrollPhase.NoScrollPhase,
        False,
    )
    lienzo.wheelEvent(evento_rueda)
    assert lienzo.factor_zoom == zoom_inicial
    # La rueda no debe ser aceptada por el lienzo (no scrollea el cuadro)
    assert evento_rueda.isAccepted() is False


def test_dialogo_conversion_paso_5_sin_botones_zoom_ni_auto(qapp):
    """Verifica que en el diálogo de conversión el Paso 5 no contenga botones de zoom ni auto-distribuir."""
    nfa = AutomataNFA(alfabeto=["0", "1"], estados=["q0", "q1"], estado_inicial="q0")
    nfa.agregar_transicion("q0", "0", "q0")
    nfa.agregar_transicion("q0", "0", "q1")
    nfa.agregar_estado_aceptacion("q1")

    dialogo = DialogoConversionDFA(nfa)
    assert hasattr(dialogo, "lienzo_tabla3")
    assert dialogo.lienzo_tabla3.modo_estatico is True

    # Los nodos del grafo de la Tabla 3 no deben ser movibles
    for nodo in dialogo.lienzo_tabla3.nodos.values():
        assert not (nodo.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsMovable)

    # La pestaña de pasos 5 y 6 (índice 2) no debe contener botones de zoom
    pestana_5_6 = dialogo.pestanas.widget(2)
    textos_botones = [b.text() for b in pestana_5_6.findChildren(QPushButton)]
    assert "🔍+" not in textos_botones
    assert "🔍-" not in textos_botones
    assert "⟲ 100%" not in textos_botones
    assert "🔄 Auto-distribuir" not in textos_botones


def test_panel_paso_a_paso_construccion_continua(qapp):
    """Verifica que PanelPasoAPasoConversion renderice los 6 pasos continuos con grafo estático."""
    nfa = AutomataNFA(alfabeto=["a", "b"], estados=["q0", "q1"], estado_inicial="q0")
    nfa.agregar_transicion("q0", "a", "q0")
    nfa.agregar_transicion("q0", "a", "q1")
    nfa.agregar_estado_aceptacion("q1")

    resultado = ConvertidorSubconjuntos.convertir(nfa)
    panel = PanelPasoAPasoConversion()

    # Cargar resultado
    panel.cargar_resultado(resultado)
    assert panel.resultado is not None
    assert panel.lienzo_tabla3 is not None
    assert panel.lienzo_tabla3.modo_estatico is True

    # Comprobar presencia de nodos y marcado en rojo del inalcanzable K1
    assert "K0" in panel.lienzo_tabla3.nodos
    assert "K1" in panel.lienzo_tabla3.nodos
    assert panel.lienzo_tabla3.nodos["K0"].es_inalcanzable is False
    assert panel.lienzo_tabla3.nodos["K1"].es_inalcanzable is True
    assert not (panel.lienzo_tabla3.nodos["K0"].flags() & QGraphicsItem.GraphicsItemFlag.ItemIsMovable)


def test_integracion_ventana_principal_pestana_al_lado_matriz(qapp):
    """Verifica que la pestaña del paso a paso esté al lado de la matriz de transiciones (índice 2) y su flujo con el controlador."""
    modelo = AutomataNFA(alfabeto=["a", "b"], estados=["q0", "q1"], estado_inicial="q0")
    modelo.agregar_transicion("q0", "a", "q0")
    modelo.agregar_transicion("q0", "a", "q1")
    modelo.agregar_estado_aceptacion("q1")

    vista = VentanaPrincipal()
    controlador = ControladorAutomata(modelo=modelo, vista=vista)

    # Pestaña 1: Matriz de Transiciones, Pestaña 2: Paso a Paso
    assert "Matriz de Transiciones" in vista.pestanas_derecha.tabText(1)
    assert "Paso a Paso" in vista.pestanas_derecha.tabText(2)

    # Inicialmente la pestaña de paso a paso está oculta
    assert vista.pestanas_derecha.isTabVisible(2) is False
    assert vista.tabla_transiciones.boton_ver_paso_a_paso.isHidden() is True

    # Realizar conversión
    resultado = ConvertidorSubconjuntos.convertir(modelo)
    controlador.al_aplicar_conversion_dfa(resultado)

    # Ahora la pestaña y el botón deben ser visibles
    assert vista.pestanas_derecha.isTabVisible(2) is True
    assert vista.tabla_transiciones.boton_ver_paso_a_paso.isHidden() is False

    # Al hacer clic en el botón de ver paso a paso, cambia a la pestaña del paso a paso
    vista.tabla_transiciones.boton_ver_paso_a_paso.click()
    assert vista.pestanas_derecha.currentWidget() == vista.panel_paso_a_paso

    # Probar deshacer con Ctrl+Z: debe volver a ocultar el paso a paso
    controlador.deshacer()
    assert vista.pestanas_derecha.isTabVisible(2) is False
    assert vista.tabla_transiciones.boton_ver_paso_a_paso.isHidden() is True

    # Probar rehacer con Ctrl+Y: debe volver a mostrar el paso a paso
    controlador.rehacer()
    assert vista.pestanas_derecha.isTabVisible(2) is True
    assert vista.tabla_transiciones.boton_ver_paso_a_paso.isHidden() is False


def test_bloqueo_boton_conversion_al_dejar_de_ser_afn(qapp):
    """Verifica que si el autómata deja de ser AFN (se elimina la conexión múltiple), el botón de conversión se bloquea."""
    modelo = AutomataNFA(alfabeto=["0", "1"], estados=["q0", "q1"], estado_inicial="q0")
    modelo.agregar_transicion("q0", "0", "q0")
    modelo.agregar_transicion("q0", "0", "q1")  # No determinismo

    vista = VentanaPrincipal()
    controlador = ControladorAutomata(modelo=modelo, vista=vista)

    # Debe estar habilitado el botón de convertir a DFA
    assert vista.barra_herramientas_grafo.boton_convertir_dfa.isEnabled() is True
    assert vista.tabla_transiciones.boton_convertir_dfa.isEnabled() is True
    assert not vista.tabla_transiciones.boton_convertir_dfa.isHidden()

    # Eliminar la transición que causaba no-determinismo desde el grafo
    controlador.al_eliminar_transicion_desde_grafo("q0", "0", "q1")

    # Ahora solo queda q0 --0--> q0, no hay transiciones múltiples
    assert modelo.tiene_transiciones_multiples() is False
    assert modelo.es_no_deterministico() is False
    assert vista.barra_herramientas_grafo.boton_convertir_dfa.isEnabled() is False
    assert vista.tabla_transiciones.boton_convertir_dfa.isHidden() is True
    assert vista.tabla_transiciones.boton_convertir_dfa.isEnabled() is False


def test_aviso_sin_estado_final_en_evaluacion_cadena(qapp):
    """Verifica que si no hay estado final, se avisa en pantalla y se rechaza la lectura de la cadena."""
    modelo = AutomataNFA(alfabeto=["0", "1"], estados=["q0", "q1"], estado_inicial="q0")
    modelo.agregar_transicion("q0", "0", "q1")
    # Sin estados de aceptación
    assert len(modelo.estados_aceptacion) == 0

    vista = VentanaPrincipal()
    controlador = ControladorAutomata(modelo=modelo, vista=vista)

    # Intentar leer cadena sin estado final
    exito = controlador.al_solicitar_evaluacion("0")
    assert exito is False
    assert "ERROR DE ENTRADA" in vista.panel_simulacion.insignia_estado.text()
    assert "no tiene ningún estado final" in vista.panel_simulacion.etiqueta_detalle_paso.text()
    assert "Sin Estado Final" in vista.barra_estado.currentMessage()


def test_aviso_sin_estado_final_en_conversion_afd(qapp):
    """Verifica que si no hay estado final, se avisa en pantalla y se bloquea la conversión a AFD."""
    from src.model.automata import ErrorAutomata

    nfa = AutomataNFA(alfabeto=["0", "1"], estados=["q0", "q1"], estado_inicial="q0")
    nfa.agregar_transicion("q0", "0", "q0")
    nfa.agregar_transicion("q0", "0", "q1")  # No determinista
    # Sin estados de aceptación
    assert len(nfa.estados_aceptacion) == 0

    vista = VentanaPrincipal()
    controlador = ControladorAutomata(modelo=nfa, vista=vista)

    # Intentar convertir a AFD sin estado final
    controlador.al_solicitar_conversion_a_dfa()
    assert "Sin Estado Final" in vista.barra_estado.currentMessage()

    # El convertidor por subconjuntos debe lanzar ErrorAutomata explicativo
    with pytest.raises(ErrorAutomata, match="no tiene ningún estado final"):
        ConvertidorSubconjuntos.convertir(nfa)
