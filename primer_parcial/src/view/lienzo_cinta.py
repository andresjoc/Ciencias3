"""Lienzo gráfico (QGraphicsView) para la visualización de Cinta y Unidad de Control."""

from __future__ import annotations
from typing import Optional, Union

from PyQt6.QtCore import QPointF, QRectF, Qt
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
    QGraphicsScene,
    QGraphicsView,
    QWidget,
)

from src.model.automata import ResultadoTraza
from src.model.automata_nfa import ResultadoTrazaNFA, RamaTrazaNFA


class LienzoCinta(QGraphicsView):
    """Lienzo para renderizar el diagrama de Cinta (nivel superior) y Control (nivel inferior).

    Estructura visual según specs/mission.md:
    - Nivel superior (Cinta):
      * Tira horizontal de celdas cuadradas con la cadena u.
      * Llave horizontal superior que agrupa los símbolos de u.
      * Celda delimitadora de fin de cadena (≡).
      * Borde derecho abierto con puntos suspensivos (…).
    - Nivel inferior (Unidad de Control):
      * DFA: Cajas cuadradas individuales con los estados y flecha ascendente hacia la celda activa.
      * NFA: Ramas de cómputo paralelas dispuestas verticalmente (árbol/bifurcaciones).
        - Ramas completas que alcanzan ≡ (marcando aceptación o rechazo).
        - Ramas abortadas prematuramente que se truncan con ∅ ante transiciones indefinidas.
    """

    TAMANO_CELDA = 55
    ESPACIO_VERTICAL = 75
    ESPACIO_ENTRE_RAMAS = 60
    MARGEN_IZQUIERDO = 75
    MARGEN_SUPERIOR = 60

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._escena = QGraphicsScene(self)
        self.setScene(self._escena)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        self.setBackgroundBrush(QBrush(QColor("#ffffff")))

        self._traza: Optional[Union[ResultadoTraza, ResultadoTrazaNFA]] = None
        self._paso_actual: int = 0
        self._cadena_actual: str = ""

        self.actualizar_vista()

    def establecer_traza(
        self,
        traza: Optional[Union[ResultadoTraza, ResultadoTrazaNFA]],
        paso_actual: int = 0,
        cadena: str = "",
    ) -> None:
        """Configura los datos de la traza de ejecución y el paso actual a visualizar.

        Args:
            traza: ResultadoTraza (DFA) o ResultadoTrazaNFA (NFA), o None.
            paso_actual: Índice del paso activo actual (0 hasta N).
            cadena: Cadena de entrada u.
        """
        self._traza = traza
        self._paso_actual = paso_actual
        self._cadena_actual = cadena if traza is None else traza.cadena_entrada
        self.actualizar_vista()

    def actualizar_vista(self) -> None:
        """Redibuja completamente la escena con la cinta, llave, flechas y estados."""
        self._escena.clear()

        # Si no hay cadena ni traza, mostrar mensaje guía
        if not self._cadena_actual and self._traza is None:
            self._dibujar_estado_espera()
            return

        cadena = self._cadena_actual
        total_simbolos = len(cadena)
        paso_activo = self._paso_actual

        # 1. Dibujar llave superior { sobre la entrada u (si u no está vacía)
        if total_simbolos > 0:
            self._dibujar_llave_superior(total_simbolos)

        # 2. Dibujar celdas de la cinta superior
        for i, caracter in enumerate(cadena):
            es_activa = (i == paso_activo)
            self._dibujar_celda_cinta(
                indice=i,
                texto=caracter,
                es_activa=es_activa,
            )

        # 3. Celda delimitadora de fin de cadena (≡)
        indice_delimitador = total_simbolos
        es_delimitador_activo = (paso_activo == indice_delimitador)
        self._dibujar_celda_cinta(
            indice=indice_delimitador,
            texto="≡",
            es_activa=es_delimitador_activo,
            es_delimitador=True,
        )

        # 4. Extremo derecho abierto con puntos suspensivos (…)
        self._dibujar_extremo_abierto(indice_delimitador + 1)

        # 5. Nivel inferior: Unidad de Control (DFA o NFA)
        if self._traza is not None:
            if isinstance(self._traza, ResultadoTrazaNFA):
                self._dibujar_unidades_control_nfa()
            elif isinstance(self._traza, ResultadoTraza) and self._traza.pasos:
                self._dibujar_unidad_control_dfa()

        # Ajustar dimensiones de la escena con márgenes
        rect_items = self._escena.itemsBoundingRect()
        self._escena.setSceneRect(
            rect_items.adjusted(-30, -30, 40, 40)
        )

    def _dibujar_estado_espera(self) -> None:
        """Dibuja un texto indicativo cuando no hay simulación activa."""
        texto = self._escena.addText("Ingrese una cadena y presione 'Iniciar Simulación' para visualizar.")
        texto.setDefaultTextColor(QColor("#94a3b8"))
        texto.setFont(QFont("Segoe UI", 12, QFont.Weight.Medium))
        texto.setPos(50, 60)
        self._escena.setSceneRect(0, 0, 500, 160)

    def _dibujar_llave_superior(self, total_simbolos: int) -> None:
        """Dibuja una llave horizontal superior { que agrupa la palabra u."""
        x_inicio = self.MARGEN_IZQUIERDO
        ancho_total = total_simbolos * self.TAMANO_CELDA
        x_fin = x_inicio + ancho_total
        x_medio = (x_inicio + x_fin) / 2
        y_base = self.MARGEN_SUPERIOR - 8
        altura_llave = 12

        camino = QPainterPath()
        camino.moveTo(x_inicio, y_base)
        camino.quadTo(x_inicio + 5, y_base - altura_llave / 2, (x_inicio + x_medio) / 2, y_base - altura_llave / 2)
        camino.quadTo(x_medio - 5, y_base - altura_llave / 2, x_medio, y_base - altura_llave)
        camino.quadTo(x_medio + 5, y_base - altura_llave / 2, (x_fin + x_medio) / 2, y_base - altura_llave / 2)
        camino.quadTo(x_fin - 5, y_base - altura_llave / 2, x_fin, y_base)

        pluma = QPen(QColor("#334155"), 1.8)
        self._escena.addPath(camino, pluma)

        etiqueta_u = self._escena.addText("u")
        etiqueta_u.setDefaultTextColor(QColor("#0f172a"))
        fuente_u = QFont("Segoe UI", 11, QFont.Weight.Bold)
        fuente_u.setItalic(True)
        etiqueta_u.setFont(fuente_u)
        etiqueta_u.setPos(x_medio - 7, y_base - altura_llave - 22)

    def _dibujar_celda_cinta(
        self,
        indice: int,
        texto: str,
        es_activa: bool = False,
        es_delimitador: bool = False,
    ) -> None:
        """Dibuja una celda cuadrada contigua de la cinta superior."""
        x = self.MARGEN_IZQUIERDO + (indice * self.TAMANO_CELDA)
        y = self.MARGEN_SUPERIOR

        rect = QRectF(x, y, self.TAMANO_CELDA, self.TAMANO_CELDA)

        if es_activa:
            color_fondo = QColor("#fef08a")  # Amarillo resaltado para celda activa
            color_borde = QColor("#ca8a04")
            ancho_borde = 2.0
        elif es_delimitador:
            color_fondo = QColor("#f1f5f9")
            color_borde = QColor("#64748b")
            ancho_borde = 1.5
        else:
            color_fondo = QColor("#ffffff")
            color_borde = QColor("#94a3b8")
            ancho_borde = 1.2

        pluma = QPen(color_borde, ancho_borde)
        pincel = QBrush(color_fondo)
        self._escena.addRect(rect, pluma, pincel)

        item_texto = self._escena.addText(texto)
        if es_delimitador:
            item_texto.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
            item_texto.setDefaultTextColor(QColor("#334155"))
        else:
            item_texto.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
            item_texto.setDefaultTextColor(QColor("#0f172a"))

        rect_texto = item_texto.boundingRect()
        pos_x = x + (self.TAMANO_CELDA - rect_texto.width()) / 2
        pos_y = y + (self.TAMANO_CELDA - rect_texto.height()) / 2
        item_texto.setPos(pos_x, pos_y)

    def _dibujar_extremo_abierto(self, indice_inicio: int) -> None:
        """Dibuja el borde derecho abierto con puntos suspensivos (…)"""
        x = self.MARGEN_IZQUIERDO + (indice_inicio * self.TAMANO_CELDA)
        y = self.MARGEN_SUPERIOR
        ancho_abierto = self.TAMANO_CELDA * 0.9

        pluma = QPen(QColor("#94a3b8"), 1.2)
        self._escena.addLine(x, y, x + ancho_abierto, y, pluma)
        self._escena.addLine(x, y + self.TAMANO_CELDA, x + ancho_abierto, y + self.TAMANO_CELDA, pluma)

        item_puntos = self._escena.addText("…")
        item_puntos.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        item_puntos.setDefaultTextColor(QColor("#94a3b8"))
        rect_puntos = item_puntos.boundingRect()
        pos_x = x + (ancho_abierto - rect_puntos.width()) / 2
        pos_y = y + (self.TAMANO_CELDA - rect_puntos.height()) / 2
        item_puntos.setPos(pos_x, pos_y)

    def _dibujar_unidad_control_dfa(self) -> None:
        """Dibuja las cajas de estado y flechas verticales para DFA."""
        assert isinstance(self._traza, ResultadoTraza)
        pasos = self._traza.pasos
        paso_activo = self._paso_actual

        y_caja = self.MARGEN_SUPERIOR + self.TAMANO_CELDA + self.ESPACIO_VERTICAL
        y_flecha_fin = self.MARGEN_SUPERIOR + self.TAMANO_CELDA

        for idx in range(min(paso_activo + 1, len(pasos))):
            paso = pasos[idx]
            es_paso_activo = (idx == paso_activo)

            x_centro_celda = self.MARGEN_IZQUIERDO + (idx * self.TAMANO_CELDA) + (self.TAMANO_CELDA / 2)
            ancho_caja = 46
            alto_caja = 40
            x_caja = x_centro_celda - (ancho_caja / 2)

            rect_caja = QRectF(x_caja, y_caja, ancho_caja, alto_caja)

            if es_paso_activo:
                if idx == len(pasos) - 1:
                    if self._traza.aceptada:
                        color_fondo = QColor("#bbf7d0")  # Verde aceptación
                        color_borde = QColor("#16a34a")
                    else:
                        color_fondo = QColor("#fecaca")  # Rojo rechazo
                        color_borde = QColor("#dc2626")
                else:
                    color_fondo = QColor("#dbeafe")  # Azul activo
                    color_borde = QColor("#2563eb")
                ancho_borde = 2.2
            else:
                color_fondo = QColor("#f8fafc")
                color_borde = QColor("#94a3b8")
                ancho_borde = 1.2

            pluma_caja = QPen(color_borde, ancho_borde)
            pincel_caja = QBrush(color_fondo)
            self._escena.addRect(rect_caja, pluma_caja, pincel_caja)

            texto_estado = self._escena.addText(paso.estado_actual)
            texto_estado.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
            texto_estado.setDefaultTextColor(QColor("#0f172a"))
            rect_txt = texto_estado.boundingRect()
            texto_estado.setPos(
                x_caja + (ancho_caja - rect_txt.width()) / 2,
                y_caja + (alto_caja - rect_txt.height()) / 2,
            )

            if es_paso_activo:
                self._dibujar_flecha_ascendente(
                    x=x_centro_celda,
                    y_inicio=y_caja,
                    y_fin=y_flecha_fin + 3,
                    color=color_borde,
                )

    def _dibujar_unidades_control_nfa(self) -> None:
        """Dibuja ramas de cómputo paralelas para NFA con bifurcaciones y truncamientos."""
        assert isinstance(self._traza, ResultadoTrazaNFA)
        ramas = self._traza.ramas
        paso_activo = self._paso_actual
        total_simbolos = len(self._cadena_actual)
        y_flecha_fin = self.MARGEN_SUPERIOR + self.TAMANO_CELDA

        ancho_caja = 46
        alto_caja = 40

        for idx_rama, rama in enumerate(ramas):
            y_caja = (
                self.MARGEN_SUPERIOR
                + self.TAMANO_CELDA
                + self.ESPACIO_VERTICAL
                + (idx_rama * self.ESPACIO_ENTRE_RAMAS)
            )

            # Etiqueta lateral para identificar la rama
            etiqueta_rama = self._escena.addText(f"Rama {rama.id_rama}")
            etiqueta_rama.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            etiqueta_rama.setDefaultTextColor(QColor("#64748b"))
            etiqueta_rama.setPos(self.MARGEN_IZQUIERDO - 68, y_caja + 10)

            # Conector gráfico hacia la rama padre si bifurcó
            if rama.id_padre is not None:
                padre = next((r for r in ramas if r.id_rama == rama.id_padre), None)
                if padre is not None:
                    idx_padre = ramas.index(padre)
                    y_padre = (
                        self.MARGEN_SUPERIOR
                        + self.TAMANO_CELDA
                        + self.ESPACIO_VERTICAL
                        + (idx_padre * self.ESPACIO_ENTRE_RAMAS)
                    )
                    # Dibujar línea tenue de bifurcación
                    paso_nacimiento = (
                        rama.pasos[0].indice_paso if len(rama.camino) <= 2
                        else rama.pasos[len(rama.camino) - 2].indice_paso
                    )
                    if paso_nacimiento <= paso_activo:
                        x_bif = (
                            self.MARGEN_IZQUIERDO
                            + (paso_nacimiento * self.TAMANO_CELDA)
                            + (self.TAMANO_CELDA / 2)
                        )
                        pluma_bif = QPen(QColor("#cbd5e1"), 1.5, Qt.PenStyle.DashLine)
                        self._escena.addLine(x_bif, y_padre + alto_caja, x_bif, y_caja, pluma_bif)

            # Dibujar los pasos de esta rama que hayan ocurrido hasta paso_activo
            for paso in rama.pasos:
                idx = paso.indice_paso
                if idx > paso_activo:
                    continue

                x_centro = self.MARGEN_IZQUIERDO + (idx * self.TAMANO_CELDA) + (self.TAMANO_CELDA / 2)
                x_caja = x_centro - (ancho_caja / 2)
                rect_caja = QRectF(x_caja, y_caja, ancho_caja, alto_caja)

                es_paso_abortado = (rama.es_abortada and idx == rama.indice_aborto)
                es_paso_terminal = (idx == total_simbolos)
                es_paso_activo = (idx == paso_activo)

                # Estilos visuales
                if es_paso_abortado:
                    # Rama truncada prematuramente ante transición vacía ∅
                    color_fondo = QColor("#fee2e2")
                    color_borde = QColor("#ef4444")
                    ancho_borde = 1.8
                    estilo_linea = Qt.PenStyle.DashLine
                elif es_paso_terminal and paso_activo == total_simbolos:
                    # Rama completa en la celda ≡
                    if rama.es_aceptada:
                        color_fondo = QColor("#bbf7d0")  # Verde aceptación
                        color_borde = QColor("#16a34a")
                    else:
                        color_fondo = QColor("#fecaca")  # Rojo rechazo
                        color_borde = QColor("#dc2626")
                    ancho_borde = 2.2
                    estilo_linea = Qt.PenStyle.SolidLine
                elif es_paso_activo:
                    color_fondo = QColor("#dbeafe")  # Azul activo
                    color_borde = QColor("#2563eb")
                    ancho_borde = 2.2
                    estilo_linea = Qt.PenStyle.SolidLine
                else:
                    color_fondo = QColor("#f8fafc")
                    color_borde = QColor("#94a3b8")
                    ancho_borde = 1.2
                    estilo_linea = Qt.PenStyle.SolidLine

                pluma_caja = QPen(color_borde, ancho_borde, estilo_linea)
                pincel_caja = QBrush(color_fondo)
                self._escena.addRect(rect_caja, pluma_caja, pincel_caja)

                # Texto del estado dentro de la caja
                texto_estado = self._escena.addText(paso.estado_actual)
                texto_estado.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
                texto_estado.setDefaultTextColor(QColor("#0f172a"))
                rect_txt = texto_estado.boundingRect()
                texto_estado.setPos(
                    x_caja + (ancho_caja - rect_txt.width()) / 2,
                    y_caja + (alto_caja - rect_txt.height()) / 2,
                )

                # Indicador de aborto (∅) o aceptación (✓ / ✗)
                if es_paso_abortado:
                    insignia_aborto = self._escena.addText("∅")
                    insignia_aborto.setFont(QFont("Segoe UI", 10, QFont.Weight.Black))
                    insignia_aborto.setDefaultTextColor(QColor("#dc2626"))
                    insignia_aborto.setPos(x_caja + ancho_caja - 14, y_caja - 10)
                elif es_paso_terminal and paso_activo == total_simbolos:
                    simbolo_fin = "✓" if rama.es_aceptada else "✗"
                    color_simbolo = QColor("#15803d") if rama.es_aceptada else QColor("#b91c1c")
                    insignia_fin = self._escena.addText(simbolo_fin)
                    insignia_fin.setFont(QFont("Segoe UI", 10, QFont.Weight.Black))
                    insignia_fin.setDefaultTextColor(color_simbolo)
                    insignia_fin.setPos(x_caja + ancho_caja - 14, y_caja - 10)

                # Flecha vertical ascendente (↑) si este paso está activo en la celda correspondiente
                if es_paso_activo and not es_paso_abortado:
                    if idx_rama == 0:
                        self._dibujar_flecha_ascendente(
                            x=x_centro,
                            y_inicio=y_caja,
                            y_fin=y_flecha_fin + 3,
                            color=color_borde,
                        )
                    else:
                        # Flecha ascendente local desde la caja de esta rama
                        self._dibujar_flecha_ascendente(
                            x=x_centro,
                            y_inicio=y_caja,
                            y_fin=y_caja - 20,
                            color=color_borde,
                        )

    def _dibujar_flecha_ascendente(
        self,
        x: float,
        y_inicio: float,
        y_fin: float,
        color: QColor,
    ) -> None:
        """Dibuja una flecha vertical ascendente (↑) hacia la celda activa."""
        pluma = QPen(color, 2.4)
        self._escena.addLine(x, y_inicio, x, y_fin, pluma)

        # Punta de flecha triangular apuntando hacia arriba
        tam_punta = 8.0
        punta = QPolygonF([
            QPointF(x, y_fin),
            QPointF(x - tam_punta / 1.5, y_fin + tam_punta),
            QPointF(x + tam_punta / 1.5, y_fin + tam_punta),
        ])
        pincel = QBrush(color)
        self._escena.addPolygon(punta, pluma, pincel)
