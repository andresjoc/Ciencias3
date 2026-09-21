"""Diálogo interactivo que muestra el Procedimiento de Conversión de AFN a AFD tal cual la guía del profesor."""

from __future__ import annotations
from typing import List, Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.model.automata_nfa import AutomataNFA
from src.model.conversion_nfa_dfa import (
    ConvertidorSubconjuntos,
    FilaMapeoKn,
    ResultadoConversionMetodoProfe,
)
from src.view.lienzo_grafo import LienzoGrafo


class DialogoConversionDFA(QDialog):
    """Muestra el Procedimiento de Conversión: AFN a AFD (Método de Subconjuntos del Profesor).

    Sigue estrictamente la estructura descrita en 'guiiadeconversionAFNtoAFN.md':
    - Paso 1: Tabla 1 - Transiciones del AFN inicial
    - Paso 2: Tabla 2 - Expansión de estados compuestos
    - Paso 3: Tabla de renombrado a la notación Kn
    - Paso 4: Identificación de estados finales y Tabla 3 formalizada con columna '¿Es Final?'
    - Paso 5: Instrucciones de dibujo ("Pintar") y Grafo interactivo con estados inalcanzables en rojo
    - Paso 6: Rastreo de accesibilidad, poda de inalcanzables y Tabla 4 final simplificada.
    """

    aplicar_afd_solicitado = pyqtSignal(object)

    def __init__(
        self,
        nfa: AutomataNFA,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.nfa = nfa
        self.resultado: Optional[ResultadoConversionMetodoProfe] = None

        self.setWindowTitle("Procedimiento de Conversión: AFN a AFD")
        self.resize(1040, 740)
        self.setMinimumSize(880, 580)

        self._calcular_conversion()
        self._inicializar_ui()

    def _calcular_conversion(self) -> None:
        """Ejecuta el algoritmo del profesor sobre el AFN."""
        self.resultado = ConvertidorSubconjuntos.convertir(self.nfa)

    def _inicializar_ui(self) -> None:
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(16, 14, 16, 14)
        layout_principal.setSpacing(10)

        # 1. Cabecera formal
        marco_cabecera = QFrame()
        marco_cabecera.setStyleSheet(
            "QFrame { background-color: #f8fafc; border: 1.5px solid #cbd5e1; border-radius: 8px; padding: 10px; }"
        )
        layout_cab = QVBoxLayout(marco_cabecera)
        layout_cab.setSpacing(4)

        titulo = QLabel("Procedimiento de Conversión: AFN a AFD")
        titulo.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        titulo.setStyleSheet("color: #0f172a;")
        layout_cab.addWidget(titulo)

        subtitulo = QLabel(
            "Equivalencia por estados Kn (K₀, K₁, K₂...) y determinación formal de estados de aceptación."
        )
        subtitulo.setStyleSheet("color: #475569; font-size: 11px;")
        layout_cab.addWidget(subtitulo)

        if self.resultado:
            res = self.resultado
            q_orig_str = "{" + ", ".join(res.estados_nfa_originales) + "}"
            f_orig_str = "{" + ", ".join(sorted(res.estados_aceptacion_nfa)) + "}" if res.estados_aceptacion_nfa else "∅"
            resumen = QLabel(
                f"AFN Base: Q = {q_orig_str} | Σ = {{{', '.join(res.alfabeto)}}} | Estado inicial = → {res.estado_inicial_nfa} | Finales F = {f_orig_str}"
            )
            resumen.setStyleSheet("color: #047857; font-weight: 600; font-size: 11px; margin-top: 2px;")
            layout_cab.addWidget(resumen)

        layout_principal.addWidget(marco_cabecera)

        # 2. Pestañas de pasos del método
        self.pestanas = QTabWidget()
        self.pestanas.setStyleSheet(
            "QTabBar::tab { font-weight: bold; font-size: 11px; padding: 8px 16px; }"
            "QTabBar::tab:selected { color: #047857; border-bottom: 2px solid #059669; }"
        )

        # Pestaña 1: Pasos 1 y 2 (Tablas 1 y 2)
        self.pestanas.addTab(self._crear_pestana_pasos_1_y_2(), "📋 Pasos 1 y 2: Tablas AFN y Expansión")

        # Pestaña 2: Pasos 3 y 4 (Notación Kn y Estados Finales)
        self.pestanas.addTab(self._crear_pestana_pasos_3_y_4(), "🏷️ Pasos 3 y 4: Notación Kn y Estados Finales")

        # Pestaña 3: Pasos 5 y 6 (Poda de Inalcanzables y Tabla 4 Final)
        self.pestanas.addTab(self._crear_pestana_pasos_5_y_6(), "⚡ Pasos 5 y 6: Grafo y AFD Final Simplificado")

        layout_principal.addWidget(self.pestanas, stretch=1)

        # 3. Barra de botones inferior
        layout_botones = QHBoxLayout()
        layout_botones.setSpacing(10)

        etiqueta_info = QLabel("Puede inspeccionar cada paso de la demostración formal en las pestañas superiores.")
        etiqueta_info.setStyleSheet("color: #64748b; font-size: 11px;")
        layout_botones.addWidget(etiqueta_info)

        layout_botones.addStretch()

        self.boton_aplicar = QPushButton("✔ Aplicar AFD al Editor y Matriz (Notación Kn)")
        self.boton_aplicar.setStyleSheet(
            "QPushButton { background-color: #059669; color: white; font-weight: bold; "
            "padding: 8px 18px; border-radius: 6px; font-size: 12px; }"
            "QPushButton:hover { background-color: #047857; }"
            "QPushButton:pressed { background-color: #064e3b; }"
        )
        self.boton_aplicar.setToolTip(
            "Sustituye el autómata actual por el AFD final simplificado en notación Kn (Tabla 4),\n"
            "actualizando inmediatamente el lienzo gráfico con distribución circular y la matriz de transiciones."
        )
        self.boton_aplicar.clicked.connect(self._al_aplicar_afd)
        layout_botones.addWidget(self.boton_aplicar)

        self.boton_cerrar = QPushButton("Cerrar")
        self.boton_cerrar.setStyleSheet(
            "QPushButton { background-color: #e2e8f0; color: #334155; font-weight: 500; "
            "padding: 8px 16px; border-radius: 6px; font-size: 12px; }"
            "QPushButton:hover { background-color: #cbd5e1; }"
        )
        self.boton_cerrar.clicked.connect(self.reject)
        layout_botones.addWidget(self.boton_cerrar)

        layout_principal.addLayout(layout_botones)

    # ==========================================================================
    # Construcción de Pestañas
    # ==========================================================================

    def _crear_pestana_pasos_1_y_2(self) -> QWidget:
        """Paso 1: Tabla 1 (AFN original) y Paso 2: Tabla 2 (Expansión de compuestos)."""
        contenedor = QWidget()
        layout = QVBoxLayout(contenedor)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(14)

        if not self.resultado:
            return contenedor

        res = self.resultado

        # --- SECCIÓN PASO 1 ---
        lbl_p1 = QLabel("Paso 1: Construcción de la tabla de transiciones original del AFN")
        lbl_p1.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        lbl_p1.setStyleSheet("color: #1e293b;")
        layout.addWidget(lbl_p1)

        txt_p1 = QLabel(
            "• Columnas: símbolos de entrada Σ. Filas: estados del AFN.\n"
            "• Flecha (→): estado inicial. Asterisco (*): estados de aceptación originales.\n"
            "• Múltiples destinos se agrupan entre llaves {q₁, q₂}. Sin transición se representa con el conjunto vacío (∅)."
        )
        txt_p1.setStyleSheet("color: #475569; font-size: 11px;")
        layout.addWidget(txt_p1)

        lbl_t1 = QLabel("Tabla 1: Transiciones del AFN inicial")
        lbl_t1.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        lbl_t1.setStyleSheet("color: #047857;")
        layout.addWidget(lbl_t1)

        tabla1 = self._crear_tabla_estilizada(
            columnas=["Estado Δ"] + [f"Entrada {s}" for s in res.alfabeto],
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
                tabla1.setItem(fila_idx, c_idx, it_d)
        layout.addWidget(tabla1)

        layout.addSpacing(6)

        # --- SECCIÓN PASO 2 ---
        lbl_p2 = QLabel("Paso 2: Generar y evaluar nuevos estados compuestos")
        lbl_p2.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        lbl_p2.setStyleSheet("color: #1e293b;")
        layout.addWidget(lbl_p2)

        txt_p2 = QLabel(
            "Al existir salidas con conjuntos de múltiples estados (ej. {q₁, q₂}), estos se tratan como estados individuales\n"
            "del nuevo autómata, calculando la unión de sus transiciones: δ(q₁, σ) ∪ δ(q₂, σ)."
        )
        txt_p2.setStyleSheet("color: #475569; font-size: 11px;")
        layout.addWidget(txt_p2)

        lbl_t2 = QLabel("Tabla 2: Expansión de estados compuestos")
        lbl_t2.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        lbl_t2.setStyleSheet("color: #047857;")
        layout.addWidget(lbl_t2)

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
        layout.addWidget(tabla2)

        # Envolver en área desplazable
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(contenedor)
        return scroll

    def _crear_pestana_pasos_3_y_4(self) -> QWidget:
        """Paso 3: Notación Kn y Paso 4: Identificación de estados finales (Tabla 3)."""
        contenedor = QWidget()
        layout = QVBoxLayout(contenedor)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(14)

        if not self.resultado:
            return contenedor

        res = self.resultado

        # --- SECCIÓN PASO 3 ---
        lbl_p3 = QLabel("Paso 3: Renombrar estados a la notación Kn")
        lbl_p3.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        lbl_p3.setStyleSheet("color: #1e293b;")
        layout.addWidget(lbl_p3)

        txt_p3 = QLabel(
            "Se toma la lista de conjuntos únicos descubiertos en la Tabla 2 y se les asigna una etiqueta formal Kn.\n"
            "El estado inicial se etiqueta como K₀. Los estados simples conservan el índice si es posible (K₁={q₁}, K₂={q₂}...).\n"
            "Los estados compuestos descubiertos se etiquetan correlativamente (K₄, K₅...)."
        )
        txt_p3.setStyleSheet("color: #475569; font-size: 11px;")
        layout.addWidget(txt_p3)

        tabla_kn = self._crear_tabla_estilizada(
            columnas=["Notación Formal", "Conjunto Equivalente {qi}", "Tipo de Estado"],
            num_filas=len(res.mapeo_kn),
        )
        for fila_idx, f in enumerate(res.mapeo_kn):
            tipo = "Inicial (K₀)" if f.es_inicial else ("Compuesto" if len(f.subconjunto) > 1 else "Simple")
            it0 = QTableWidgetItem(f.etiqueta)
            it0.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            it0.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if f.es_inicial:
                it0.setForeground(QColor("#047857"))
            tabla_kn.setItem(fila_idx, 0, it0)

            it1 = QTableWidgetItem(f.subconjunto_formateado)
            it1.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            tabla_kn.setItem(fila_idx, 1, it1)

            it2 = QTableWidgetItem(tipo)
            it2.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            tabla_kn.setItem(fila_idx, 2, it2)

        layout.addWidget(tabla_kn)
        layout.addSpacing(6)

        # --- SECCIÓN PASO 4 ---
        lbl_p4 = QLabel("Paso 4: Identificar estados finales en Kn")
        lbl_p4.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        lbl_p4.setStyleSheet("color: #1e293b;")
        layout.addWidget(lbl_p4)

        # Marco destacado para el Criterio de Aceptación
        marco_regla = QFrame()
        marco_regla.setStyleSheet(
            "QFrame { background-color: #fefce8; border: 1.5px solid #facc15; border-radius: 6px; padding: 8px; }"
        )
        layout_regla = QVBoxLayout(marco_regla)
        txt_regla = QLabel(
            "⭐ Criterio de Aceptación: Un estado Kn es un estado final (de aceptación) si y solo si contiene al menos uno "
            "de los estados finales del AFN original.\n"
            "Kn ∈ F_AFD ⟺ Kn ∩ F_AFN ≠ ∅"
        )
        txt_regla.setStyleSheet("color: #854d0e; font-weight: bold; font-size: 11px;")
        layout_regla.addWidget(txt_regla)

        f_afn_str = "{" + ", ".join(sorted(res.estados_aceptacion_nfa)) + "}"
        txt_f_afn = QLabel(f"Estados finales originales del AFN: F_AFN = {f_afn_str}")
        txt_f_afn.setStyleSheet("color: #713f12; font-size: 11px;")
        layout_regla.addWidget(txt_f_afn)
        layout.addWidget(marco_regla)

        # Listado de justificaciones de estados finales
        for f in res.mapeo_kn:
            lbl_item = QLabel(f"• {f.etiqueta} = {f.subconjunto_formateado}: {f.motivo_final} ➔ {f.explicacion_regla_oro}")
            if f.es_final:
                lbl_item.setStyleSheet("color: #059669; font-weight: 600; font-size: 11px;")
            else:
                lbl_item.setStyleSheet("color: #64748b; font-size: 11px;")
            layout.addWidget(lbl_item)

        lbl_t3 = QLabel("Tabla 3: Transiciones formalizada en términos de Kn")
        lbl_t3.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        lbl_t3.setStyleSheet("color: #047857; margin-top: 6px;")
        layout.addWidget(lbl_t3)

        tabla3 = self._crear_tabla_estilizada(
            columnas=["Estado"] + list(res.alfabeto) + ["¿Es Final?"],
            num_filas=len(res.tabla3_formalizada),
        )
        for fila_idx, f in enumerate(res.tabla3_formalizada):
            it_est = QTableWidgetItem(f.estado_con_prefijo)
            it_est.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            it_est.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            if f.es_final:
                it_est.setForeground(QColor("#059669"))
            if f.es_inicial:
                it_est.setForeground(QColor("#047857"))
            tabla3.setItem(fila_idx, 0, it_est)

            for c_idx, sim in enumerate(res.alfabeto, start=1):
                dest_k = f.transiciones_kn.get(sim)
                texto = dest_k if dest_k else "∅"
                it_d = QTableWidgetItem(texto)
                it_d.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                tabla3.setItem(fila_idx, c_idx, it_d)

            # Columna ¿Es Final?
            it_fin = QTableWidgetItem(f.explicacion_regla_oro)
            it_fin.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            it_fin.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold if f.es_final else QFont.Weight.Normal))
            if f.es_final:
                it_fin.setForeground(QColor("#059669"))
            else:
                it_fin.setForeground(QColor("#64748b"))
            tabla3.setItem(fila_idx, len(res.alfabeto) + 1, it_fin)

        layout.addWidget(tabla3)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(contenedor)
        return scroll

    def _crear_pestana_pasos_5_y_6(self) -> QWidget:
        """Paso 5: Instrucciones de Pintado y Paso 6: Accesibilidad y Tabla 4 Final Simplificada."""
        contenedor = QWidget()
        layout = QVBoxLayout(contenedor)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(14)

        if not self.resultado:
            return contenedor

        res = self.resultado

        # ======================================================================
        # PASO 5: DIBUJAR EL GRAFO DEL AFD («PINTAR» A PARTIR DE TABLA 3)
        # ======================================================================
        lbl_p5 = QLabel("Paso 5: Dibujar el grafo del AFD («Pintar» a partir de la Tabla 3)")
        lbl_p5.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        lbl_p5.setStyleSheet("color: #1e293b;")
        layout.addWidget(lbl_p5)

        txt_p5 = QLabel(
            "1. Se traza el estado inicial con flecha entrante → (K₀).\n"
            "2. Se representan los estados finales de aceptación con doble círculo concéntrico.\n"
            "3. Se grafican todas las transiciones rotuladas con las entradas {a, b...} formalizadas en la Tabla 3.\n"
            "• Nota pedagógica: En el visor inferior se muestra el grafo íntegro de la Tabla 3. Los estados que\n"
            "  resultan inalcanzables desde K₀ se colorean automáticamente en ROJO para visualizar la poda del Paso 6."
        )
        txt_p5.setStyleSheet("color: #475569; font-size: 11px;")
        layout.addWidget(txt_p5)

        # Marco visual con el visor del grafo de la Tabla 3
        marco_grafo = QFrame()
        marco_grafo.setStyleSheet(
            "QFrame { background-color: #ffffff; border: 1.5px solid #cbd5e1; border-radius: 8px; }"
        )
        layout_marco = QVBoxLayout(marco_grafo)
        layout_marco.setContentsMargins(10, 10, 10, 10)
        layout_marco.setSpacing(8)

        # Barra superior con título, leyendas y controles de navegación
        barra_top = QHBoxLayout()
        barra_top.setSpacing(8)

        lbl_titulo_grafo = QLabel("Grafo Completo del AFD (Tabla 3)")
        lbl_titulo_grafo.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        lbl_titulo_grafo.setStyleSheet("color: #0f172a;")
        barra_top.addWidget(lbl_titulo_grafo)

        # Pastillas informativas de la leyenda
        lbl_leg_ini = QLabel("➔ → K₀ (Inicial)")
        lbl_leg_ini.setStyleSheet(
            "color: #065f46; font-weight: 600; font-size: 11px; background: #ecfdf5; "
            "border: 1px solid #a7f3d0; padding: 2px 6px; border-radius: 4px;"
        )
        barra_top.addWidget(lbl_leg_ini)

        lbl_leg_alc = QLabel("🟢 Kₙ Alcanzable")
        lbl_leg_alc.setStyleSheet(
            "color: #166534; font-weight: 600; font-size: 11px; background: #f0fdf4; "
            "border: 1px solid #bbf7d0; padding: 2px 6px; border-radius: 4px;"
        )
        barra_top.addWidget(lbl_leg_alc)

        lbl_leg_inacc = QLabel("🔴 Kₙ Inalcanzable (Rojo)")
        lbl_leg_inacc.setStyleSheet(
            "color: #b91c1c; font-weight: 600; font-size: 11px; background: #fef2f2; "
            "border: 1px solid #fecaca; padding: 2px 6px; border-radius: 4px;"
        )
        barra_top.addWidget(lbl_leg_inacc)

        lbl_leg_doble = QLabel("⭕ Doble Círculo (Final)")
        lbl_leg_doble.setStyleSheet(
            "color: #475569; font-weight: 600; font-size: 11px; background: #f8fafc; "
            "border: 1px solid #e2e8f0; padding: 2px 6px; border-radius: 4px;"
        )
        barra_top.addWidget(lbl_leg_doble)

        barra_top.addStretch()
        layout_marco.addLayout(barra_top)

        # Lienzo del grafo en modo estático solo visualización (sin zoom, sin mover nodos, sin botones)
        lienzo_tabla3 = LienzoGrafo(parent=marco_grafo, solo_lectura=True, modo_estatico=True)
        self.lienzo_tabla3 = lienzo_tabla3
        lienzo_tabla3.setMinimumHeight(350)
        lienzo_tabla3.establecer_alfabeto_permitido(res.alfabeto)

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

        lienzo_tabla3.sincronizar_desde_modelo(
            estados=estados_tabla3,
            transiciones=transiciones_tabla3,
            estado_inicial=estado_inicial_tabla3,
            estados_aceptacion=estados_aceptacion_tabla3,
            estados_inalcanzables=estados_inalcanzables_set,
            estados_alcanzables=estados_alcanzables_set,
        )
        lienzo_tabla3.auto_organizar_nodos()
        layout_marco.addWidget(lienzo_tabla3)
        layout.addWidget(marco_grafo)

        # Banner explicativo de la detección visual de inalcanzables
        if res.accesibilidad.estados_inalcanzables:
            inacc_str = ", ".join(res.accesibilidad.estados_inalcanzables)
            marco_alerta_inacc = QFrame()
            marco_alerta_inacc.setStyleSheet(
                "QFrame { background-color: #fef2f2; border: 1.5px solid #f87171; border-radius: 6px; padding: 8px 12px; }"
            )
            layout_alerta = QVBoxLayout(marco_alerta_inacc)
            layout_alerta.setSpacing(3)

            lbl_alerta_tit = QLabel(f"✂ Estados Inalcanzables Resaltados en ROJO: {{{inacc_str}}}")
            lbl_alerta_tit.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            lbl_alerta_tit.setStyleSheet("color: #b91c1c;")
            layout_alerta.addWidget(lbl_alerta_tit)

            lbl_alerta_desc = QLabel(
                f"Al observar el grafo de la Tabla 3, se puede evidenciar que no existe ningún camino dirigido desde el estado inicial "
                f"({estado_inicial_tabla3}) hacia los nodos en rojo {{{inacc_str}}}. "
                f"Por tanto, en el Paso 6 son podados del autómata para producir la versión mínima de la Tabla 4."
            )
            lbl_alerta_desc.setStyleSheet("color: #7f1d1d; font-size: 11px;")
            lbl_alerta_desc.setWordWrap(True)
            layout_alerta.addWidget(lbl_alerta_desc)
            layout.addWidget(marco_alerta_inacc)
        else:
            marco_alerta_ok = QFrame()
            marco_alerta_ok.setStyleSheet(
                "QFrame { background-color: #f0fdf4; border: 1.5px solid #86efac; border-radius: 6px; padding: 8px 12px; }"
            )
            layout_ok = QVBoxLayout(marco_alerta_ok)
            lbl_ok = QLabel("✔ Todos los estados del autómata son alcanzables desde K₀ (no hay estados inalcanzables en rojo).")
            lbl_ok.setStyleSheet("color: #166534; font-weight: bold; font-size: 11px;")
            layout_ok.addWidget(lbl_ok)
            layout.addWidget(marco_alerta_ok)

        layout.addSpacing(6)

        # ======================================================================
        # PASO 6: IDENTIFICAR Y PODAR ESTADOS INALCANZABLES (TABLA 4 FINAL)
        # ======================================================================
        lbl_p6 = QLabel("Paso 6: Identificar y podar estados inalcanzables (Poda y Tabla 4 Final)")
        lbl_p6.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        lbl_p6.setStyleSheet("color: #1e293b;")
        layout.addWidget(lbl_p6)

        txt_p6 = QLabel(
            "Rastreo formal de accesibilidad partiendo del estado inicial (K₀):\n"
            "Aquellos estados a los que ningún camino parte desde el estado inicial quedan aislados y son podados:"
        )
        txt_p6.setStyleSheet("color: #475569; font-size: 11px;")
        layout.addWidget(txt_p6)

        # Marco con el análisis de accesibilidad
        marco_acc = QFrame()
        marco_acc.setStyleSheet(
            "QFrame { background-color: #f0fdf4; border: 1.5px solid #86efac; border-radius: 6px; padding: 8px; }"
        )
        layout_acc = QVBoxLayout(marco_acc)
        layout_acc.setSpacing(3)

        for paso_txt in res.accesibilidad.recorrido_pasos:
            lbl_paso = QLabel(f"• {paso_txt}")
            lbl_paso.setStyleSheet("color: #166534; font-size: 11px;")
            layout_acc.addWidget(lbl_paso)
        layout.addWidget(marco_acc)

        if res.accesibilidad.estados_inalcanzables:
            lbl_poda = QLabel(
                f"✂ Estados inalcanzables podados: {', '.join(res.accesibilidad.estados_inalcanzables)}"
            )
            lbl_poda.setStyleSheet("color: #b91c1c; font-weight: bold; font-size: 11px;")
            layout.addWidget(lbl_poda)

        lbl_t4 = QLabel("Tabla 4: AFD final simplificado y mínimo")
        lbl_t4.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        lbl_t4.setStyleSheet("color: #047857; margin-top: 6px;")
        layout.addWidget(lbl_t4)

        tabla4 = self._crear_tabla_estilizada(
            columnas=["Estado"] + [f"Entrada {s}" for s in res.alfabeto],
            num_filas=len(res.tabla4_final),
        )
        for fila_idx, f in enumerate(res.tabla4_final):
            it_est = QTableWidgetItem(f.estado_con_prefijo)
            it_est.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            it_est.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            if f.es_final:
                it_est.setForeground(QColor("#059669"))
            if f.es_inicial:
                it_est.setForeground(QColor("#047857"))
            tabla4.setItem(fila_idx, 0, it_est)

            for c_idx, sim in enumerate(res.alfabeto, start=1):
                dest_k = f.transiciones_kn.get(sim)
                texto = dest_k if dest_k else "∅"
                it_d = QTableWidgetItem(texto)
                it_d.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                tabla4.setItem(fila_idx, c_idx, it_d)
        layout.addWidget(tabla4)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(contenedor)
        return scroll

    # ==========================================================================
    # Utilidades Visuales
    # ==========================================================================

    def _crear_tabla_estilizada(self, columnas: List[str], num_filas: int) -> QTableWidget:
        """Crea y estiliza un QTableWidget idéntico a las matrices del apunte."""
        tabla = QTableWidget()
        tabla.setColumnCount(len(columnas))
        tabla.setHorizontalHeaderLabels(columnas)
        tabla.setRowCount(num_filas)
        tabla.setAlternatingRowColors(True)
        tabla.setStyleSheet(
            "QTableWidget { gridline-color: #e2e8f0; font-size: 11px; background-color: #ffffff; }"
            "QHeaderView::section { background-color: #f1f5f9; font-weight: bold; color: #1e293b; padding: 5px; }"
        )
        tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        # Altura fija adecuada según filas
        altura_calculada = min(220, 36 + num_filas * 28)
        tabla.setMinimumHeight(altura_calculada)
        return tabla

    def _al_aplicar_afd(self) -> None:
        """Aplica el AFD final simplificado al controlador y cierra el diálogo."""
        if self.resultado:
            self.aplicar_afd_solicitado.emit(self.resultado)
            self.accept()
