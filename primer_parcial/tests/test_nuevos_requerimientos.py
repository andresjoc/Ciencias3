"""Pruebas unitarias para los nuevos requerimientos:
- Zoom in / out / reset en el visor.
- Diferenciación de ida y vuelta con colores distintos en aristas bidireccionales.
- Restricción de caracteres especiales en todos los inputs.
- Ejecución automática paso a paso de la simulación.
- Limpiar grafo eliminando todo tipo de historial y estado.
"""

import pytest
from PyQt6.QtGui import QValidator
from PyQt6.QtWidgets import QApplication
from src.model.automata import Automata
from src.view.ventana_principal import VentanaPrincipal
from src.controller.controlador_automata import ControladorAutomata
from src.view.items_grafo import ItemAristaTransicion
from src.view.lienzo_grafo import LienzoGrafo


@pytest.fixture(scope="session")
def qapp():
    """Provee la instancia de QApplication para pruebas de interfaz gráfica."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_zoom_visor_grafo(qapp):
    """Verifica que los métodos de zoom modifiquen correctamente el factor de escala."""
    ventana = VentanaPrincipal()
    lienzo = ventana.lienzo_grafo

    factor_inicial = lienzo.factor_zoom
    assert factor_inicial == 1.0

    lienzo.zoom_acercar()
    assert lienzo.factor_zoom > 1.0
    assert abs(lienzo.factor_zoom - 1.2) < 1e-4

    lienzo.zoom_alejar()
    assert abs(lienzo.factor_zoom - 1.0) < 1e-4

    lienzo.zoom_alejar()
    assert lienzo.factor_zoom < 1.0

    lienzo.zoom_restablecer()
    assert lienzo.factor_zoom == 1.0


def test_aristas_bidireccionales_colores_distintos(qapp):
    """Verifica que las conexiones de ida y vuelta tengan tipos y colores diferenciados."""
    ventana = VentanaPrincipal()
    lienzo = ventana.lienzo_grafo

    nodo_a = lienzo.agregar_nodo_visual("q0", 0, 0)
    nodo_b = lienzo.agregar_nodo_visual("q1", 100, 0)

    # Solo arista de q0 a q1 (unidireccional)
    arista_ida = lienzo.agregar_arista_visual("q0", "a", "q1")
    assert arista_ida.obtener_tipo_bidireccional() is None

    # Agregar arista de q1 a q0 (convirtiéndola en bidireccional)
    arista_vuelta = lienzo.agregar_arista_visual("q1", "b", "q0")

    # Como "q0" < "q1", la ida q0 -> q1 es "ida" (verde), y q1 -> q0 es "vuelta" (rojo)
    assert arista_ida.obtener_tipo_bidireccional() == "ida"
    assert arista_vuelta.obtener_tipo_bidireccional() == "vuelta"


def test_restriccion_caracteres_especiales_inputs(qapp):
    """Verifica que los validadores de inputs rechacen caracteres especiales."""
    ventana = VentanaPrincipal()

    # 1. Campo de cadena en PanelSimulacion
    validador_cadena = ventana.panel_simulacion.campo_cadena.validator()
    assert validador_cadena is not None
    # Alfanuméricos válidos
    estado, _, _ = validador_cadena.validate("abc123", 0)
    assert estado == QValidator.State.Acceptable
    # Caracteres especiales inválidos
    estado, _, _ = validador_cadena.validate("abc@123", 0)
    assert estado == QValidator.State.Invalid
    estado, _, _ = validador_cadena.validate("a#b$", 0)
    assert estado == QValidator.State.Invalid

    # 2. Campo de nombre de estado en TablaTransiciones
    validador_estado = ventana.tabla_transiciones.campo_nombre_estado.validator()
    assert validador_estado is not None
    estado, _, _ = validador_estado.validate("q0", 0)
    assert estado == QValidator.State.Acceptable
    estado, _, _ = validador_estado.validate("q-0", 0)
    assert estado == QValidator.State.Invalid
    estado, _, _ = validador_estado.validate("q@!", 0)
    assert estado == QValidator.State.Invalid


def test_ejecucion_automatica_paso_a_paso(qapp):
    """Verifica que al ejecutar todo automáticamente se avance paso a paso con el temporizador."""
    modelo = Automata()
    modelo.definir_alfabeto(["0", "1"])
    modelo.agregar_estado("q0", es_inicial=True, es_aceptacion=False)
    modelo.agregar_estado("q1", es_inicial=False, es_aceptacion=True)
    modelo.agregar_transicion("q0", "0", "q0")
    modelo.agregar_transicion("q0", "1", "q1")
    modelo.agregar_transicion("q1", "0", "q0")
    modelo.agregar_transicion("q1", "1", "q1")

    ventana = VentanaPrincipal()
    controlador = ControladorAutomata(modelo, ventana)

    # Iniciar simulación de "01"
    assert controlador.al_solicitar_evaluacion("01") is True
    assert controlador._paso_actual == 0
    total_pasos = controlador._obtener_total_pasos()
    assert total_pasos == 3  # q0 -0-> q0 -1-> q1

    # Iniciar ejecución automática
    controlador.al_ejecutar_todo_automatico()
    assert controlador._temporizador_animacion.isActive() is True

    # Simular un tick del temporizador
    controlador._al_tick_temporizador_simulacion()
    assert controlador._paso_actual == 1
    assert controlador._temporizador_animacion.isActive() is True

    # Simular segundo tick (debe llegar al final y detener el temporizador)
    controlador._al_tick_temporizador_simulacion()
    assert controlador._paso_actual == 2
    assert controlador._temporizador_animacion.isActive() is False


def test_limpiar_grafo_elimina_todo_el_historial(qapp):
    """Verifica que limpiar grafo borre por completo el autómata, simulación y vistas."""
    modelo = Automata()
    modelo.definir_alfabeto(["a", "b"])
    modelo.agregar_estado("q0", es_inicial=True, es_aceptacion=False)
    modelo.agregar_estado("q1", es_inicial=False, es_aceptacion=True)
    modelo.agregar_transicion("q0", "a", "q1")

    ventana = VentanaPrincipal()
    controlador = ControladorAutomata(modelo, ventana)

    # Simular algo
    controlador.al_solicitar_evaluacion("a")
    assert controlador._traza_actual is not None

    # Ejecutar limpiar grafo completo
    controlador.al_limpiar_grafo_completo()

    # El modelo debe estar vacío
    assert modelo.estados == []
    assert modelo.estado_inicial is None
    assert modelo.estados_aceptacion == set()
    assert modelo.transiciones == {}

    # La simulación debe estar reseteada
    assert controlador._traza_actual is None
    assert controlador._paso_actual == 0
    assert controlador._temporizador_animacion.isActive() is False

    # El lienzo debe estar limpio
    assert len(ventana.lienzo_grafo.nodos) == 0
    assert len(ventana.lienzo_grafo.aristas) == 0

    # La tabla debe tener 0 filas
    assert ventana.tabla_transiciones.tabla.rowCount() == 0

    # El panel de simulación debe tener la cadena limpia
    assert ventana.panel_simulacion.campo_cadena.text() == ""


def test_dialogo_seleccion_simbolos_desplegable(qapp):
    """Verifica que el diálogo con desplegable permita seleccionar caracteres del alfabeto con actualización inmediata."""
    from src.view.dialogo_seleccion_simbolos import DialogoSeleccionSimbolos
    from PyQt6.QtCore import Qt, QEvent, QPointF
    from PyQt6.QtGui import QMouseEvent

    dialogo = DialogoSeleccionSimbolos(
        origen="q0",
        destino="q1",
        alfabeto_disponible=["0", "1", "2"],
        simbolos_actuales={"0"},
    )

    # Inicialmente solo "0" está marcado
    assert dialogo.obtener_simbolos_seleccionados() == {"0"}
    assert dialogo.desplegable.line_edit.text() == "0"
    assert "0" in dialogo.campo_resumen.text()

    # Probar marcar todos: actualiza inmediatamente el desplegable y el resumen
    dialogo._establecer_todos(True)
    assert dialogo.obtener_simbolos_seleccionados() == {"0", "1", "2"}
    assert dialogo.desplegable.line_edit.text() == "0, 1, 2"
    assert "0, 1, 2" in dialogo.campo_resumen.text()

    # Probar desmarcar todos: limpia inmediatamente el desplegable y el resumen
    dialogo._establecer_todos(False)
    assert dialogo.obtener_simbolos_seleccionados() == set()
    assert dialogo.desplegable.line_edit.text() == ""
    assert dialogo.campo_resumen.text() == ""

    # Marcar individualmente el item 1 ("1") en el modelo: actualiza en tiempo real
    item_1 = dialogo.desplegable.modelo.item(1)
    assert item_1.text() == "1"
    item_1.setCheckState(Qt.CheckState.Checked)

    assert dialogo.obtener_simbolos_seleccionados() == {"1"}
    assert dialogo.desplegable.line_edit.text() == "1"
    assert "1" in dialogo.campo_resumen.text()

    # Simular clic en la fila 2 ("2") a través del eventFilter para verificar toggle sin cerrar
    rect = dialogo.desplegable.view().visualRect(dialogo.desplegable.modelo.index(2, 0))
    evento_click = QMouseEvent(
        QEvent.Type.MouseButtonRelease,
        rect.center().toPointF(),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    resultado_filtro = dialogo.desplegable.eventFilter(dialogo.desplegable.view().viewport(), evento_click)
    assert resultado_filtro is True  # Interceptado para no cerrar popup
    assert dialogo.obtener_simbolos_seleccionados() == {"1", "2"}
    assert dialogo.desplegable.line_edit.text() == "1, 2"
    assert "1, 2" in dialogo.campo_resumen.text()


def test_desmarcar_primer_elemento_desplegable_mantiene_lista_correcta(qapp):
    """Verifica que al desmarcar el primer elemento, la vista del desplegable no se colapse en ese elemento."""
    from src.view.dialogo_seleccion_simbolos import DialogoSeleccionSimbolos
    from PyQt6.QtCore import Qt

    dialogo = DialogoSeleccionSimbolos(
        origen="q0",
        destino="q1",
        alfabeto_disponible=["a", "b", "c"],
        simbolos_actuales={"a", "b"},
    )

    # Estado inicial: a y b marcados
    assert dialogo.desplegable.line_edit.text() == "a, b"
    assert dialogo.obtener_simbolos_seleccionados() == {"a", "b"}

    # Desmarcar el primer elemento (índice 0, 'a')
    item_0 = dialogo.desplegable.modelo.item(0)
    assert item_0.text() == "a"
    item_0.setCheckState(Qt.CheckState.Unchecked)

    # La vista DEBE mostrar "b", no "a"
    assert dialogo.desplegable.line_edit.text() == "b"
    assert dialogo.obtener_simbolos_seleccionados() == {"b"}
    assert "b" in dialogo.campo_resumen.text()

    # Volver a marcar el primer elemento ('a')
    item_0.setCheckState(Qt.CheckState.Checked)
    assert dialogo.desplegable.line_edit.text() == "a, b"
    assert dialogo.obtener_simbolos_seleccionados() == {"a", "b"}



def test_dialogo_sin_alfabeto_no_permite_anadir_y_avisa_pantalla_principal(qapp):
    """Verifica que si no hay alfabeto definido, no brinde opción de añadir en el diálogo y avise."""
    from src.view.dialogo_seleccion_simbolos import DialogoSeleccionSimbolos

    dialogo = DialogoSeleccionSimbolos(
        origen="q0",
        destino="q1",
        alfabeto_disponible=[],
    )

    # No debe existir el desplegable ni campo de texto para añadir símbolos
    assert dialogo.desplegable is None
    assert getattr(dialogo, "campo_nuevo_simbolo", None) is None
    assert dialogo.obtener_simbolos_seleccionados() == set()



def test_placeholders_y_tooltips_en_elementos_interactivos(qapp):
    """Verifica que todos los elementos interactivos tengan placeholders y tooltips explicativos."""
    ventana = VentanaPrincipal()

    # 1. Panel de Alfabeto
    assert len(ventana.panel_alfabeto.campo_simbolos.placeholderText()) > 0
    assert len(ventana.panel_alfabeto.campo_simbolos.toolTip()) > 0
    assert len(ventana.panel_alfabeto.boton_establecer.toolTip()) > 0

    # 2. Tabla de Transiciones
    assert len(ventana.tabla_transiciones.campo_nombre_estado.placeholderText()) > 0
    assert len(ventana.tabla_transiciones.campo_nombre_estado.toolTip()) > 0
    assert len(ventana.tabla_transiciones.check_inicial.toolTip()) > 0
    assert len(ventana.tabla_transiciones.check_aceptacion.toolTip()) > 0
    assert len(ventana.tabla_transiciones.boton_agregar_estado.toolTip()) > 0
    assert len(ventana.tabla_transiciones.boton_eliminar_estado.toolTip()) > 0
    assert len(ventana.tabla_transiciones.tabla.toolTip()) > 0

    # 3. Panel de Simulación
    assert len(ventana.panel_simulacion.campo_cadena.placeholderText()) > 0
    assert len(ventana.panel_simulacion.campo_cadena.toolTip()) > 0
    assert len(ventana.panel_simulacion.boton_iniciar.toolTip()) > 0
    assert len(ventana.panel_simulacion.boton_anterior.toolTip()) > 0
    assert len(ventana.panel_simulacion.boton_siguiente.toolTip()) > 0
    assert len(ventana.panel_simulacion.boton_ejecutar_todo.toolTip()) > 0
    assert len(ventana.panel_simulacion.boton_reiniciar.toolTip()) > 0
    assert len(ventana.panel_simulacion.lienzo.toolTip()) > 0

    # 4. Barra de Herramientas del Grafo
    barra = ventana.barra_herramientas_grafo
    assert len(barra.boton_seleccionar.toolTip()) > 0
    assert len(barra.boton_desplazar.toolTip()) > 0
    assert len(barra.boton_crear_estado.toolTip()) > 0
    assert len(barra.boton_conectar.toolTip()) > 0
    assert len(barra.boton_borrar.toolTip()) > 0
    assert len(barra.boton_zoom_acercar.toolTip()) > 0
    assert len(barra.boton_zoom_alejar.toolTip()) > 0
    assert len(barra.boton_zoom_restablecer.toolTip()) > 0
    assert len(barra.boton_auto_organizar.toolTip()) > 0
    assert len(barra.boton_limpiar.toolTip()) > 0
    assert len(barra.boton_ayuda.toolTip()) > 0

    # 5. Lienzo del Grafo e Items
    lienzo = ventana.lienzo_grafo
    assert len(lienzo.toolTip()) > 0
    assert "Sección Editor Gráfico" in lienzo.toolTip()
    assert "Sección Editor Gráfico" in lienzo.placeholderText()

    nodo = lienzo.agregar_nodo_visual("q0", 0, 0, es_inicial=True)
    assert len(nodo.toolTip()) > 0
    assert "Sección Editor Gráfico" in nodo.toolTip()
    assert "Sección Editor Gráfico" in nodo.placeholderText()

    arista = lienzo.agregar_arista_visual("q0", "a", "q0")
    assert len(arista.toolTip()) > 0
    assert "Sección Editor Gráfico" in arista.toolTip()
    assert "Sección Editor Gráfico" in arista.placeholderText()


def test_hover_iluminacion_y_sombra_en_nodos_y_conexiones(qapp):
    """Verifica que al señalar con el cursor un nodo o conexión se active la iluminación/sombra."""
    ventana = VentanaPrincipal()
    lienzo = ventana.lienzo_grafo

    nodo = lienzo.agregar_nodo_visual("q0", 50, 50, es_inicial=True)
    arista = lienzo.agregar_arista_visual("q0", "a", "q0")

    assert nodo._en_hover is False
    assert arista._en_hover is False

    # 1. Señalar el nodo (hover enter)
    nodo.hoverEnterEvent(None)
    assert nodo._en_hover is True
    assert "Nodo de Estado 'q0'" in ventana.barra_estado.currentMessage()

    # Retirar cursor del nodo (hover leave)
    nodo.hoverLeaveEvent(None)
    assert nodo._en_hover is False

    # 2. Señalar la conexión (hover enter)
    arista.hoverEnterEvent(None)
    assert arista._en_hover is True
    assert "Conexión" in ventana.barra_estado.currentMessage()

    # Retirar cursor de la conexión (hover leave)
    arista.hoverLeaveEvent(None)
    assert arista._en_hover is False


def test_modo_desplazar_vista(qapp):
    """Verifica que el modo desplazar vista active el arrastre manual en el lienzo."""
    from PyQt6.QtWidgets import QGraphicsView
    from PyQt6.QtCore import Qt
    ventana = VentanaPrincipal()
    lienzo = ventana.lienzo_grafo

    # Modo por defecto es selección
    assert lienzo.modo_actual == LienzoGrafo.MODO_SELECCION
    assert lienzo.dragMode() == QGraphicsView.DragMode.RubberBandDrag

    # Cambiar a modo desplazar
    ventana.barra_herramientas_grafo.boton_desplazar.click()
    assert lienzo.modo_actual == LienzoGrafo.MODO_DESPLAZAR
    assert lienzo.dragMode() == QGraphicsView.DragMode.ScrollHandDrag
    assert lienzo.cursor().shape() == Qt.CursorShape.OpenHandCursor

    # Volver a modo selección
    ventana.barra_herramientas_grafo.boton_seleccionar.click()
    assert lienzo.modo_actual == LienzoGrafo.MODO_SELECCION
    assert lienzo.dragMode() == QGraphicsView.DragMode.RubberBandDrag


def test_secuencia_creacion_estados_al_borrar(qapp):
    """Verifica que al borrar estados intermedios o extremos, la numeración continúe a partir del mayor."""
    modelo = Automata()
    ventana = VentanaPrincipal()
    controlador = ControladorAutomata(modelo, ventana)

    # Crear estados q0, q1, q2, q3, q4, q5, q6, q7, q8
    for i in range(9):
        controlador.al_agregar_estado(f"q{i}", es_inicial=(i == 0), es_aceptacion=False)

    # Verificar que existen q0 a q8
    assert set(modelo.estados) == {f"q{i}" for i in range(9)}

    # Eliminar q2 y q8
    controlador.al_eliminar_estado("q2")
    controlador.al_eliminar_estado("q8")

    # Estados restantes: q0, q1, q3, q4, q5, q6, q7
    assert "q2" not in modelo.estados
    assert "q8" not in modelo.estados
    assert "q7" in modelo.estados

    # El siguiente identificador generado en el lienzo debe continuar desde el mayor (q7 + 1 = q8)
    siguiente = ventana.lienzo_grafo._obtener_siguiente_identificador_estado()
    assert siguiente == "q8"

    # Si agregamos q8, el siguiente debe ser q9
    controlador.al_agregar_estado(siguiente, es_inicial=False, es_aceptacion=False)
    assert "q8" in modelo.estados
    assert ventana.lienzo_grafo._obtener_siguiente_identificador_estado() == "q9"


def test_doble_conexion_inmediatamente_curva_ambos_lados(qapp):
    """Verifica que al trazar la conexión de vuelta, AMBAS conexiones se curven inmediatamente sin mover nodos."""
    ventana = VentanaPrincipal()
    lienzo = ventana.lienzo_grafo

    nodo_a = lienzo.agregar_nodo_visual("q0", 0, 0)
    nodo_b = lienzo.agregar_nodo_visual("q1", 200, 0)

    # 1. Crear arista de ida q0 -> q1
    arista_ida = lienzo.agregar_arista_visual("q0", "a", "q1")
    assert arista_ida is not None
    assert arista_ida.obtener_tipo_bidireccional() is None
    # Como es unidireccional y recta, elementCount del QPainterPath es 2 (MoveTo + LineTo)
    assert arista_ida.path().elementCount() == 2

    # 2. Crear arista de retorno q1 -> q0 (sin mover ningún nodo)
    arista_vuelta = lienzo.agregar_arista_visual("q1", "b", "q0")
    assert arista_vuelta is not None

    # Verificar que AMBAS aristas ahora se reconocen como bidireccionales
    assert arista_ida.obtener_tipo_bidireccional() == "ida"
    assert arista_vuelta.obtener_tipo_bidireccional() == "vuelta"

    # Verificar que AMBAS aristas son inmediatamente curvas (elementCount > 2 por la curva de Bézier quadTo)
    # Ninguna debe haberse quedado recta!
    assert arista_ida.path().elementCount() > 2
    assert arista_vuelta.path().elementCount() > 2

    # Verificar que las dos curvas se curvan en sentidos opuestos (el punto de etiqueta o medio se desvía arriba/abajo)
    # Para q0 en (0,0) y q1 en (200,0), el vector perpendicular normal apunta hacia arriba o abajo
    assert arista_ida._punto_etiqueta.y() != arista_vuelta._punto_etiqueta.y()

    # 3. Al eliminar la arista de retorno, la arista de ida debe volver a ser recta inmediatamente
    lienzo.eliminar_arista(arista_vuelta)
    assert arista_ida.obtener_tipo_bidireccional() is None
    assert arista_ida.path().elementCount() == 2


