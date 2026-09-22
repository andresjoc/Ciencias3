"""Módulo para la conversión de AFN a AFD

Implementa con exactitud el procedimiento paso a paso:
- Paso 1: Construcción de la tabla de transiciones original del AFN (Tabla 1).
- Paso 2: Generación y evaluación de nuevos estados compuestos por unión de transiciones (Tabla 2).
- Paso 3: Renombramiento formal de estados a la notación K_n (K0, K1, K2...).
- Paso 4: Criterio de aceptación para identificar estados finales (Tabla 3).
- Paso 5: Representación gráfica de transiciones con doble círculo en finales.
- Paso 6: Identificación y poda de estados inalcanzables desde K0 (Tabla 4 final simplificada).
"""

from __future__ import annotations
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from src.model.alfabeto import Alfabeto
from src.model.automata import Automata, ErrorAutomata


@dataclass
class FilaTablaAFN:
    """Fila de la Tabla 1: Transiciones del AFN inicial."""
    estado: str
    es_inicial: bool
    es_aceptacion: bool
    transiciones: Dict[str, Set[str]] = field(default_factory=dict)

    @property
    def estado_con_prefijo(self) -> str:
        prefijo = ""
        if self.es_inicial:
            prefijo += "→ "
        if self.es_aceptacion:
            prefijo += "* "
        return f"{prefijo}{self.estado}"


@dataclass
class FilaExpansion:
    """Fila de la Tabla 2: Expansión de estados compuestos."""
    subconjunto: Set[str]
    es_compuesto: bool
    es_inicial: bool
    es_aceptacion: bool
    transiciones: Dict[str, Set[str]] = field(default_factory=dict)

    @property
    def nombre_visual(self) -> str:
        if len(self.subconjunto) == 1:
            nombre = list(self.subconjunto)[0]
        else:
            nombre = "{" + ", ".join(sorted(self.subconjunto)) + "}"
        prefijo = ""
        if self.es_inicial:
            prefijo += "→ "
        if self.es_aceptacion:
            prefijo += "* "
        return f"{prefijo}{nombre}"


@dataclass
class FilaMapeoKn:
    """Fila para el Paso 3, Tabla 3 (Paso 4) y Tabla 4 (Paso 6)."""
    etiqueta: str               # "K0", "K1", "K4", etc.
    subconjunto: Set[str]       # {"q0"} o {"q1", "q2"}
    es_inicial: bool
    es_final: bool              # ¿Es estado final/de aceptación?
    motivo_final: str           # ej. "Contiene a q1" o "No contiene estados finales"
    estados_finales_contenidos: Set[str]
    transiciones_kn: Dict[str, Optional[str]] = field(default_factory=dict)  # sim -> "K4" o None si vacío (∅)
    transiciones_conjuntos: Dict[str, Set[str]] = field(default_factory=dict) # sim -> {q1, q2}

    @property
    def subconjunto_formateado(self) -> str:
        if not self.subconjunto:
            return "∅"
        return "{" + ", ".join(sorted(self.subconjunto)) + "}"

    @property
    def estado_con_prefijo(self) -> str:
        prefijo = ""
        if self.es_inicial:
            prefijo += "→ "
        if self.es_final:
            prefijo += "* "
        return f"{prefijo}{self.etiqueta}"

    @property
    def explicacion_regla_oro(self) -> str:
        if self.es_final:
            contenidos = ", ".join(sorted(self.estados_finales_contenidos))
            return f"Sí ({contenidos})"
        return "No"


@dataclass
class AnalisisAccesibilidad:
    """Paso 6: Identificación y poda de estados inalcanzables."""
    estados_alcanzables: List[str]    # ["K0", "K4", "K5"]
    estados_inalcanzables: List[str]  # ["K1", "K2", "K3"]
    recorrido_pasos: List[str]        # Explicaciones del rastreo desde K0


