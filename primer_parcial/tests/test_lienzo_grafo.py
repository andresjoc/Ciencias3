"""Pruebas unitarias para el editor de grafos interactivo estilo Draw.io (LienzoGrafo e Items)."""

import pytest
from PyQt6.QtWidgets import QApplication

from src.model.automata import Automata
from src.view.items_grafo import ItemAristaTransicion, ItemNodoEstado
from src.view.lienzo_grafo import LienzoGrafo
from src.view.ventana_principal import VentanaPrincipal
from src.controller.controlador_automata import ControladorAutomata


@pytest.fixture(scope="session")
def qapp():
    """Provee la instancia de QApplication para pruebas de interfaz gráfica."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_creacion_lienzo_grafo(qapp):
    """Verifica que LienzoGrafo se inicialice correctamente con su escena y modo selección."""
    lienzo = LienzoGrafo()
    assert lienzo.modo_actual == LienzoGrafo.MODO_SELECCION
    assert len(lienzo.nodos) == 0
    assert len(lienzo.aristas) == 0


def test_agregar_nodos_visuales(qapp):
    """Verifica la adición de nodos visuales con estados iniciales y de aceptación."""
    lienzo = LienzoGrafo()

    nodo0 = lienzo.agregar_nodo_visual("q0", 50, 100, es_inicial=True, es_aceptacion=False)
    nodo1 = lienzo.agregar_nodo_visual("q1", 200, 100, es_inicial=False, es_aceptacion=True)

    assert len(lienzo.nodos) == 2
    assert nodo0.nombre == "q0"
    assert nodo0.es_inicial is True
    assert nodo0.es_aceptacion is False
    assert nodo0.pos().x() == 50
    assert nodo0.pos().y() == 100

    assert nodo1.nombre == "q1"
    assert nodo1.es_inicial is False
    assert nodo1.es_aceptacion is True


def test_conectar_aristas_transicion_normal(qapp):
    """Verifica la creación de una arista dirigida entre dos estados distintos."""
    lienzo = LienzoGrafo()
    lienzo.agregar_nodo_visual("q0", 0, 0)
    lienzo.agregar_nodo_visual("q1", 100, 0)

    arista = lienzo.agregar_arista_visual("q0", "a", "q1")
    assert arista is not None
    assert arista.nodo_origen.nombre == "q0"
    assert arista.nodo_destino.nombre == "q1"
    assert arista.simbolos == {"a"}
    assert not arista._es_bucle

    # Agregar otro símbolo a la misma conexión
    lienzo.agregar_arista_visual("q0", "b", "q1")
    assert arista.simbolos == {"a", "b"}


def test_arista_bucle_self_loop(qapp):
    """Verifica la creación de un lazo o bucle sobre el mismo estado."""
    lienzo = LienzoGrafo()
    lienzo.agregar_nodo_visual("q0", 0, 0)

    arista_bucle = lienzo.agregar_arista_visual("q0", "0", "q0")
    assert arista_bucle is not None
    assert arista_bucle._es_bucle is True
    assert arista_bucle.simbolos == {"0"}


def test_cambio_de_modos_lienzo(qapp):
    """Verifica que el cambio de herramientas configure adecuadamente el cursor y modo."""
    lienzo = LienzoGrafo()

    lienzo.establecer_modo(LienzoGrafo.MODO_CREAR_ESTADO)
    assert lienzo.modo_actual == LienzoGrafo.MODO_CREAR_ESTADO

    lienzo.establecer_modo(LienzoGrafo.MODO_CONECTAR)
    assert lienzo.modo_actual == LienzoGrafo.MODO_CONECTAR

    lienzo.establecer_modo(LienzoGrafo.MODO_BORRAR)
    assert lienzo.modo_actual == LienzoGrafo.MODO_BORRAR

    lienzo.establecer_modo(LienzoGrafo.MODO_SELECCION)
    assert lienzo.modo_actual == LienzoGrafo.MODO_SELECCION


def test_eliminar_nodo_y_sus_aristas(qapp):
    """Verifica que al eliminar un nodo se remuevan automáticamente sus aristas conectadas."""
    lienzo = LienzoGrafo()
    nodo0 = lienzo.agregar_nodo_visual("q0", 0, 0)
    lienzo.agregar_nodo_visual("q1", 100, 0)
    lienzo.agregar_arista_visual("q0", "a", "q1")

    assert len(lienzo.nodos) == 2
    assert len(lienzo.aristas) == 1

    lienzo.eliminar_nodo(nodo0)
    assert len(lienzo.nodos) == 1
    assert len(lienzo.aristas) == 0
    assert "q0" not in lienzo.nodos


def test_auto_organizar_nodos(qapp):
    """Verifica que el método de auto-organización distribuya los nodos sin errores."""
    lienzo = LienzoGrafo()
    for i in range(4):
        lienzo.agregar_nodo_visual(f"q{i}", 0, 0)

    lienzo.auto_organizar_nodos()
    # Las posiciones deben haber cambiado respecto a (0, 0)
    posiciones = [nodo.pos() for nodo in lienzo.nodos.values()]
    assert any(p.x() != 0 or p.y() != 0 for p in posiciones)


def test_sincronizar_desde_modelo(qapp):
    """Verifica que el lienzo se pueble automáticamente desde los datos de un modelo."""
    lienzo = LienzoGrafo()
    estados = ["q0", "q1", "q2"]
    transiciones = {
        "q0": {"a": "q1", "b": "q0"},
        "q1": {"a": "q2"},
        "q2": {},
    }
    inicial = "q0"
    aceptacion = {"q2"}

    lienzo.sincronizar_desde_modelo(estados, transiciones, inicial, aceptacion)

    assert len(lienzo.nodos) == 3
    assert lienzo.nodos["q0"].es_inicial is True
    assert lienzo.nodos["q2"].es_aceptacion is True
    assert len(lienzo.aristas) == 3  # q0->q1, q0->q0 (bucle), q1->q2


def test_integracion_controlador_con_lienzo_grafo(qapp):
    """Verifica la comunicación bidireccional entre el controlador y el editor de grafos."""
    modelo = Automata(alfabeto=["0", "1"])
    vista = VentanaPrincipal()
    controlador = ControladorAutomata(modelo=modelo, vista=vista)

    # 1. Crear estados desde el lienzo
    vista.lienzo_grafo.estado_creado.emit("q0", 50.0, 50.0, True, False)
    vista.lienzo_grafo.estado_creado.emit("q1", 200.0, 50.0, False, True)

    assert "q0" in modelo.estados
    assert "q1" in modelo.estados
    assert modelo.estado_inicial == "q0"
    assert "q1" in modelo.estados_aceptacion

    # 2. Conectar transición desde el lienzo
    vista.lienzo_grafo.transicion_solicitada.emit("q0", "0", "q1")
    assert modelo.obtener_transicion("q0", "0") == "q1"

    # 3. Eliminar estado desde el lienzo
    vista.lienzo_grafo.estado_eliminado.emit("q1")
    assert "q1" not in modelo.estados
    assert modelo.obtener_transicion("q0", "0") is None


def test_conexion_dos_clics_flujo(qapp, monkeypatch):
    """Verifica que el modo conectar funcione seleccionando origen en clic 1 y destino en clic 2."""
    from PyQt6.QtGui import QMouseEvent
    from PyQt6.QtCore import QPointF, Qt

    lienzo = LienzoGrafo()
    nodo0 = lienzo.agregar_nodo_visual("q0", 100, 100)
    nodo1 = lienzo.agregar_nodo_visual("q1", 300, 100)

    lienzo.establecer_modo(LienzoGrafo.MODO_CONECTAR)
    assert lienzo._nodo_origen_temporal is None

    transiciones_capturadas = []
    lienzo.transicion_solicitada.connect(lambda o, s, d: transiciones_capturadas.append((o, s, d)))

    # Simular diálogo que ingresa el símbolo "1"
    from PyQt6.QtWidgets import QDialog, QInputDialog
    from src.view.dialogo_seleccion_simbolos import DialogoSeleccionSimbolos

    monkeypatch.setattr(QInputDialog, "getText", lambda *args, **kwargs: ("1", True))
    monkeypatch.setattr(DialogoSeleccionSimbolos, "exec", lambda self: QDialog.DialogCode.Accepted)
    monkeypatch.setattr(DialogoSeleccionSimbolos, "obtener_simbolos_seleccionados", lambda self: {"1"})

    # Clic 1: sobre nodo0 (origen)
    pos_pantalla_0 = lienzo.mapFromScene(nodo0.pos())
    ev_clic1 = QMouseEvent(
        QMouseEvent.Type.MouseButtonPress,
        QPointF(pos_pantalla_0),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    lienzo.mousePressEvent(ev_clic1)

    assert lienzo._nodo_origen_temporal == nodo0
    assert lienzo._linea_guia_temporal.isVisible() is True

    # Soltado de ratón sobre nodo0: no debe cancelar ni disparar conexión
    ev_soltar1 = QMouseEvent(
        QMouseEvent.Type.MouseButtonRelease,
        QPointF(pos_pantalla_0),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
    )
    lienzo.mouseReleaseEvent(ev_soltar1)
    assert lienzo._nodo_origen_temporal == nodo0

    # Clic 2: sobre nodo1 (destino)
    pos_pantalla_1 = lienzo.mapFromScene(nodo1.pos())
    ev_clic2 = QMouseEvent(
        QMouseEvent.Type.MouseButtonPress,
        QPointF(pos_pantalla_1),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    lienzo.mousePressEvent(ev_clic2)

    # Debe haber conectado y reiniciado el estado temporal
    assert lienzo._nodo_origen_temporal is None
    assert lienzo._linea_guia_temporal.isVisible() is False
    assert len(transiciones_capturadas) == 1
    assert transiciones_capturadas[0] == ("q0", "1", "q1")


def test_geometria_bounding_rect_estado_inicial(qapp):
    """Verifica que el estado inicial contenga holgadamente la flecha y etiqueta 'inicio'."""
    nodo = ItemNodoEstado("q0", 0, 0, es_inicial=True)
    rect = nodo.boundingRect()

    # La flecha se extiende hacia la izquierda; el boundingRect debe cubrir al menos x = -80
    assert rect.left() <= -80.0
    assert rect.right() >= 27.0
    assert rect.top() <= -35.0
    assert rect.bottom() >= 27.0
