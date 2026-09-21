"""Modelo para la representación formal de un Autómata Finito No Determinista (NFA)."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Set

from src.model.alfabeto import Alfabeto
from src.model.automata import Automata, ErrorAutomata


@dataclass
class PasoRamaNFA:
    """Representa un paso individual dentro de una rama computacional del NFA."""
    indice_paso: int
    estado_actual: str
    simbolo: Optional[str]
    destinos_posibles: Set[str] = field(default_factory=set)
    es_aceptacion: bool = False


@dataclass
class RamaTrazaNFA:
    """Representa un camino computacional individual ejecutado por el NFA."""
    id_rama: int
    id_padre: Optional[int]
    camino: List[str]
    pasos: List[PasoRamaNFA] = field(default_factory=list)
    estado_terminal: Optional[str] = None
    alcanzo_fin: bool = False
    es_aceptada: bool = False
    es_abortada: bool = False
    indice_aborto: Optional[int] = None
    simbolo_aborto: Optional[str] = None
    motivo_aborto: Optional[str] = None


@dataclass
class ResultadoTrazaNFA:
    """Representa el resultado global de la evaluación de una cadena en un NFA."""
    cadena_entrada: str
    aceptada: bool
    ramas: List[RamaTrazaNFA]
    total_pasos: int

    @property
    def ramas_aceptadas(self) -> List[RamaTrazaNFA]:
        """Retorna todas las ramas completas que alcanzaron estado de aceptación."""
        return [r for r in self.ramas if r.es_aceptada]

    @property
    def ramas_rechazadas(self) -> List[RamaTrazaNFA]:
        """Retorna todas las ramas completas que alcanzaron fin pero no en aceptación."""
        return [r for r in self.ramas if r.alcanzo_fin and not r.es_aceptada]

    @property
    def ramas_abortadas(self) -> List[RamaTrazaNFA]:
        """Retorna todas las ramas truncadas prematuramente por falta de transición."""
        return [r for r in self.ramas if r.es_abortada]


class AutomataNFA(Automata):
    """Representa un Autómata Finito No Determinista (NFA).
    
    Formalmente definido por (Q, Sigma, delta, q0, F) donde:
    delta: Q x Sigma -> P(Q) (conjuntos de estados destino).
    """

    def __init__(
        self,
        alfabeto: Optional[Alfabeto | List[str] | Set[str]] = None,
        estados: Optional[List[str] | Set[str]] = None,
        estado_inicial: Optional[str] = None,
        estados_aceptacion: Optional[List[str] | Set[str]] = None,
    ) -> None:
        self._transiciones_nd: Dict[str, Dict[str, Set[str]]] = {}
        super().__init__(
            alfabeto=alfabeto,
            estados=estados,
            estado_inicial=estado_inicial,
            estados_aceptacion=estados_aceptacion,
        )

    @property
    def transiciones(self) -> Dict[str, Dict[str, Set[str]]]:
        """Retorna una copia de la tabla de transiciones delta no determinista."""
        return {
            estado: {sim: set(destinos) for sim, destinos in trans.items()}
            for estado, trans in self._transiciones_nd.items()
        }

    def agregar_estado(
        self,
        nombre: str,
        es_inicial: bool = False,
        es_aceptacion: bool = False,
    ) -> None:
        """Agrega un estado a Q e inicializa su diccionario de transiciones no deterministas."""
        super().agregar_estado(nombre, es_inicial, es_aceptacion)
        if nombre not in self._transiciones_nd:
            self._transiciones_nd[nombre] = {}

    def eliminar_estado(self, nombre: str) -> None:
        """Elimina un estado de Q y todas sus transiciones entrantes y salientes."""
        if nombre not in self._estados:
            raise ErrorAutomata(f"El estado '{nombre}' no existe en Q.")

        super().eliminar_estado(nombre)

        # Eliminar transiciones salientes en NFA
        if nombre in self._transiciones_nd:
            del self._transiciones_nd[nombre]

        # Eliminar transiciones entrantes hacia este estado en NFA
        for origen, trans in self._transiciones_nd.items():
            for sim in list(trans.keys()):
                trans[sim].discard(nombre)
                if not trans[sim]:
                    del trans[sim]

    def definir_alfabeto(self, simbolos: Iterable[str] | Alfabeto) -> None:
        """Define el alfabeto y purga transiciones que usen símbolos no permitidos."""
        super().definir_alfabeto(simbolos)
        for origen, trans in self._transiciones_nd.items():
            simbolos_invalidos = [sim for sim in trans if not self._alfabeto.contiene(sim)]
            for sim in simbolos_invalidos:
                del trans[sim]

    def agregar_transicion(self, origen: str, simbolo: str, destino: str) -> None:
        """Agrega una transición no determinista delta(origen, simbolo) -> destino.

        Si ya existen otros destinos para el mismo par (origen, simbolo), se añaden.
        """
        if origen not in self._estados:
            raise ErrorAutomata(f"El estado origen '{origen}' no pertenece a Q.")
        if destino not in self._estados:
            raise ErrorAutomata(f"El estado destino '{destino}' no pertenece a Q.")
        if not self._alfabeto.contiene(simbolo):
            raise ErrorAutomata(
                f"El símbolo '{simbolo}' no pertenece al alfabeto Sigma: {self._alfabeto.simbolos}."
            )

        if origen not in self._transiciones_nd:
            self._transiciones_nd[origen] = {}
        if simbolo not in self._transiciones_nd[origen]:
            self._transiciones_nd[origen][simbolo] = set()

        self._transiciones_nd[origen][simbolo].add(destino)

    def agregar_transiciones_multiples(
        self,
        origen: str,
        simbolo: str,
        destinos: Iterable[str],
    ) -> None:
        """Agrega múltiples estados destino para delta(origen, simbolo)."""
        for dest in destinos:
            self.agregar_transicion(origen, simbolo, dest)

    def eliminar_transicion(
        self,
        origen: str,
        simbolo: str,
        destino: Optional[str] = None,
    ) -> None:
        """Elimina un destino específico o todas las transiciones con ese símbolo."""
        if origen in self._transiciones_nd and simbolo in self._transiciones_nd[origen]:
            if destino is None:
                del self._transiciones_nd[origen][simbolo]
            else:
                self._transiciones_nd[origen][simbolo].discard(destino)
                if not self._transiciones_nd[origen][simbolo]:
                    del self._transiciones_nd[origen][simbolo]

    def obtener_transiciones(self, origen: str, simbolo: str) -> Set[str]:
        """Obtiene el conjunto delta(origen, simbolo) o un conjunto vacío si no hay transiciones."""
        if origen not in self._transiciones_nd:
            return set()
        return set(self._transiciones_nd[origen].get(simbolo, set()))

    def obtener_transicion(self, origen: str, simbolo: str) -> Optional[str]:
        """Compatibilidad con interfaz DFA: retorna un destino o None si está vacío."""
        destinos = self.obtener_transiciones(origen, simbolo)
        if not destinos:
            return None
        return sorted(destinos)[0]

    @classmethod
    def desde_dfa(cls, dfa: Automata) -> AutomataNFA:
        """Construye un AutomataNFA equivalente a partir de un Automata (DFA)."""
        nfa = cls(
            alfabeto=Alfabeto(dfa.alfabeto.simbolos),
            estados=dfa.estados,
            estado_inicial=dfa.estado_inicial,
            estados_aceptacion=dfa.estados_aceptacion,
        )
        for origen, trans in dfa.transiciones.items():
            for simbolo, destino in trans.items():
                nfa.agregar_transicion(origen, simbolo, destino)
        return nfa

    def tiene_transiciones_multiples(self) -> bool:
        """Retorna True si al menos un par (q, σ) tiene más de un destino formal."""
        for trans in self._transiciones_nd.values():
            for destinos in trans.values():
                if len(destinos) > 1:
                    return True
        return False

    def es_no_deterministico(self) -> bool:
        """Determina si este autómata presenta características no deterministas.

        Un autómata es no determinista y requiere conversión de subconjuntos si posee
        al menos una transición con múltiples destinos (|δ(q, σ)| > 1).
        """
        return self.tiene_transiciones_multiples()

    def convertir_a_dfa(self, incluir_trampa: bool = False):
        """Convierte este NFA a un DFA equivalente mediante el método de subconjuntos de Rabin-Scott."""
        from src.model.conversion_nfa_dfa import ConvertidorSubconjuntos
        return ConvertidorSubconjuntos.convertir(self, incluir_trampa=incluir_trampa)

    def evaluar_cadena(self, cadena: str) -> bool:
        """Evalúa si una cadena es aceptada por este NFA.

        Aceptada si al menos una rama computacional finaliza en un estado de aceptación.
        """
        resultado = self.generar_traza(cadena)
        return resultado.aceptada

    def generar_traza(self, cadena: str) -> ResultadoTrazaNFA:
        """Simula la ejecución del NFA paso a paso generando todas las ramas computacionales.

        Diferencia ramas que alcanzan la celda delimitadora '≡' (aceptadas o rechazadas)
        de aquellas abortadas prematuramente ante transiciones vacías (∅).
        """
        if self._estado_inicial is None:
            raise ErrorAutomata("No se puede evaluar: el estado inicial q0 no está definido.")
        if self._estado_inicial not in self._estados:
            raise ErrorAutomata(f"El estado inicial '{self._estado_inicial}' no pertenece a los estados Q.")

        self._alfabeto.verificar_cadena(cadena)

        total_simbolos = len(cadena)
        contador_ramas = 1

        # Estructura de trabajo para ramas activas durante la simulación
        # Cada elemento: (rama_obj, estado_actual)
        rama_raiz = RamaTrazaNFA(
            id_rama=contador_ramas,
            id_padre=None,
            camino=[self._estado_inicial],
            pasos=[],
        )
        ramas_totales: List[RamaTrazaNFA] = [rama_raiz]
        ramas_activas: List[RamaTrazaNFA] = [rama_raiz]

        # Simular paso a paso por cada símbolo
        for indice, simbolo in enumerate(cadena):
            nuevas_ramas_activas: List[RamaTrazaNFA] = []

            for rama in ramas_activas:
                estado_actual = rama.camino[-1]
                destinos = self.obtener_transiciones(estado_actual, simbolo)

                # Registrar el paso en la celda correspondiente
                paso = PasoRamaNFA(
                    indice_paso=indice,
                    estado_actual=estado_actual,
                    simbolo=simbolo,
                    destinos_posibles=destinos,
                    es_aceptacion=estado_actual in self._estados_aceptacion,
                )
                rama.pasos.append(paso)

                if not destinos:
                    # Rama abortada prematuramente por transición vacía (∅)
                    rama.es_abortada = True
                    rama.indice_aborto = indice
                    rama.simbolo_aborto = simbolo
                    rama.motivo_aborto = (
                        f"Transición vacía (∅) desde el estado '{estado_actual}' con el símbolo '{simbolo}'."
                    )
                else:
                    destinos_ordenados = sorted(destinos)
                    # El primer destino continúa en la rama actual
                    primer_destino = destinos_ordenados[0]
                    rama.camino.append(primer_destino)
                    nuevas_ramas_activas.append(rama)

                    # Los destinos adicionales crean nuevas ramas hijas bifurcadas
                    for dest_adicional in destinos_ordenados[1:]:
                        contador_ramas += 1
                        rama_hija = RamaTrazaNFA(
                            id_rama=contador_ramas,
                            id_padre=rama.id_rama,
                            camino=list(rama.camino[:-1]) + [dest_adicional],
                            pasos=list(rama.pasos),
                        )
                        ramas_totales.append(rama_hija)
                        nuevas_ramas_activas.append(rama_hija)

            ramas_activas = nuevas_ramas_activas

        # Paso terminal en la celda de fin de cadena (≡) para las ramas que completaron la lectura
        for rama in ramas_activas:
            estado_terminal = rama.camino[-1]
            rama.alcanzo_fin = True
            rama.estado_terminal = estado_terminal
            rama.es_aceptada = estado_terminal in self._estados_aceptacion

            # Registrar el paso final en la celda ≡
            rama.pasos.append(
                PasoRamaNFA(
                    indice_paso=total_simbolos,
                    estado_actual=estado_terminal,
                    simbolo=None,
                    destinos_posibles=set(),
                    es_aceptacion=rama.es_aceptada,
                )
            )

        aceptada_global = any(r.es_aceptada for r in ramas_totales)

        return ResultadoTrazaNFA(
            cadena_entrada=cadena,
            aceptada=aceptada_global,
            ramas=ramas_totales,
            total_pasos=total_simbolos + 1,
        )

    def a_diccionario(self) -> dict:
        """Serializa el NFA a un diccionario."""
        transiciones_dict = {
            origen: {sim: sorted(destinos) for sim, destinos in trans.items()}
            for origen, trans in self._transiciones_nd.items()
        }
        return {
            "tipo": "NFA",
            "alfabeto": self._alfabeto.a_lista(),
            "estados": self.estados,
            "estado_inicial": self._estado_inicial,
            "estados_aceptacion": list(self._estados_aceptacion),
            "transiciones": transiciones_dict,
        }

    @classmethod
    def desde_diccionario(cls, datos: dict) -> AutomataNFA:
        """Deserializa un NFA a partir de un diccionario."""
        alfabeto = Alfabeto(datos.get("alfabeto", []))
        nfa = cls(
            alfabeto=alfabeto,
            estados=datos.get("estados", []),
            estado_inicial=datos.get("estado_inicial"),
            estados_aceptacion=datos.get("estados_aceptacion", []),
        )
        for origen, trans in datos.get("transiciones", {}).items():
            for simbolo, destinos in trans.items():
                if isinstance(destinos, list):
                    for dest in destinos:
                        nfa.agregar_transicion(origen, simbolo, dest)
                else:
                    nfa.agregar_transicion(origen, simbolo, str(destinos))
        return nfa