@dataclass
class ResultadoConversionMetodoProfe:
    """Contenedor integral con todos los pasos del método de conversión del profesor."""
    dfa_final: Automata
    tabla1_afn: List[FilaTablaAFN]
    tabla2_expansion: List[FilaExpansion]
    mapeo_kn: List[FilaMapeoKn]
    tabla3_formalizada: List[FilaMapeoKn]
    accesibilidad: AnalisisAccesibilidad
    tabla4_final: List[FilaMapeoKn]
    alfabeto: List[str]
    estados_nfa_originales: List[str]
    estado_inicial_nfa: str
    estados_aceptacion_nfa: Set[str]


# Alias de compatibilidad hacia atrás
ResultadoConversionDFA = ResultadoConversionMetodoProfe
FilaProcesoSubconjuntos = FilaMapeoKn


class ConvertidorSubconjuntos:
    """Implementa el método de conversión de AFN a AFD documentado por el profesor."""

    @classmethod
    def convertir(
        cls,
        nfa: object,
        incluir_trampa: bool = False,
    ) -> ResultadoConversionMetodoProfe:
        """Ejecuta los 6 pasos del método del profesor para transformar un AFN a AFD.

        Args:
            nfa: Instancia de AutomataNFA.
            incluir_trampa: Parámetro opcional para incluir estado pozo si se desea.

        Returns:
            ResultadoConversionMetodoProfe con todas las tablas del procedimiento docente.
        """
        if not hasattr(nfa, "estados") or not nfa.estados:
            raise ErrorAutomata("No se puede convertir: el autómata no tiene estados definidos en Q.")

        if nfa.estado_inicial is None:
            raise ErrorAutomata("No se puede convertir: el estado inicial q0 no está definido.")

        if not hasattr(nfa, "alfabeto") or not nfa.alfabeto.simbolos:
            raise ErrorAutomata("No se puede convertir: el alfabeto Sigma no tiene símbolos definidos.")

        if not hasattr(nfa, "estados_aceptacion") or not nfa.estados_aceptacion:
            raise ErrorAutomata("No se puede convertir a AFD: el autómata no tiene ningún estado final (de aceptación) definido.")

        simbolos: List[str] = list(nfa.alfabeto.simbolos)
        estados_nfa: List[str] = list(nfa.estados)
        q0_nfa: str = nfa.estado_inicial
        f_nfa: Set[str] = set(nfa.estados_aceptacion)

        # ----------------------------------------------------------------------
        # PASO 1: Construcción de la tabla de transiciones original del AFN (Tabla 1)
        # ----------------------------------------------------------------------
        tabla1_afn: List[FilaTablaAFN] = []
        for estado in estados_nfa:
            trans_estado: Dict[str, Set[str]] = {}
            for sim in simbolos:
                destinos = nfa.obtener_transiciones(estado, sim)
                trans_estado[sim] = set(destinos)
            tabla1_afn.append(
                FilaTablaAFN(
                    estado=estado,
                    es_inicial=(estado == q0_nfa),
                    es_aceptacion=(estado in f_nfa),
                    transiciones=trans_estado,
                )
            )

        # ----------------------------------------------------------------------
        # PASO 2: Generar y evaluar nuevos estados compuestos (Tabla 2)
        # ----------------------------------------------------------------------
        # Estados simples iniciales
        conjuntos_visitados: List[frozenset[str]] = [frozenset([e]) for e in estados_nfa]
        cola_compuestos: deque[frozenset[str]] = deque()

        # Detectar salidas compuestas (|destinos| > 1) desde la tabla inicial
        for fila in tabla1_afn:
            for destinos in fila.transiciones.values():
                if len(destinos) > 1:
                    frozen_dest = frozenset(destinos)
                    if frozen_dest not in conjuntos_visitados:
                        conjuntos_visitados.append(frozen_dest)
                        cola_compuestos.append(frozen_dest)

        # Evaluar la unión de transiciones de los estados compuestos iterativamente
        tabla2_expansion: List[FilaExpansion] = []

        # Agregar primero las filas simples
        for fila in tabla1_afn:
            tabla2_expansion.append(
                FilaExpansion(
                    subconjunto={fila.estado},
                    es_compuesto=False,
                    es_inicial=fila.es_inicial,
                    es_aceptacion=fila.es_aceptacion,
                    transiciones=dict(fila.transiciones),
                )
            )

        # Procesar los compuestos pendientes
        while cola_compuestos:
            compuesto_actual = cola_compuestos.popleft()
            es_inicial = (q0_nfa in compuesto_actual)
            es_aceptacion = any(q in f_nfa for q in compuesto_actual)

            trans_compuesto: Dict[str, Set[str]] = {}
            for sim in simbolos:
                union_dest: Set[str] = set()
                for q in compuesto_actual:
                    union_dest.update(nfa.obtener_transiciones(q, sim))
                trans_compuesto[sim] = union_dest

                # Si la unión resulta en un nuevo compuesto que no ha sido evaluado
                if len(union_dest) > 1:
                    frozen_union = frozenset(union_dest)
                    if frozen_union not in conjuntos_visitados:
                        conjuntos_visitados.append(frozen_union)
                        cola_compuestos.append(frozen_union)

            tabla2_expansion.append(
                FilaExpansion(
                    subconjunto=set(compuesto_actual),
                    es_compuesto=True,
                    es_inicial=es_inicial,
                    es_aceptacion=es_aceptacion,
                    transiciones=trans_compuesto,
                )
            )

        # ----------------------------------------------------------------------
        # PASO 3: Renombrar estados a la notación K_n
        # ----------------------------------------------------------------------
        # Asignar K0, K1, K2... a los estados simples originales en su orden
        mapeo_conjunto_a_kn: Dict[frozenset[str], str] = {}
        mapeo_kn_a_conjunto: Dict[str, frozenset[str]] = {}

        contador_k = 0
        for estado in estados_nfa:
            etiqueta = f"K{contador_k}"
            frozen_simple = frozenset([estado])
            mapeo_conjunto_a_kn[frozen_simple] = etiqueta
            mapeo_kn_a_conjunto[etiqueta] = frozen_simple
            contador_k += 1

        # Asignar Kn subsiguientes a los estados compuestos
        for fila in tabla2_expansion:
            if fila.es_compuesto:
                frozen_c = frozenset(fila.subconjunto)
                if frozen_c not in mapeo_conjunto_a_kn:
                    etiqueta = f"K{contador_k}"
                    mapeo_conjunto_a_kn[frozen_c] = etiqueta
                    mapeo_kn_a_conjunto[etiqueta] = frozen_c
                    contador_k += 1

        # ----------------------------------------------------------------------
        # PASO 4: Identificar estados finales de aceptación (Tabla 3)
        # ----------------------------------------------------------------------
        # Criterio de aceptación: Kn es final si y solo si contiene al menos uno de los estados finales de AFN:
        # Kn ∈ F_AFD <=> Kn ∩ F_AFN ≠ ∅
        mapeo_kn_filas: List[FilaMapeoKn] = []
        tabla3_formalizada: List[FilaMapeoKn] = []

        for etiqueta, frozen_set in mapeo_kn_a_conjunto.items():
            set_actual = set(frozen_set)
            finales_contenidos = set_actual.intersection(f_nfa)
            es_final = len(finales_contenidos) > 0
            es_inicial = (q0_nfa in set_actual and len(set_actual) == 1) or (set_actual == {q0_nfa})

            if es_final:
                motivo = f"Contiene a {', '.join(sorted(finales_contenidos))}"
            else:
                motivo = "No contiene estados finales de aceptación"

            # Buscar las transiciones correspondientes en tabla2_expansion
            fila_exp = next(f for f in tabla2_expansion if f.subconjunto == set_actual)

            trans_kn: Dict[str, Optional[str]] = {}
            for sim in simbolos:
                dest_set = fila_exp.transiciones.get(sim, set())
                if not dest_set:
                    trans_kn[sim] = None
                else:
                    frozen_dest = frozenset(dest_set)
                    # Si el destino es un estado simple o compuesto mapeado
                    if frozen_dest in mapeo_conjunto_a_kn:
                        trans_kn[sim] = mapeo_conjunto_a_kn[frozen_dest]
                    else:
                        # Si surgió un conjunto no indexado, registrarlo
                        nueva_etiqueta = f"K{contador_k}"
                        contador_k += 1
                        mapeo_conjunto_a_kn[frozen_dest] = nueva_etiqueta
                        mapeo_kn_a_conjunto[nueva_etiqueta] = frozen_dest
                        trans_kn[sim] = nueva_etiqueta

            fila_kn = FilaMapeoKn(
                etiqueta=etiqueta,
                subconjunto=set_actual,
                es_inicial=es_inicial,
                es_final=es_final,
                motivo_final=motivo,
                estados_finales_contenidos=finales_contenidos,
                transiciones_kn=trans_kn,
                transiciones_conjuntos=dict(fila_exp.transiciones),
            )
            mapeo_kn_filas.append(fila_kn)
            tabla3_formalizada.append(fila_kn)

        # ----------------------------------------------------------------------
        # PASO 6: Identificar y podar estados inalcanzables (Tabla 4)
        # ----------------------------------------------------------------------
        # Estado inicial del AFD es K0 (correspondiente a {q0})
        etiqueta_inicial = mapeo_conjunto_a_kn.get(frozenset([q0_nfa]), "K0")

        # Rastreo de accesibilidad mediante BFS desde la etiqueta inicial
        alcanzables: Set[str] = set([etiqueta_inicial])
        cola_accesibilidad: deque[str] = deque([etiqueta_inicial])
        recorrido_explicacion: List[str] = [
            f"Se inicia el rastreo desde el estado inicial {etiqueta_inicial} ({set(mapeo_kn_a_conjunto[etiqueta_inicial])})."
        ]

        dict_filas_kn = {f.etiqueta: f for f in tabla3_formalizada}

        while cola_accesibilidad:
            actual = cola_accesibilidad.popleft()
            fila_act = dict_filas_kn.get(actual)
            if not fila_act:
                continue

            for sim in simbolos:
                dest = fila_act.transiciones_kn.get(sim)
                if dest and dest not in alcanzables:
                    alcanzables.add(dest)
                    cola_accesibilidad.append(dest)
                    recorrido_explicacion.append(
                        f"Desde {actual}, con entrada '{sim}' se accede al estado {dest} ({dict_filas_kn[dest].subconjunto_formateado})."
                    )

        todos_los_kn = [f.etiqueta for f in tabla3_formalizada]
        inalcanzables = [k for k in todos_los_kn if k not in alcanzables]

        if inalcanzables:
            recorrido_explicacion.append(
                f"Los estados {', '.join(sorted(inalcanzables))} quedan aislados (inalcanzables desde {etiqueta_inicial}) y son podados."
            )
        else:
            recorrido_explicacion.append(
                "Todos los estados generados son accesibles desde el estado inicial."
            )

        accesibilidad_info = AnalisisAccesibilidad(
            estados_alcanzables=[k for k in todos_los_kn if k in alcanzables],
            estados_inalcanzables=inalcanzables,
            recorrido_pasos=recorrido_explicacion,
        )

        # Tabla 4: Solo estados accesibles
        tabla4_final = [f for f in tabla3_formalizada if f.etiqueta in alcanzables]

        # Construir el Automata (DFA) final simplificado con la notación Kn
        estados_dfa = [f.etiqueta for f in tabla4_final]
        estados_finales_dfa = [f.etiqueta for f in tabla4_final if f.es_final]

        dfa_final = Automata(
            alfabeto=Alfabeto(simbolos),
            estados=estados_dfa,
            estado_inicial=etiqueta_inicial,
            estados_aceptacion=estados_finales_dfa,
        )

        for fila in tabla4_final:
            for sim, dest_kn in fila.transiciones_kn.items():
                if dest_kn is not None and dest_kn in alcanzables:
                    dfa_final.agregar_transicion(fila.etiqueta, sim, dest_kn)

        return ResultadoConversionMetodoProfe(
            dfa_final=dfa_final,
            tabla1_afn=tabla1_afn,
            tabla2_expansion=tabla2_expansion,
            mapeo_kn=mapeo_kn_filas,
            tabla3_formalizada=tabla3_formalizada,
            accesibilidad=accesibilidad_info,
            tabla4_final=tabla4_final,
            alfabeto=simbolos,
            estados_nfa_originales=estados_nfa,
            estado_inicial_nfa=q0_nfa,
            estados_aceptacion_nfa=f_nfa,
        )
