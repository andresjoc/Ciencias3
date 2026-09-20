"""Items gráficos personalizados para el editor interactivo de grafos de autómatas.

Incluye:
- ItemNodoEstado: Círculo interactivo arrastrable con soporte de estado inicial y aceptación.
- ItemAristaTransicion: Flecha dirigida con soporte de curvatura, bucles (self-loops) y etiquetas.
"""

from __future__ import annotations
import math
from typing import List, Optional, Set, TYPE_CHECKING

from PyQt6.QtCore import QLineF, QPointF, QRectF, Qt
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QPainter,
    QPainterPath,
    QPen,
    QPolygonF,
)
from PyQt6.QtWidgets import (
    QGraphicsItem,
    QGraphicsPathItem,
    QGraphicsSceneMouseEvent,
    QMenu,
)

if TYPE_CHECKING:
    from src.view.lienzo_grafo import LienzoGrafo


class ItemNodoEstado(QGraphicsItem):
    """Representa visualmente un estado formal q en el lienzo interactivo.

    Características:
    - Arrastrable libremente por el usuario con actualización de flechas en tiempo real.
    - Anillo concéntrico interior para estados de aceptación (doble círculo formal).
    - Flecha entrante lateral desde la izquierda para estado inicial (-> q).
    - Resaltado brillante cuando el estado está activo en la simulación paso a paso.
    - Menú contextual de clic derecho para editar propiedades.
    """

    RADIO = 27.0
    DIAMETRO = RADIO * 2.0

    def __init__(
        self,
        nombre: str,
        x: float = 0.0,
        y: float = 0.0,
        es_inicial: bool = False,
        es_aceptacion: bool = False,
        lienzo: Optional[LienzoGrafo] = None,
    ) -> None:
        super().__init__()
        self.nombre = nombre
        self.es_inicial = es_inicial
        self.es_aceptacion = es_aceptacion
        self.lienzo = lienzo
        self.aristas_incidentes: List[ItemAristaTransicion] = []
        self._esta_resaltado = False

        self.setPos(x, y)
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setAcceptHoverEvents(True)
        self.setZValue(2.0)  # Los nodos se dibujan por encima de las aristas

    def boundingRect(self) -> QRectF:
        """Define el área envolvente del nodo incluyendo la flecha inicial si aplica."""
        margen_izq = 65.0 if self.es_inicial else 12.0
        margen_sup = 25.0 if self.es_inicial else 12.0
        margen_der = 12.0
        margen_inf = 12.0
        return QRectF(
            -self.RADIO - margen_izq,
            -self.RADIO - margen_sup,
            self.DIAMETRO + margen_izq + margen_der,
            self.DIAMETRO + margen_sup + margen_inf,
        )

    def shape(self) -> QPainterPath:
        """Define la forma de colisión precisa para selección y clics de interacción."""
        path = QPainterPath()
        path.addEllipse(QRectF(-self.RADIO, -self.RADIO, self.DIAMETRO, self.DIAMETRO))
        if self.es_inicial:
            path.addRect(QRectF(-self.RADIO - 40.0, -14.0, 40.0, 28.0))
        return path

    def paint(
        self,
        painter: QPainter,
        option: object,
        widget: object = None,
    ) -> None:
        """Dibuja el estado con diseño moderno, borde, doble aro si aplica y texto."""
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 1. Flecha inicial entrante (->) desde la izquierda si es_inicial
        if self.es_inicial:
            self._dibujar_flecha_inicial(painter)

        # 2. Estilos según selección y resaltado en simulación
        if self._esta_resaltado:
            color_fondo = QColor("#fef08a")  # Amarillo simulación activo
            color_borde = QColor("#ca8a04")
            grosor_borde = 3.2
        elif self.isSelected():
            color_fondo = QColor("#eff6ff")
            color_borde = QColor("#2563eb")  # Azul seleccionado
            grosor_borde = 2.6
        else:
            color_fondo = QColor("#ffffff")
            color_borde = QColor("#1e293b")  # Pizarra oscuro
            grosor_borde = 2.0

        # 3. Círculo principal del estado
        rect_circulo = QRectF(-self.RADIO, -self.RADIO, self.DIAMETRO, self.DIAMETRO)
        pluma = QPen(color_borde, grosor_borde)
        pincel = QBrush(color_fondo)
        painter.setPen(pluma)
        painter.setBrush(pincel)
        painter.drawEllipse(rect_circulo)

        # 4. Doble círculo concéntrico interior para estados de aceptación
        if self.es_aceptacion:
            radio_interior = self.RADIO - 5.5
            rect_interior = QRectF(
                -radio_interior,
                -radio_interior,
                radio_interior * 2.0,
                radio_interior * 2.0,
            )
            painter.drawEllipse(rect_interior)

        # 5. Etiqueta con el nombre del estado (ej. q0)
        painter.setPen(QColor("#0f172a"))
        fuente = QFont("Segoe UI", 11, QFont.Weight.Bold)
        painter.setFont(fuente)
        painter.drawText(rect_circulo, Qt.AlignmentFlag.AlignCenter, self.nombre)

    def _dibujar_flecha_inicial(self, painter: QPainter) -> None:
        """Dibuja una flecha horizontal formal que apunta al estado desde la izquierda."""
        pluma_inicio = QPen(QColor("#0284c7"), 2.4)
        painter.setPen(pluma_inicio)
        painter.setBrush(QBrush(QColor("#0284c7")))

        longitud_flecha = 28.0
        x_fin = -self.RADIO
        x_inicio = x_fin - longitud_flecha
        y = 0.0

        painter.drawLine(QPointF(x_inicio, y), QPointF(x_fin, y))

        # Punta de flecha triangular apuntando hacia el estado
        tam = 7.0
        punta = QPolygonF([
            QPointF(x_fin, y),
            QPointF(x_fin - tam, y - tam * 0.7),
            QPointF(x_fin - tam, y + tam * 0.7),
        ])
        painter.drawPolygon(punta)

        # Etiqueta "inicio" centrada justo sobre el asta de la flecha
        painter.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        painter.setPen(QColor("#0369a1"))
        rect_texto = QRectF(x_inicio - 2.0, -16.0, longitud_flecha + 4.0, 14.0)
        painter.drawText(rect_texto, Qt.AlignmentFlag.AlignCenter, "inicio")

    def establecer_es_inicial(self, valor: bool) -> None:
        """Actualiza el atributo inicial notificando cambio de geometría."""
        if self.es_inicial != valor:
            self.prepareGeometryChange()
            self.es_inicial = valor
            self.update()

    def establecer_es_aceptacion(self, valor: bool) -> None:
        """Actualiza el atributo de aceptación notificando cambio de geometría."""
        if self.es_aceptacion != valor:
            self.prepareGeometryChange()
            self.es_aceptacion = valor
            self.update()

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: object) -> object:
        """Notifica cambios de posición para que las aristas conectadas se redibujen."""
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            for arista in self.aristas_incidentes:
                arista.actualizar_geometria()
            if self.lienzo:
                pos = self.pos()
                self.lienzo.al_nodo_movido(self.nombre, pos.x(), pos.y())
        return super().itemChange(change, value)

    def contextMenuEvent(self, event: object) -> None:
        """Despliega el menú contextual de clic derecho para editar el estado."""
        menu = QMenu()
        accion_inicial = menu.addAction("Marcar como Inicial (q₀)")
        accion_inicial.setCheckable(True)
        accion_inicial.setChecked(self.es_inicial)

        accion_aceptacion = menu.addAction("Estado de Aceptación (F)")
        accion_aceptacion.setCheckable(True)
        accion_aceptacion.setChecked(self.es_aceptacion)

        menu.addSeparator()
        accion_renombrar = menu.addAction("✏ Renombrar Estado...")
        accion_conectar = menu.addAction("➔ Conectar transición desde aquí...")
        menu.addSeparator()
        accion_eliminar = menu.addAction("🗑 Eliminar Estado")

        pantalla_pos = event.screenPos()
        seleccion = menu.exec(pantalla_pos)

        if seleccion == accion_inicial:
            self.establecer_es_inicial(not self.es_inicial)
            if self.lienzo:
                self.lienzo.al_cambiar_propiedad_nodo(self.nombre, self.es_inicial, self.es_aceptacion)
        elif seleccion == accion_aceptacion:
            self.establecer_es_aceptacion(not self.es_aceptacion)
            if self.lienzo:
                self.lienzo.al_cambiar_propiedad_nodo(self.nombre, self.es_inicial, self.es_aceptacion)
        elif seleccion == accion_renombrar:
            if self.lienzo:
                self.lienzo.solicitar_renombrar_nodo(self)
        elif seleccion == accion_conectar:
            if self.lienzo:
                self.lienzo.iniciar_conexion_desde(self)
        elif seleccion == accion_eliminar:
            if self.lienzo:
                self.lienzo.eliminar_nodo(self)

    def agregar_arista(self, arista: ItemAristaTransicion) -> None:
        """Registra una arista conectada a este nodo."""
        if arista not in self.aristas_incidentes:
            self.aristas_incidentes.append(arista)

    def remover_arista(self, arista: ItemAristaTransicion) -> None:
        """Desvincula una arista de este nodo."""
        if arista in self.aristas_incidentes:
            self.aristas_incidentes.remove(arista)

    def establecer_resaltado(self, resaltar: bool) -> None:
        """Activa o desactiva el resaltado de simulación paso a paso."""
        if self._esta_resaltado != resaltar:
            self._esta_resaltado = resaltar
            self.update()


