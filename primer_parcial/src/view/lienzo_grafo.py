"""Lienzo gráfico interactivo estilo Draw.io para pintar y conectar autómatas."""

from __future__ import annotations
from collections import Counter
import math
import re
from typing import Dict, List, Optional, Set

from PyQt6.QtCore import QLineF, QPointF, QRectF, Qt, pyqtSignal
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QMouseEvent,
    QPainter,
    QPen,
    QWheelEvent,
)
from PyQt6.QtWidgets import (
    QDialog,
    QGraphicsItem,
    QGraphicsLineItem,
    QGraphicsScene,
    QGraphicsSceneMouseEvent,
    QGraphicsView,
    QInputDialog,
    QLineEdit,
    QMessageBox,
    QWidget,
)

from src.view.dialogo_seleccion_simbolos import DialogoSeleccionSimbolos
from src.view.items_grafo import ItemAristaTransicion, ItemNodoEstado


class LienzoGrafo(QGraphicsView):
    """Editor visual de grafos donde el usuario puede arrastrar estados y conectar flechas.

    Señales:
        estado_creado (str, float, float, bool, bool): nombre, x, y, es_inicial, es_aceptacion.
        estado_movido (str, float, float): nombre, nueva_x, nueva_y.
        estado_modificado (str, bool, bool): nombre, es_inicial, es_aceptacion.
        estado_renombrado (str, str): nombre_antiguo, nombre_nuevo.
        estado_eliminado (str): nombre.
        transicion_solicitada (str, str, str): origen, simbolo, destino.
        transicion_eliminada (str, str, str): origen, simbolo, destino.
        mensaje_solicitado (str): Texto explicativo para la barra de estado.
        grafo_limpiado (): Emite cuando se limpia el grafo por completo.
    """

    MODO_SELECCION = "seleccion"
    MODO_DESPLAZAR = "desplazar"
    MODO_CREAR_ESTADO = "crear_estado"
    MODO_CONECTAR = "conectar"
    MODO_BORRAR = "borrar"

    estado_creado = pyqtSignal(str, float, float, bool, bool)
    estado_movido = pyqtSignal(str, float, float)
    estado_modificado = pyqtSignal(str, bool, bool)
    estado_renombrado = pyqtSignal(str, str)
    estado_eliminado = pyqtSignal(str)
    transicion_solicitada = pyqtSignal(str, str, str)
    transicion_eliminada = pyqtSignal(str, str, str)
    mensaje_solicitado = pyqtSignal(str)
    grafo_limpiado = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._escena = QGraphicsScene(self)
        self.setScene(self._escena)
        self._escena.setSceneRect(-2000, -2000, 4000, 4000)

        # Calidad de renderizado y actualización completa para evitar rastros de dibujo
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

        # Diccionarios de referencia para sincronización rápida
        self.nodos: Dict[str, ItemNodoEstado] = {}
        self.aristas: List[ItemAristaTransicion] = []

        self.modo_actual: str = self.MODO_SELECCION
        self._nodo_origen_temporal: Optional[ItemNodoEstado] = None
        self._linea_guia_temporal: Optional[QGraphicsLineItem] = None
        self._contador_estados: int = 0
        self._simbolos_alfabeto_permitidos: List[str] = []
        self._factor_zoom: float = 1.0
        self.setToolTip(
            "Sección Editor Gráfico: Pizarra interactiva del autómata donde diseña estados y transiciones. "
            "Arrastre estados, conecte flechas y ajuste la vista con zoom o desplazamiento."
        )

        self._inicializar_linea_guia()

    def placeholderText(self) -> str:
        """Texto identificador de ubicación para la sección del editor gráfico."""
        return "Sección Editor Gráfico: Pizarra del autómata (haga clic o arrastre para interactuar)"

    def zoom_acercar(self) -> None:
        """Aumenta el nivel de zoom del lienzo gráfico."""
        if self._factor_zoom < 3.5:
            factor = 1.2
            self.scale(factor, factor)
            self._factor_zoom *= factor
            self.mensaje_solicitado.emit(f"Zoom: {int(self._factor_zoom * 100)}%")

    def zoom_alejar(self) -> None:
        """Disminuye el nivel de zoom del lienzo gráfico."""
        if self._factor_zoom > 0.35:
            factor = 1.0 / 1.2
            self.scale(factor, factor)
            self._factor_zoom *= factor
            self.mensaje_solicitado.emit(f"Zoom: {int(self._factor_zoom * 100)}%")

    def zoom_restablecer(self) -> None:
        """Restablece el nivel de zoom a la escala original (1:1 o 100%)."""
        self.resetTransform()
        self._factor_zoom = 1.0
        self.mensaje_solicitado.emit("Zoom restablecido al 100%")

    @property
    def factor_zoom(self) -> float:
        """Factor de escala actual del visor de grafos."""
        return self._factor_zoom

    def wheelEvent(self, event: QWheelEvent) -> None:
        """Permite hacer zoom interactivo con la rueda del ratón."""
        delta = event.angleDelta().y()
        if delta > 0:
            self.zoom_acercar()
        elif delta < 0:
            self.zoom_alejar()
        event.accept()

    def _inicializar_linea_guia(self) -> None:
        """Crea la línea elástica visible al conectar estados."""
        pluma = QPen(QColor("#2563eb"), 2.2, Qt.PenStyle.DashLine)
        self._linea_guia_temporal = self._escena.addLine(0, 0, 0, 0, pluma)
        self._linea_guia_temporal.setZValue(10.0)
        self._linea_guia_temporal.setEnabled(False)
        self._linea_guia_temporal.setVisible(False)

    def establecer_alfabeto_permitido(self, simbolos: List[str]) -> None:
        """Configura los símbolos válidos para validar las transiciones creadas."""
        self._simbolos_alfabeto_permitidos = list(simbolos)

    def establecer_modo(self, modo: str) -> None:
        """Cambia el modo de interacción del cursor (selección, crear, conectar, borrar)."""
        self.modo_actual = modo
        self._cancelar_conexion_temporal()

        if modo == self.MODO_SELECCION:
            self.setCursor(Qt.CursorShape.ArrowCursor)
            self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
            self.mensaje_solicitado.emit("Modo Selección: Arrastre estados para moverlos o selecciónelos con clic.")
        elif modo == self.MODO_DESPLAZAR:
            self.setCursor(Qt.CursorShape.OpenHandCursor)
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            self.mensaje_solicitado.emit("Modo Desplazar: Mantén el clic presionado y arrastra para mover la vista de la pizarra.")
        elif modo == self.MODO_CREAR_ESTADO:
            self.setCursor(Qt.CursorShape.CrossCursor)
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            self.mensaje_solicitado.emit("Modo Crear Estado: Haz clic en el lienzo para colocar un nuevo estado.")
        elif modo == self.MODO_CONECTAR:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            self.mensaje_solicitado.emit("Modo Conectar: Haz clic en el estado de ORIGEN y luego en el estado DESTINO.")
        elif modo == self.MODO_BORRAR:
            self.setCursor(Qt.CursorShape.ForbiddenCursor)
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            self.mensaje_solicitado.emit("Modo Borrar: Haz clic sobre un estado o flecha para eliminarlo.")

    def drawBackground(self, painter: QPainter, rect: QRectF) -> None:
        """Dibuja una cuadrícula punteada elegante y suave estilo Draw.io / Figma."""
        painter.fillRect(rect, QColor("#f8fafc"))  # Fondo pizarra muy suave

        tam_cuadricula = 22
        izq = int(rect.left()) - (int(rect.left()) % tam_cuadricula)
        arr = int(rect.top()) - (int(rect.top()) % tam_cuadricula)

        painter.setPen(QColor("#cbd5e1"))  # Puntos grises sutiles
        for x in range(izq, int(rect.right()), tam_cuadricula):
            for y in range(arr, int(rect.bottom()), tam_cuadricula):
                painter.drawPoint(x, y)

    def drawForeground(self, painter: QPainter, rect: QRectF) -> None:
        """Dibuja un marco placeholder explicativo en el centro cuando la pizarra no contiene estados."""
        super().drawForeground(painter, rect)
        if not self.nodos:
            painter.save()
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            centro = self.mapToScene(self.viewport().rect().center())
            ancho_box = 440.0
            alto_box = 105.0
            rect_box = QRectF(
                centro.x() - ancho_box / 2,
                centro.y() - alto_box / 2,
                ancho_box,
                alto_box,
            )

            # Fondo translúcido con borde redondeado suave punteado
            painter.setPen(QPen(QColor("#94a3b8"), 1.5, Qt.PenStyle.DashLine))
            painter.setBrush(QBrush(QColor(255, 255, 255, 230)))
            painter.drawRoundedRect(rect_box, 10, 10)

            # Título formal de ubicación en la sección
            painter.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
            painter.setPen(QColor("#334155"))
            rect_titulo = QRectF(rect_box.left(), rect_box.top() + 14, ancho_box, 24)
            painter.drawText(
                rect_titulo,
                Qt.AlignmentFlag.AlignCenter,
                "Sección Editor Gráfico: Pizarra del Autómata",
            )

            # Subtítulo explicativo con instrucciones
            painter.setFont(QFont("Segoe UI", 9))
            painter.setPen(QColor("#64748b"))
            rect_sub = QRectF(rect_box.left() + 16, rect_box.top() + 42, ancho_box - 32, 50)
            texto_guia = (
                "• Utilice la herramienta 'Crear Estado' o doble clic para añadir nodos\n"
                "• Conecte flechas entre estados para trazar las transiciones formales"
            )
            painter.drawText(rect_sub, Qt.AlignmentFlag.AlignCenter, texto_guia)
            painter.restore()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Gestiona las pulsaciones de ratón según la herramienta activa."""
        # 0. Modo Desplazar (Pan con arrastre de mano)
        if self.modo_actual == self.MODO_DESPLAZAR:
            super().mousePressEvent(event)
            return

        pos_escena = self.mapToScene(event.pos())

        # Resolver el nodo o arista bajo el cursor examinando los items en la posición
        item_nodo = None
        item_arista = None
        for it in self.items(event.pos()):
            if it == self._linea_guia_temporal:
                continue
            if isinstance(it, ItemNodoEstado):
                item_nodo = it
                break
            elif it.parentItem() and isinstance(it.parentItem(), ItemNodoEstado):
                item_nodo = it.parentItem()
                break
            elif isinstance(it, ItemAristaTransicion):
                if item_arista is None:
                    item_arista = it
            elif it.parentItem() and isinstance(it.parentItem(), ItemAristaTransicion):
                if item_arista is None:
                    item_arista = it.parentItem()

        # 1. Modo Crear Estado
        if self.modo_actual == self.MODO_CREAR_ESTADO and event.button() == Qt.MouseButton.LeftButton:
            self._crear_nuevo_estado_en(pos_escena.x(), pos_escena.y())
            return

        # 2. Modo Borrar
        if self.modo_actual == self.MODO_BORRAR and event.button() == Qt.MouseButton.LeftButton:
            if item_nodo:
                self.eliminar_nodo(item_nodo)
            elif item_arista:
                self.eliminar_arista(item_arista)
            return

        # 3. Modo Conectar Transición (Flujo intuitivo de dos clics)
        if self.modo_actual == self.MODO_CONECTAR:
            if event.button() == Qt.MouseButton.RightButton:
                self._cancelar_conexion_temporal()
                self.mensaje_solicitado.emit("Conexión cancelada.")
                return

            if event.button() == Qt.MouseButton.LeftButton:
                if self._nodo_origen_temporal is None:
                    # Primer clic: Seleccionar estado de origen
                    if item_nodo:
                        self._nodo_origen_temporal = item_nodo
                        if self._linea_guia_temporal:
                            p = item_nodo.pos()
                            self._linea_guia_temporal.setLine(p.x(), p.y(), pos_escena.x(), pos_escena.y())
                            self._linea_guia_temporal.setVisible(True)
                        self.mensaje_solicitado.emit(
                            f"Estado origen '{item_nodo.nombre}' seleccionado. Haz clic en el estado DESTINO (o en el mismo para bucle)."
                        )
                    else:
                        self.mensaje_solicitado.emit(
                            "Haz clic sobre un estado para iniciar la conexión."
                        )
                    return
                else:
                    # Segundo clic: Seleccionar estado de destino y conectar
                    nodo_origen = self._nodo_origen_temporal
                    if item_nodo:
                        self._cancelar_conexion_temporal()
                        self._solicitar_simbolo_y_conectar(nodo_origen, item_nodo)
                    else:
                        # Clic en el vacío: cancelar la conexión en curso
                        self._cancelar_conexion_temporal()
                        self.mensaje_solicitado.emit("Conexión cancelada.")
                    return

        # 4. Modo Selección: si se hace clic sobre una arista, seleccionarla y abrir selector
        if self.modo_actual == self.MODO_SELECCION and event.button() == Qt.MouseButton.LeftButton:
            if item_arista and not item_nodo:
                super().mousePressEvent(event)
                self.solicitar_editar_arista(item_arista)
                return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Actualiza la línea elástica de conexión temporal si hay un nodo origen seleccionado."""
        if self.modo_actual == self.MODO_DESPLAZAR:
            super().mouseMoveEvent(event)
            return

        if self._nodo_origen_temporal and self._linea_guia_temporal:
            p_origen = self._nodo_origen_temporal.pos()
            p_actual = self.mapToScene(event.pos())
            self._linea_guia_temporal.setLine(p_origen.x(), p_origen.y(), p_actual.x(), p_actual.y())

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Gestiona el soltado del ratón permitiendo tanto dos clics como arrastrar."""
        if self.modo_actual == self.MODO_DESPLAZAR:
            super().mouseReleaseEvent(event)
            return

        if self.modo_actual == self.MODO_CONECTAR and self._nodo_origen_temporal is not None:
            # Si el usuario realizó un arrastre directo y soltó sobre un nodo destino distinto
            items_en_punto = self.items(event.pos())
            nodo_destino = None
            for it in items_en_punto:
                if it == self._linea_guia_temporal:
                    continue
                if isinstance(it, ItemNodoEstado):
                    nodo_destino = it
                    break
                elif it.parentItem() and isinstance(it.parentItem(), ItemNodoEstado):
                    nodo_destino = it.parentItem()
                    break

            if nodo_destino is not None and nodo_destino != self._nodo_origen_temporal:
                nodo_origen = self._nodo_origen_temporal
                self._cancelar_conexion_temporal()
                self._solicitar_simbolo_y_conectar(nodo_origen, nodo_destino)
                super().mouseReleaseEvent(event)
                return

        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event: object) -> None:
        """Permite borrar items seleccionados con la tecla Supr o volver a modo Selección con Esc."""
        tecla = event.key()
        if tecla in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            items_sel = self._escena.selectedItems()
            for item in items_sel:
                if isinstance(item, ItemNodoEstado):
                    self.eliminar_nodo(item)
                elif isinstance(item, ItemAristaTransicion):
                    self.eliminar_arista(item)
            event.accept()
            return
        elif tecla == Qt.Key.Key_Escape:
            if self._nodo_origen_temporal is not None:
                self._cancelar_conexion_temporal()
                self.mensaje_solicitado.emit("Conexión cancelada.")
            else:
                self.establecer_modo(self.MODO_SELECCION)
            event.accept()
            return

        super().keyPressEvent(event)

    def _cancelar_conexion_temporal(self) -> None:
        """Oculta y reinicia la línea guía de conexión."""
        self._nodo_origen_temporal = None
        if self._linea_guia_temporal:
            self._linea_guia_temporal.setVisible(False)

    def _obtener_siguiente_identificador_estado(self) -> str:
        """Determina el siguiente nombre de estado continuando la secuencia desde el mayor índice existente."""
        if not self.nodos:
            return "q0"

        # Extraer prefijo y números de los estados existentes
        numeros = []
        prefijos = []
        for nombre in self.nodos.keys():
            match = re.match(r"^([a-zA-Z]*)(\d+)$", nombre.strip())
            if match:
                prefijo, num_str = match.groups()
                prefijos.append(prefijo)
                numeros.append(int(num_str))

        if not numeros:
            contador = len(self.nodos)
            while f"q{contador}" in self.nodos:
                contador += 1
            return f"q{contador}"

        # Continuar la secuencia desde el mayor índice existente + 1 (evita rellenar huecos internos como q2)
        mayor_numero = max(numeros)
        siguiente_num = mayor_numero + 1

        prefijo_comun = Counter(prefijos).most_common(1)[0][0] if prefijos else "q"

        candidato = f"{prefijo_comun}{siguiente_num}"
        while candidato in self.nodos:
            siguiente_num += 1
            candidato = f"{prefijo_comun}{siguiente_num}"

        return candidato

    def _crear_nuevo_estado_en(self, x: float, y: float) -> None:
        """Crea e inserta un nuevo estado con nombre incremental continuando la secuencia."""
        nombre = self._obtener_siguiente_identificador_estado()
        es_primero = (len(self.nodos) == 0)
        self.agregar_nodo_visual(nombre, x, y, es_inicial=es_primero, es_aceptacion=False)
        self.estado_creado.emit(nombre, x, y, es_primero, False)

    def agregar_nodo_visual(
        self,
        nombre: str,
        x: float,
        y: float,
        es_inicial: bool = False,
        es_aceptacion: bool = False,
    ) -> ItemNodoEstado:
        """Instancia e inserta un nodo en la escena gráfica."""
        if nombre in self.nodos:
            nodo = self.nodos[nombre]
            nodo.setPos(x, y)
            nodo.establecer_es_inicial(es_inicial)
            nodo.establecer_es_aceptacion(es_aceptacion)
            return nodo

        nodo = ItemNodoEstado(
            nombre=nombre,
            x=x,
            y=y,
            es_inicial=es_inicial,
            es_aceptacion=es_aceptacion,
            lienzo=self,
        )
        self._escena.addItem(nodo)
        self.nodos[nombre] = nodo
        return nodo

    def _solicitar_simbolo_y_conectar(
        self,
        origen: ItemNodoEstado,
        destino: ItemNodoEstado,
    ) -> None:
        if not self._simbolos_alfabeto_permitidos:
            self.mensaje_solicitado.emit(
                "No hay un alfabeto formal (Σ) definido. Debe añadirlo primero en la pantalla principal."
            )
        dialogo = DialogoSeleccionSimbolos(
            origen=origen.nombre,
            destino=destino.nombre,
            alfabeto_disponible=self._simbolos_alfabeto_permitidos,
            simbolos_actuales=None,
            parent=self,
        )
        if dialogo.exec() == QDialog.DialogCode.Accepted:
            simbolos_seleccionados = dialogo.obtener_simbolos_seleccionados()
            if not simbolos_seleccionados:
                return

            for sim in sorted(simbolos_seleccionados):
                self.transicion_solicitada.emit(origen.nombre, sim, destino.nombre)

    def agregar_arista_visual(
        self,
        origen: str,
        simbolo: str,
        destino: str,
    ) -> Optional[ItemAristaTransicion]:
        """Crea o actualiza la arista gráfica entre dos estados para el símbolo especificado."""
        nodo_orig = self.nodos.get(origen)
        nodo_dest = self.nodos.get(destino)
        if not nodo_orig or not nodo_dest:
            return None

        # Buscar si ya existe una arista en esa misma dirección
        arista_existente = next(
            (a for a in self.aristas if a.nodo_origen == nodo_orig and a.nodo_destino == nodo_dest),
            None,
        )
        if arista_existente:
            arista_existente.simbolos.add(simbolo)
            arista_existente.actualizar_geometria()
            arista_existente.update()
            return arista_existente

        arista = ItemAristaTransicion(nodo_orig, nodo_dest, {simbolo}, lienzo=self)
        self._escena.addItem(arista)
        self.aristas.append(arista)
        arista.actualizar_geometria()

        # Si existe una arista opuesta, actualizarla inmediatamente para que ambas queden curvas desde el inicio
        arista_opuesta = next(
            (a for a in self.aristas if a.nodo_origen == nodo_dest and a.nodo_destino == nodo_orig and a != arista),
            None,
        )
        if arista_opuesta:
            arista_opuesta.actualizar_geometria()
            arista_opuesta.update()

        return arista

    def al_nodo_movido(self, nombre: str, x: float, y: float) -> None:
        """Emite la señal de que un nodo ha sido reubicado por el usuario."""
        self.estado_movido.emit(nombre, x, y)

    def al_cambiar_propiedad_nodo(self, nombre: str, es_inicial: bool, es_aceptacion: bool) -> None:
        """Emite la señal de modificación de atributos (inicial / aceptación)."""
        # Si este estado se hizo inicial, asegurar que los otros dejen de serlo visualmente si es DFA
        if es_inicial:
            for n_nombre, n_item in self.nodos.items():
                if n_nombre != nombre and n_item.es_inicial:
                    n_item.establecer_es_inicial(False)

        self.estado_modificado.emit(nombre, es_inicial, es_aceptacion)

    def solicitar_renombrar_nodo(self, nodo: ItemNodoEstado) -> None:
        """Abre un diálogo para cambiar el nombre de un estado con placeholder explicativo."""
        dialogo = QInputDialog(self)
        dialogo.setWindowTitle("Renombrar Estado")
        dialogo.setLabelText("Nuevo identificador para el estado:")
        dialogo.setTextValue(nodo.nombre)
        campo_texto = dialogo.findChild(QLineEdit)
        if campo_texto:
            campo_texto.setPlaceholderText("Sección Editor Gráfico: Ingrese identificador (ej. q0, q1)")
            campo_texto.setToolTip("Identificador alfanumérico único para el estado en el autómata.")

        if dialogo.exec() == QDialog.DialogCode.Accepted:
            nuevo_nombre = dialogo.textValue()
            if nuevo_nombre and nuevo_nombre.strip() and nuevo_nombre.strip() != nodo.nombre:
                nombre_limpio = nuevo_nombre.strip()
                if not (nombre_limpio.isalnum() and nombre_limpio.isascii()):
                    QMessageBox.warning(
                        self,
                        "Nombre Inválido",
                        "El nombre del estado solo puede contener letras y números sin caracteres especiales."
                    )
                    return

                if nombre_limpio in self.nodos:
                    QMessageBox.warning(self, "Nombre Duplicado", f"El estado '{nombre_limpio}' ya existe.")
                    return

                antiguo = nodo.nombre
                del self.nodos[antiguo]
                nodo.nombre = nombre_limpio
                self.nodos[nombre_limpio] = nodo
                nodo.actualizar_tooltip()
                nodo.update()
                self.estado_renombrado.emit(antiguo, nombre_limpio)

    def iniciar_conexion_desde(self, nodo: ItemNodoEstado) -> None:
        """Inicia el modo de conexión interactiva partiendo del nodo indicado."""
        self.establecer_modo(self.MODO_CONECTAR)
        self._nodo_origen_temporal = nodo
        if self._linea_guia_temporal:
            p = nodo.pos()
            self._linea_guia_temporal.setLine(p.x(), p.y(), p.x(), p.y())
            self._linea_guia_temporal.setVisible(True)

    def solicitar_editar_arista(self, arista: ItemAristaTransicion) -> None:
        """Permite editar los símbolos asociados a una arista existente mediante el selector desplegable."""
        if not self._simbolos_alfabeto_permitidos:
            self.mensaje_solicitado.emit(
                "No hay un alfabeto formal (Σ) definido. Debe añadirlo primero en la pantalla principal."
            )
        dialogo = DialogoSeleccionSimbolos(
            origen=arista.nodo_origen.nombre,
            destino=arista.nodo_destino.nombre,
            alfabeto_disponible=self._simbolos_alfabeto_permitidos,
            simbolos_actuales=arista.simbolos,
            parent=self,
        )
        if dialogo.exec() == QDialog.DialogCode.Accepted:
            nuevos = dialogo.obtener_simbolos_seleccionados()
            # Notificar eliminados
            eliminados = arista.simbolos - nuevos
            for e in eliminados:
                self.transicion_eliminada.emit(arista.nodo_origen.nombre, e, arista.nodo_destino.nombre)
            # Notificar agregados
            agregados = nuevos - arista.simbolos
            for a in agregados:
                self.transicion_solicitada.emit(arista.nodo_origen.nombre, a, arista.nodo_destino.nombre)

            if not nuevos:
                self.eliminar_arista(arista)
            else:
                arista.simbolos = nuevos
                arista.actualizar_geometria()
                arista.update()

    def eliminar_nodo(self, nodo: ItemNodoEstado) -> None:
        """Elimina un estado del lienzo y todas las aristas conectadas."""
        nombre = nodo.nombre
        # Eliminar aristas incidentes
        for arista in list(nodo.aristas_incidentes):
            self.eliminar_arista(arista, notificar=False)

        if nombre in self.nodos:
            del self.nodos[nombre]

        self._escena.removeItem(nodo)
        self.estado_eliminado.emit(nombre)

    def eliminar_arista(
        self,
        arista: ItemAristaTransicion,
        notificar: bool = True,
    ) -> None:
        nodo_orig = arista.nodo_origen
        nodo_dest = arista.nodo_destino

        if arista in self.aristas:
            self.aristas.remove(arista)

        nodo_orig.remover_arista(arista)
        nodo_dest.remover_arista(arista)
        self._escena.removeItem(arista)

        # Si existía una arista opuesta, ahora deja de ser bidireccional: actualizarla para que vuelva a ser recta
        arista_opuesta = next(
            (a for a in self.aristas if a.nodo_origen == nodo_dest and a.nodo_destino == nodo_orig),
            None,
        )
        if arista_opuesta:
            arista_opuesta.actualizar_geometria()
            arista_opuesta.update()

        if notificar:
            for s in arista.simbolos:
                self.transicion_eliminada.emit(nodo_orig.nombre, s, nodo_dest.nombre)

    def limpiar_grafo(self, notificar: bool = True) -> None:
        """Borra todos los nodos y aristas del lienzo."""
        self._cancelar_conexion_temporal()
        for arista in list(self.aristas):
            self._escena.removeItem(arista)
        self.aristas.clear()

        for nodo in list(self.nodos.values()):
            self._escena.removeItem(nodo)
        self.nodos.clear()
        self._contador_estados = 0

        if notificar:
            self.grafo_limpiado.emit()

    def auto_organizar_nodos(self) -> None:
        """Distribuye los estados de forma circular estética y equidistante."""
        total = len(self.nodos)
        if total == 0:
            return

        radio_distribucion = max(140.0, total * 35.0)
        centro_x = 0.0
        centro_y = 0.0

        for i, (nombre, nodo) in enumerate(self.nodos.items()):
            angulo = 2 * math.pi * i / total
            nx = centro_x + radio_distribucion * math.cos(angulo)
            ny = centro_y + radio_distribucion * math.sin(angulo)
            nodo.setPos(nx, ny)

        for arista in self.aristas:
            arista.actualizar_geometria()

    def resaltar_estado(self, nombre_estado: Optional[str]) -> None:
        """Ilumina en amarillo el estado activo durante la simulación de la cinta."""
        for nombre, nodo in self.nodos.items():
            nodo.establecer_resaltado(nombre == nombre_estado)

    def sincronizar_desde_modelo(
        self,
        estados: List[str],
        transiciones: dict,
        estado_inicial: Optional[str],
        estados_aceptacion: Set[str],
        posiciones_restauradas: Optional[Dict[str, Tuple[float, float]]] = None,
    ) -> None:
        """Sincroniza el lienzo cuando el modelo cambia externamente (ej. tabla o deshacer)."""
        # 1. Eliminar nodos que ya no están en Q
        for n_existente in list(self.nodos.keys()):
            if n_existente not in estados:
                nodo = self.nodos[n_existente]
                self._escena.removeItem(nodo)
                del self.nodos[n_existente]

        # 2. Agregar nodos nuevos preservando o restaurando posiciones
        for i, nombre in enumerate(estados):
            if nombre in self.nodos:
                nodo = self.nodos[nombre]
                nodo.establecer_es_inicial(nombre == estado_inicial)
                nodo.establecer_es_aceptacion(nombre in estados_aceptacion)
                if posiciones_restauradas and nombre in posiciones_restauradas:
                    px, py = posiciones_restauradas[nombre]
                    nodo.setPos(px, py)
            else:
                # Posición restaurada o posición automática circular
                if posiciones_restauradas and nombre in posiciones_restauradas:
                    x, y = posiciones_restauradas[nombre]
                else:
                    angulo = 2 * math.pi * i / max(1, len(estados))
                    radio = 140.0
                    x = radio * math.cos(angulo)
                    y = radio * math.sin(angulo)
                self.agregar_nodo_visual(
                    nombre=nombre,
                    x=x,
                    y=y,
                    es_inicial=(nombre == estado_inicial),
                    es_aceptacion=(nombre in estados_aceptacion),
                )

        # 3. Reconstruir aristas
        for arista in list(self.aristas):
            self._escena.removeItem(arista)
        self.aristas.clear()
        for nodo in self.nodos.values():
            nodo.aristas_incidentes.clear()

        for origen, trans in transiciones.items():
            for simbolo, destinos in trans.items():
                if isinstance(destinos, (set, list)):
                    for dest in destinos:
                        self.agregar_arista_visual(origen, simbolo, dest)
                elif destinos:
                    self.agregar_arista_visual(origen, simbolo, str(destinos))

        for a in self.aristas:
            a.actualizar_geometria()
            a.update()
