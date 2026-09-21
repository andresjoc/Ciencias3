"""Panel desplazable continuo con el proceso paso a paso de conversión AFN a AFD (Método del Profesor)."""

from __future__ import annotations
from typing import List, Optional, Set

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.model.conversion_nfa_dfa import ResultadoConversionMetodoProfe
from src.view.lienzo_grafo import LienzoGrafo


class PanelPasoAPasoConversion(QWidget):
    """Muestra de manera corrida y continua (single-page scrollable) los 6 pasos

    del método del profesor para convertir un AFN a AFD simplificado.

    Pasos incluidos:
    1. Identificar no determinismo y construir Tabla 1.
    2. Expansión de estados compuestos (unión de transiciones) y Tabla 2.
    3. Notación formal Kn.
    4. Identificación de estados finales y Tabla 3.
    5. Grafo del AFD a partir de Tabla 3 (estático, sin zoom/movimiento, inalcanzables en rojo).
    6. Análisis de accesibilidad (BFS desde K₀) y Tabla 4 Final Simplificada.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.resultado: Optional[ResultadoConversionMetodoProfe] = None
        self.lienzo_tabla3: Optional[LienzoGrafo] = None
        self._inicializar_ui()

    def _inicializar_ui(self) -> None:
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)

        # Contenedor con scroll vertical único y continuo
        self.area_scroll = QScrollArea(self)
        self.area_scroll.setWidgetResizable(True)
        self.area_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.area_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.area_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.widget_contenido = QWidget()
        self.layout_contenido = QVBoxLayout(self.widget_contenido)
        self.layout_contenido.setContentsMargins(16, 16, 16, 16)
        self.layout_contenido.setSpacing(14)

        self.area_scroll.setWidget(self.widget_contenido)
        layout_principal.addWidget(self.area_scroll)

        self._mostrar_estado_inicial_vacio()

    def _limpiar_layout_contenido(self) -> None:
        while self.layout_contenido.count():
            item = self.layout_contenido.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def limpiar(self) -> None:
        """Restablece el contenido a un estado informativo vacío."""
        self.resultado = None
        self.lienzo_tabla3 = None
        self._mostrar_estado_inicial_vacio()

    def _mostrar_estado_inicial_vacio(self) -> None:
        """Muestra un banner informativo cuando aún no se ha ejecutado ninguna conversión."""
        self._limpiar_layout_contenido()

        banner_vacio = QFrame()
        banner_vacio.setStyleSheet(
            "QFrame { background-color: #ffffff; border: 2px dashed #cbd5e1; border-radius: 12px; padding: 40px 20px; }"
        )
        lay_vacio = QVBoxLayout(banner_vacio)
        lay_vacio.setSpacing(10)
        lay_vacio.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icono = QLabel("📐")
        icono.setStyleSheet("font-size: 36px; border: none; background: transparent;")
        icono.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay_vacio.addWidget(icono)

        lbl_tit = QLabel("Proceso Paso a Paso: AFN a AFD")
        lbl_tit.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        lbl_tit.setStyleSheet("color: #1e293b; border: none; background: transparent;")
        lbl_tit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay_vacio.addWidget(lbl_tit)

        lbl_desc = QLabel(
            "Cuando convierta un Autómata Finito No Determinista (AFN) a Determinista (AFD),\n"
            "aquí podrá consultar en una sola vista continua todos los pasos formales:\n"
            "• Tabla 1 (AFN Original)\n"
            "• Tabla 2 (Expansión de Compuestos)\n"
            "• Tabla 3 (Notación Kn y Estados Finales)\n"
            "• Grafo de Tabla 3 (Estados Inalcanzables en Rojo)\n"
            "• Tabla 4 (AFD Final Simplificado y Poda de Inaccesibles)"
        )
        lbl_desc.setFont(QFont("Segoe UI", 10))
        lbl_desc.setStyleSheet("color: #64748b; line-height: 1.5; border: none; background: transparent;")
        lbl_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay_vacio.addWidget(lbl_desc)

        self.layout_contenido.addWidget(banner_vacio)
        self.layout_contenido.addStretch()

    def cargar_resultado(self, resultado: ResultadoConversionMetodoProfe) -> None:
        """Construye y despliega la totalidad de los 6 pasos en la vista desplazable continua."""
        self.resultado = resultado
        self._limpiar_layout(self.layout_contenido)

        # 0. Encabezado principal del proceso
        self._construir_encabezado(resultado)

        # 1. Pasos 1 y 2
        self._construir_paso_1(resultado)
        self._construir_paso_2(resultado)

        # 2. Pasos 3 y 4
        self._construir_paso_3(resultado)
        self._construir_paso_4(resultado)

        # 3. Paso 5: Grafo de Tabla 3 en modo estático puro (inalcanzables en rojo)
        self._construir_paso_5_grafo(resultado)

        # 4. Paso 6: Accesibilidad y Tabla 4 Final
        self._construir_paso_6(resultado)

        self.layout_contenido.addStretch()

    # =========================================================================
    # Secciones Individuales
    # =========================================================================

    def _construir_encabezado(self, res: ResultadoConversionMetodoProfe) -> None:
        encabezado = QFrame()
        encabezado.setStyleSheet(
            "QFrame { background-color: #ffffff; border: 1.5px solid #cbd5e1; "
            "border-radius: 8px; padding: 14px; }"
        )
        lay = QVBoxLayout(encabezado)
        lay.setSpacing(6)

        tit = QLabel("📐 Proceso Formal de Conversión AFN → AFD")
        tit.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        tit.setStyleSheet("color: #0f172a; border: none; background: transparent;")
        lay.addWidget(tit)

        sub = QLabel(
            f"• Alfabeto Σ: {{{', '.join(res.alfabeto)}}}  |  "
            f"• Estados Originales: {len(res.tabla1_afn)}  |  "
            f"• Estados Totales Generados (Kn): {len(res.tabla3_formalizada)}  |  "
            f"• Estados Accesibles Finales: {len(res.tabla4_final)}"
        )
        sub.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        sub.setStyleSheet("color: #047857; border: none; background: transparent;")
        lay.addWidget(sub)

        self.layout_contenido.addWidget(encabezado)

    def _construir_paso_1(self, res: ResultadoConversionMetodoProfe) -> None:
        card = self._crear_tarjeta_seccion("Paso 1: Identificar no-determinismo y construir la Tabla 1")
        lay = card.layout()

        txt = QLabel(
            "Se detectan transiciones a múltiples estados concurrentes {q₁, q₂} ante el mismo símbolo del alfabeto.\n"
            "Se representa la función de transición original del autómata en formato de conjuntos de estados:"
        )
        txt.setStyleSheet("color: #475569; font-size: 11px;")
        lay.addWidget(txt)

        tabla1 = self._crear_tabla_estilizada(
            columnas=["Estado q"] + [f"Entrada {s}" for s in res.alfabeto],
            num_filas=len(res.tabla1_afn),
        )
        for fila_idx, fila in enumerate(res.tabla1_afn):
            it_est = QTableWidgetItem(fila.estado_con_prefijo)
            it_est.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            it_est.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            if fila.es_aceptacion:
                it_est.setForeground(QColor("#059669"))
            if fila.es_inicial:
                it_est.setForeground(QColor("#047857"))
            tabla1.setItem(fila_idx, 0, it_est)

            for c_idx, sim in enumerate(res.alfabeto, start=1):
                dest = fila.transiciones.get(sim, set())
                texto = "{" + ", ".join(sorted(dest)) + "}" if dest else "∅"
                it_d = QTableWidgetItem(texto)
                it_d.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if len(dest) > 1:
                    it_d.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
                    it_d.setForeground(QColor("#b45309"))
                tabla1.setItem(fila_idx, c_idx, it_d)

        lay.addWidget(tabla1)
        self.layout_contenido.addWidget(card)

    def _construir_paso_2(self, res: ResultadoConversionMetodoProfe) -> None:
        card = self._crear_tarjeta_seccion("Paso 2: Unión de transiciones y Tabla 2 (Expansión de estados compuestos)")
        lay = card.layout()

        txt = QLabel(
            "Al existir salidas con conjuntos de múltiples estados (ej. {q₀, q₁}), estos se tratan como estados individuales\n"
            "del nuevo autómata, calculando la unión de sus transiciones: δ({q₀, q₁}, σ) = δ(q₀, σ) ∪ δ(q₁, σ)."
        )
        txt.setStyleSheet("color: #475569; font-size: 11px;")
        lay.addWidget(txt)

        tabla2 = self._crear_tabla_estilizada(
            columnas=["Estado Δ"] + [f"Entrada {s}" for s in res.alfabeto],
            num_filas=len(res.tabla2_expansion),
        )
        for fila_idx, fila in enumerate(res.tabla2_expansion):
            it_est = QTableWidgetItem(fila.nombre_visual)
            it_est.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            it_est.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            if fila.es_compuesto:
                it_est.setForeground(QColor("#b45309"))
            elif fila.es_aceptacion:
                it_est.setForeground(QColor("#059669"))
            tabla2.setItem(fila_idx, 0, it_est)

            for c_idx, sim in enumerate(res.alfabeto, start=1):
                dest = fila.transiciones.get(sim, set())
                texto = "{" + ", ".join(sorted(dest)) + "}" if dest else "∅"
                it_d = QTableWidgetItem(texto)
                it_d.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                tabla2.setItem(fila_idx, c_idx, it_d)

        lay.addWidget(tabla2)
        self.layout_contenido.addWidget(card)

    def _construir_paso_3(self, res: ResultadoConversionMetodoProfe) -> None:
        card = self._crear_tarjeta_seccion("Paso 3: Renombrar estados a la notación formal Kn")
        lay = card.layout()

        txt = QLabel(
            "Se asigna una etiqueta compacta Kn a cada estado simple o compuesto generado:\n"
            "• K₀ = Estado inicial formal (siempre el estado inicial original)\n"
            "• K₁, K₂, ... = Estados simples y compuestos subsiguientes"
        )
        txt.setStyleSheet("color: #475569; font-size: 11px;")
        lay.addWidget(txt)

        # Mapeo resumen
        resumen_box = QFrame()
        resumen_box.setStyleSheet(
            "background-color: #f1f5f9; border: 1px solid #e2e8f0; border-radius: 6px; padding: 8px;"
        )
        lay_res = QVBoxLayout(resumen_box)
        lay_res.setSpacing(4)
        for mapeo in res.mapeo_kn:
            lbl_m = QLabel(f"• <b>{mapeo.etiqueta}</b> = {mapeo.subconjunto_formateado}")
            lbl_m.setStyleSheet("font-size: 11px; color: #0f172a;")
            lay_res.addWidget(lbl_m)
        lay.addWidget(resumen_box)

        self.layout_contenido.addWidget(card)

    def _construir_paso_4(self, res: ResultadoConversionMetodoProfe) -> None:
        card = self._crear_tarjeta_seccion("Paso 4: Identificación de estados finales y Tabla 3 Formalizada")
        lay = card.layout()

        banner_oro = QFrame()
        banner_oro.setStyleSheet(
            "QFrame { background-color: #fefce8; border: 1.5px solid #fde047; border-radius: 6px; padding: 8px; }"
        )
        lay_oro = QVBoxLayout(banner_oro)
        lay_oro.setSpacing(4)
        lbl_oro_tit = QLabel("⭐ Criterio de Aceptación (Estados Finales del AFD):")
        lbl_oro_tit.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        lbl_oro_tit.setStyleSheet("color: #854d0e;")
        lay_oro.addWidget(lbl_oro_tit)

        lbl_oro_txt = QLabel(
            "«Un estado compuesto o renombrado Kn será de aceptación (doble círculo) si y solo si\n"
            "contiene en su conjunto a por lo menos uno de los estados finales de aceptación originales.»"
        )
        lbl_oro_txt.setStyleSheet("color: #713f12; font-size: 11px;")
        lay_oro.addWidget(lbl_oro_txt)
        lay.addWidget(banner_oro)

        tabla3 = self._crear_tabla_estilizada(
            columnas=["Estado Kn", "Composición"] + [f"Entrada {s}" for s in res.alfabeto] + ["¿Es Final?"],
            num_filas=len(res.tabla3_formalizada),
        )
        for fila_idx, f in enumerate(res.tabla3_formalizada):
            it_kn = QTableWidgetItem(f"{'→ ' if f.es_inicial else ''}{f.etiqueta}")
            it_kn.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            it_kn.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            if f.es_inicial:
                it_kn.setForeground(QColor("#047857"))
            elif f.es_final:
                it_kn.setForeground(QColor("#059669"))
            tabla3.setItem(fila_idx, 0, it_kn)

            it_comp = QTableWidgetItem(f.subconjunto_formateado)
            it_comp.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            tabla3.setItem(fila_idx, 1, it_comp)

            for c_idx, sim in enumerate(res.alfabeto, start=2):
                dest_kn = f.transiciones_kn.get(sim, "∅")
                it_d = QTableWidgetItem(dest_kn)
                it_d.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                tabla3.setItem(fila_idx, c_idx, it_d)

            it_fin = QTableWidgetItem(f.explicacion_regla_oro)
            it_fin.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            it_fin.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold if f.es_final else QFont.Weight.Normal))
            it_fin.setForeground(QColor("#059669" if f.es_final else "#64748b"))
            tabla3.setItem(fila_idx, len(res.alfabeto) + 2, it_fin)

        lay.addWidget(tabla3)
        self.layout_contenido.addWidget(card)

    def _construir_paso_5_grafo(self, res: ResultadoConversionMetodoProfe) -> None:
        card = self._crear_tarjeta_seccion("Paso 5: Grafo del AFD (Tabla 3 con Inalcanzables en ROJO)")
        lay = card.layout()

        txt = QLabel(
            "• Se trazan todos los estados formalizados en la Tabla 3.\n"
            "• Modo puramente visual: El grafo se presenta estático y distribuido armónicamente.\n"
            "• Los estados que resultan inalcanzables desde K₀ se señalan en ROJO para justificar la poda del Paso 6."
        )
        txt.setStyleSheet("color: #475569; font-size: 11px;")
        lay.addWidget(txt)

        # Marco visual con leyenda y grafo estático
        marco_grafo = QFrame()
        marco_grafo.setStyleSheet(
            "QFrame { background-color: #ffffff; border: 1.5px solid #cbd5e1; border-radius: 8px; }"
        )
        lay_g = QVBoxLayout(marco_grafo)
        lay_g.setContentsMargins(10, 10, 10, 10)
        lay_g.setSpacing(8)

        # Pastillas informativas de la leyenda
        barra_leg = QHBoxLayout()
        barra_leg.setSpacing(6)

        lbl_tit_g = QLabel("Grafo Completo (Tabla 3):")
        lbl_tit_g.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        lbl_tit_g.setStyleSheet("color: #0f172a;")
        barra_leg.addWidget(lbl_tit_g)

        lbl_leg_ini = QLabel("➔ → K₀ (Inicial)")
        lbl_leg_ini.setStyleSheet(
            "color: #065f46; font-weight: 600; font-size: 10.5px; background: #ecfdf5; "
            "border: 1px solid #a7f3d0; padding: 2px 6px; border-radius: 4px;"
        )
        barra_leg.addWidget(lbl_leg_ini)

        lbl_leg_alc = QLabel("🟢 Kₙ Alcanzable")
        lbl_leg_alc.setStyleSheet(
            "color: #166534; font-weight: 600; font-size: 10.5px; background: #f0fdf4; "
            "border: 1px solid #bbf7d0; padding: 2px 6px; border-radius: 4px;"
        )
        barra_leg.addWidget(lbl_leg_alc)

        lbl_leg_inacc = QLabel("🔴 Kₙ Inalcanzable (Rojo)")
        lbl_leg_inacc.setStyleSheet(
            "color: #b91c1c; font-weight: 600; font-size: 10.5px; background: #fef2f2; "
            "border: 1px solid #fecaca; padding: 2px 6px; border-radius: 4px;"
        )
        barra_leg.addWidget(lbl_leg_inacc)

        lbl_leg_doble = QLabel("⭕ Doble Círculo (Final)")
        lbl_leg_doble.setStyleSheet(
            "color: #475569; font-weight: 600; font-size: 10.5px; background: #f8fafc; "
            "border: 1px solid #e2e8f0; padding: 2px 6px; border-radius: 4px;"
        )
        barra_leg.addWidget(lbl_leg_doble)
        barra_leg.addStretch()
        lay_g.addLayout(barra_leg)

        # Visor del grafo en MODO ESTÁTICO PURO (sin zoom, sin mover nodos, sin botones)
        lienzo = LienzoGrafo(parent=marco_grafo, solo_lectura=True, modo_estatico=True)
        self.lienzo_tabla3 = lienzo
        lienzo.setMinimumHeight(320)
        lienzo.establecer_alfabeto_permitido(res.alfabeto)

        estados_tabla3 = [f.etiqueta for f in res.tabla3_formalizada]
        estado_inicial_tabla3 = next((f.etiqueta for f in res.tabla3_formalizada if f.es_inicial), "K0")
        estados_aceptacion_tabla3 = {f.etiqueta for f in res.tabla3_formalizada if f.es_final}
        estados_inalcanzables_set = set(res.accesibilidad.estados_inalcanzables)
        estados_alcanzables_set = set(res.accesibilidad.estados_alcanzables)

        transiciones_tabla3 = {}
        for f in res.tabla3_formalizada:
            trans_est = {}
            for sim, dest in f.transiciones_kn.items():
                if dest:
                    trans_est[sim] = dest
            transiciones_tabla3[f.etiqueta] = trans_est

        lienzo.sincronizar_desde_modelo(
            estados=estados_tabla3,
            transiciones=transiciones_tabla3,
            estado_inicial=estado_inicial_tabla3,
            estados_aceptacion=estados_aceptacion_tabla3,
            estados_inalcanzables=estados_inalcanzables_set,
            estados_alcanzables=estados_alcanzables_set,
        )
        lienzo.auto_organizar_nodos()
        lay_g.addWidget(lienzo)
        lay.addWidget(marco_grafo)

        if res.accesibilidad.estados_inalcanzables:
            inacc_str = ", ".join(res.accesibilidad.estados_inalcanzables)
            alerta = QFrame()
            alerta.setStyleSheet(
                "QFrame { background-color: #fef2f2; border: 1.5px solid #f87171; border-radius: 6px; padding: 8px; }"
            )
            lay_al = QVBoxLayout(alerta)
            lbl_al_t = QLabel(f"⚠️ Detección Visual de Estados Inalcanzables: {inacc_str}")
            lbl_al_t.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            lbl_al_t.setStyleSheet("color: #991b1b;")
            lay_al.addWidget(lbl_al_t)

            lbl_al_d = QLabel(
                "No existe ninguna secuencia de entradas ni camino dirigido que parta desde el estado inicial (K₀) "
                "y alcance a estos nodos. Quedan desconectados de la computación útil y se eliminan en el Paso 6."
            )
            lbl_al_d.setStyleSheet("color: #7f1d1d; font-size: 10.5px;")
            lay_al.addWidget(lbl_al_d)
            lay.addWidget(alerta)

        self.layout_contenido.addWidget(card)

    def _construir_paso_6(self, res: ResultadoConversionMetodoProfe) -> None:
        card = self._crear_tarjeta_seccion("Paso 6: Accesibilidad y Tabla 4 Final Simplificada")
        lay = card.layout()

        txt = QLabel(
            "Mediante búsqueda en anchura (BFS) desde el estado inicial K₀, se determina el conjunto de estados accesibles.\n"
            "Se descartan todas las filas y transiciones correspondientes a los estados inalcanzables identificados:"
        )
        txt.setStyleSheet("color: #475569; font-size: 11px;")
        lay.addWidget(txt)

        # Resumen de accesibilidad
        marco_acc = QFrame()
        marco_acc.setStyleSheet(
            "background-color: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 6px; padding: 8px;"
        )
        lay_acc = QVBoxLayout(marco_acc)
        lay_acc.setSpacing(4)
        lbl_acc = QLabel(f"• <b>Estados Alcanzables (Conservados):</b> {', '.join(res.accesibilidad.estados_alcanzables)}")
        lbl_acc.setStyleSheet("color: #166534; font-size: 11px;")
        lay_acc.addWidget(lbl_acc)

        if res.accesibilidad.estados_inalcanzables:
            lbl_inacc = QLabel(f"• <b>Estados Inalcanzables (Podados):</b> {', '.join(res.accesibilidad.estados_inalcanzables)}")
            lbl_inacc.setStyleSheet("color: #991b1b; font-size: 11px;")
            lay_acc.addWidget(lbl_inacc)
        else:
            lbl_inacc = QLabel("• <b>Estados Inalcanzables:</b> Ninguno (todos los estados generados son accesibles)")
            lbl_inacc.setStyleSheet("color: #166534; font-size: 11px;")
            lay_acc.addWidget(lbl_inacc)
        lay.addWidget(marco_acc)

        # Tabla 4
        lbl_t4 = QLabel("Tabla 4: AFD Determinista Final Simplificado")
        lbl_t4.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        lbl_t4.setStyleSheet("color: #059669; margin-top: 6px;")
        lay.addWidget(lbl_t4)

        tabla4 = self._crear_tabla_estilizada(
            columnas=["Estado Kn", "Composición"] + [f"Entrada {s}" for s in res.alfabeto] + ["¿Es Final?"],
            num_filas=len(res.tabla4_final),
        )
        for fila_idx, f in enumerate(res.tabla4_final):
            it_kn = QTableWidgetItem(f"{'→ ' if f.es_inicial else ''}{f.etiqueta}")
            it_kn.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            it_kn.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            if f.es_inicial:
                it_kn.setForeground(QColor("#047857"))
            elif f.es_final:
                it_kn.setForeground(QColor("#059669"))
            tabla4.setItem(fila_idx, 0, it_kn)

            it_comp = QTableWidgetItem(f.subconjunto_formateado)
            it_comp.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            tabla4.setItem(fila_idx, 1, it_comp)

            for c_idx, sim in enumerate(res.alfabeto, start=2):
                dest_kn = f.transiciones_kn.get(sim, "∅")
                it_d = QTableWidgetItem(dest_kn)
                it_d.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                tabla4.setItem(fila_idx, c_idx, it_d)

            it_fin = QTableWidgetItem("SÍ (Final)" if f.es_final else "No")
            it_fin.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            it_fin.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold if f.es_final else QFont.Weight.Normal))
            it_fin.setForeground(QColor("#059669" if f.es_final else "#64748b"))
            tabla4.setItem(fila_idx, len(res.alfabeto) + 2, it_fin)

        lay.addWidget(tabla4)
        self.layout_contenido.addWidget(card)

    # =========================================================================
    # Helpers Visuales
    # =========================================================================

    def _crear_tarjeta_seccion(self, titulo: str) -> QFrame:
        """Crea un contenedor estilizado tipo tarjeta para agrupar visualmente cada paso."""
        tarjeta = QFrame()
        tarjeta.setStyleSheet(
            "QFrame { background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; }"
        )
        layout = QVBoxLayout(tarjeta)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        lbl_tit = QLabel(titulo)
        lbl_tit.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        lbl_tit.setStyleSheet("color: #1e293b; border: none; background: transparent;")
        layout.addWidget(lbl_tit)

        return tarjeta

    def _crear_tabla_estilizada(self, columnas: List[str], num_filas: int) -> QTableWidget:
        """Crea una tabla con diseño limpio y compacto para la vista scrolleable."""
        tabla = QTableWidget()
        tabla.setColumnCount(len(columnas))
        tabla.setHorizontalHeaderLabels(columnas)
        tabla.setRowCount(num_filas)
        tabla.setAlternatingRowColors(True)
        tabla.setStyleSheet(
            "QTableWidget { gridline-color: #e2e8f0; font-size: 11px; background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 4px; }"
            "QHeaderView::section { background-color: #f1f5f9; font-weight: bold; color: #1e293b; padding: 4px; }"
        )
        tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        altura = min(200, 36 + num_filas * 28)
        tabla.setMinimumHeight(altura)
        return tabla

    def _limpiar_layout(self, layout: QVBoxLayout) -> None:
        """Elimina todos los widgets hijos de un layout de forma segura."""
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            elif item.layout() is not None:
                self._limpiar_layout(item.layout())  # type: ignore[arg-type]