class ItemAristaTransicion(QGraphicsPathItem):
    """Representa visualmente una transición dirigida entre dos estados.

    Soporta:
    - Flechas dirigidas rectas o curvas entre dos nodos distintos.
    - Curvatura automática cuando existen transiciones de ida y vuelta (bidireccionales).
    - Bucles (*self-loops*) en forma de arco circular superior cuando origen == destino.
    - Puntas de flecha orientadas matemáticamente hacia el perímetro exterior.
    - Etiqueta rectangular estilizada con los símbolos de la transición (ej. '0, 1').
    """

    def __init__(
        self,
        nodo_origen: ItemNodoEstado,
        nodo_destino: ItemNodoEstado,
        simbolos: Set[str] | List[str] | str,
        lienzo: Optional[LienzoGrafo] = None,
    ) -> None:
        super().__init__()
        self.nodo_origen = nodo_origen
        self.nodo_destino = nodo_destino
        self.lienzo = lienzo

        if isinstance(simbolos, str):
            self.simbolos: Set[str] = {s.strip() for s in simbolos.split(",") if s.strip()}
        else:
            self.simbolos = set(simbolos)

        self._es_bucle = (self.nodo_origen == self.nodo_destino)
        self._punto_etiqueta = QPointF(0, 0)
        self._angulo_flecha = 0.0
        self._punto_flecha = QPointF(0, 0)

        # Vincular la arista a ambos nodos
        self.nodo_origen.agregar_arista(self)
        if not self._es_bucle:
            self.nodo_destino.agregar_arista(self)

        self.setZValue(1.0)
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.actualizar_geometria()

    def boundingRect(self) -> QRectF:
        """Área envolvente de la arista calculada a partir de su camino y la etiqueta."""
        camino_rect = self.path().boundingRect()
        margen = 24.0
        return camino_rect.adjusted(-margen, -margen, margen, margen)

    def actualizar_geometria(self) -> None:
        """Recalcula la curva matemática, punta de flecha y posición de la etiqueta."""
        camino = QPainterPath()

        if self._es_bucle:
            self._calcular_geometria_bucle(camino)
        else:
            self._calcular_geometria_transicion_normal(camino)

        self.setPath(camino)
        self.prepareGeometryChange()

    def _calcular_geometria_bucle(self, camino: QPainterPath) -> None:
        """Calcula el lazo curvo superior cuando un estado transiciona a sí mismo."""
        pos = self.nodo_origen.pos()
        r = ItemNodoEstado.RADIO

        # Puntos de salida y entrada sobre el borde superior del círculo
        angulo_salida = math.radians(-50)
        angulo_entrada = math.radians(-130)

        p_salida = QPointF(pos.x() + r * math.cos(angulo_salida), pos.y() + r * math.sin(angulo_salida))
        p_entrada = QPointF(pos.x() + r * math.cos(angulo_entrada), pos.y() + r * math.sin(angulo_entrada))

        # Puntos de control para la curva de Bézier sobre el nodo
        altura_bucle = 48.0
        c1 = QPointF(p_salida.x() + 20, p_salida.y() - altura_bucle)
        c2 = QPointF(p_entrada.x() - 20, p_entrada.y() - altura_bucle)

        camino.moveTo(p_salida)
        camino.cubicTo(c1, c2, p_entrada)

        # Punto para colocar la etiqueta
        self._punto_etiqueta = QPointF(pos.x(), pos.y() - r - altura_bucle + 12)

        # Punta de la flecha en p_entrada
        self._punto_flecha = p_entrada
        # Ángulo hacia donde llega la curva a p_entrada
        tangente = p_entrada - c2
        self._angulo_flecha = math.atan2(tangente.y(), tangente.x())

    def _calcular_geometria_transicion_normal(self, camino: QPainterPath) -> None:
        """Calcula la flecha entre dos nodos distintos con curvatura si hay bidireccionalidad."""
        p_origen = self.nodo_origen.pos()
        p_destino = self.nodo_destino.pos()

        linea = QLineF(p_origen, p_destino)
        longitud = linea.length()
        r = ItemNodoEstado.RADIO

        if longitud < r * 2:
            return

        # Comprobar si existe arista en sentido inverso para curvar y no solaparse
        tiene_retorno = False
        if self.lienzo:
            tiene_retorno = any(
                a.nodo_origen == self.nodo_destino and a.nodo_destino == self.nodo_origen
                for a in self.lienzo.aristas
                if a != self
            )

        dx = (p_destino.x() - p_origen.x()) / longitud
        dy = (p_destino.y() - p_origen.y()) / longitud

        # Vector normal perpendicular
        nx = -dy
        ny = dx

        curvatura = 26.0 if tiene_retorno else 0.0

        p1 = QPointF(p_origen.x() + dx * r, p_origen.y() + dy * r)
        p2 = QPointF(p_destino.x() - dx * r, p_destino.y() - dy * r)

        if tiene_retorno:
            # Curva cuadrática hacia un lado
            p_medio = QPointF(
                (p1.x() + p2.x()) / 2 + nx * curvatura,
                (p1.y() + p2.y()) / 2 + ny * curvatura,
            )
            camino.moveTo(p1)
            camino.quadTo(p_medio, p2)

            self._punto_etiqueta = QPointF(
                (p1.x() + p2.x()) / 2 + nx * (curvatura + 14),
                (p1.y() + p2.y()) / 2 + ny * (curvatura + 14),
            )
            tangente = p2 - p_medio
            self._angulo_flecha = math.atan2(tangente.y(), tangente.x())
        else:
            # Línea recta directa
            camino.moveTo(p1)
            camino.lineTo(p2)

            self._punto_etiqueta = QPointF(
                (p1.x() + p2.x()) / 2 + nx * 14,
                (p1.y() + p2.y()) / 2 + ny * 14,
            )
            tangente = p2 - p1
            self._angulo_flecha = math.atan2(tangente.y(), tangente.x())

        self._punto_flecha = p2

    def paint(
        self,
        painter: QPainter,
        option: object,
        widget: object = None,
    ) -> None:
        """Dibuja la curva, la punta de flecha triangular y la etiqueta de símbolos."""
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        color_arista = QColor("#2563eb") if self.isSelected() else QColor("#475569")
        grosor = 2.4 if self.isSelected() else 1.8

        pluma = QPen(color_arista, grosor)
        painter.setPen(pluma)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(self.path())

        # Dibujar punta de flecha triangular orientada
        self._dibujar_punta_flecha(painter, color_arista)

        # Dibujar etiqueta de texto de los símbolos
        self._dibujar_etiqueta(painter)

    def _dibujar_punta_flecha(self, painter: QPainter, color: QColor) -> None:
        """Dibuja la punta triangular en la llegada al nodo destino."""
        tam = 9.0
        ang = self._angulo_flecha

        p0 = self._punto_flecha
        p1 = QPointF(
            p0.x() - tam * math.cos(ang - math.pi / 6),
            p0.y() - tam * math.sin(ang - math.pi / 6),
        )
        p2 = QPointF(
            p0.x() - tam * math.cos(ang + math.pi / 6),
            p0.y() - tam * math.sin(ang + math.pi / 6),
        )

        pluma = QPen(color, 1.2)
        pincel = QBrush(color)
        painter.setPen(pluma)
        painter.setBrush(pincel)
        painter.drawPolygon(QPolygonF([p0, p1, p2]))

    def _dibujar_etiqueta(self, painter: QPainter) -> None:
        """Dibuja una pequeña pastilla con fondo blanco y el texto de los símbolos."""
        texto = ", ".join(sorted(self.simbolos)) if self.simbolos else "∅"
        fuente = QFont("Segoe UI", 9, QFont.Weight.Bold)
        painter.setFont(fuente)

        # Medir tamaño del texto
        fm = painter.fontMetrics()
        ancho_txt = fm.horizontalAdvance(texto)
        alto_txt = fm.height()

        padding_x = 6
        padding_y = 3
        rect_badge = QRectF(
            self._punto_etiqueta.x() - ancho_txt / 2 - padding_x,
            self._punto_etiqueta.y() - alto_txt / 2 - padding_y,
            ancho_txt + padding_x * 2,
            alto_txt + padding_y * 2,
        )

        # Pastilla de fondo blanco con bordes redondeados
        painter.setPen(QPen(QColor("#cbd5e1"), 1.0))
        painter.setBrush(QBrush(QColor("#ffffff")))
        painter.drawRoundedRect(rect_badge, 4, 4)

        # Texto del símbolo
        painter.setPen(QColor("#0f172a"))
        painter.drawText(rect_badge, Qt.AlignmentFlag.AlignCenter, texto)

    def contextMenuEvent(self, event: object) -> None:
        """Menú contextual para editar o eliminar la transición."""
        menu = QMenu()
        accion_editar = menu.addAction("✏ Editar Símbolos...")
        accion_eliminar = menu.addAction("🗑 Eliminar Transición")

        pantalla_pos = event.screenPos()
        seleccion = menu.exec(pantalla_pos)

        if seleccion == accion_editar:
            if self.lienzo:
                self.lienzo.solicitar_editar_arista(self)
        elif seleccion == accion_eliminar:
            if self.lienzo:
                self.lienzo.eliminar_arista(self)

    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """Doble clic abre el editor de símbolos de la transición."""
        if self.lienzo:
            self.lienzo.solicitar_editar_arista(self)
        super().mouseDoubleClickEvent(event)
