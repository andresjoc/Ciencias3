"""Modelo para la representación formal de un Autómata Finito Determinista (DFA)."""

from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, Iterable, List, Optional, Set

if TYPE_CHECKING:
    from src.model.automata_nfa import AutomataNFA

from src.model.alfabeto import Alfabeto, ErrorAlfabeto


class ErrorAutomata(Exception):
    """Excepción lanzada cuando ocurre una operación inválida en el autómata."""
    pass


@dataclass
class PasoTraza:
    """Representa un paso individual en la traza de ejecución del autómata."""
    indice_paso: int
    estado_actual: str
    simbolo: Optional[str]
    estado_siguiente: Optional[str]
    es_aceptacion: bool


@dataclass
class ResultadoTraza:
    """Representa el resultado completo de la traza de ejecución para una cadena de entrada."""
    cadena_entrada: str
    aceptada: bool
    camino: List[str]
    pasos: List[PasoTraza]
    estado_final: Optional[str]
    motivo_rechazo: Optional[str] = None


class Automata:
    """Representa un Autómata Finito formalmente definido por la 5-tupla (Q, Sigma, delta, q0, F).

    Atributos:
        alfabeto (Alfabeto): Alfabeto formal de entrada Sigma.
        estados (List[str]): Conjunto ordenado de estados Q.
        estado_inicial (Optional[str]): Estado inicial q0 en Q.
        estados_aceptacion (Set[str]): Conjunto de estados de aceptación F subconjunto de Q.
        transiciones (Dict[str, Dict[str, str]]): Función de transición delta(q, a) = q'.
    """

    def __init__(
        self,
        alfabeto: Optional[Alfabeto | List[str] | Set[str]] = None,
        estados: Optional[List[str] | Set[str]] = None,
        estado_inicial: Optional[str] = None,
        estados_aceptacion: Optional[List[str] | Set[str]] = None,
    ) -> None:
        if alfabeto is None:
            self._alfabeto = Alfabeto()
        elif isinstance(alfabeto, Alfabeto):
            self._alfabeto = alfabeto
        else:
            self._alfabeto = Alfabeto(alfabeto)

        self._estados: Set[str] = set()
        self._orden_estados: List[str] = []
        self._estado_inicial: Optional[str] = None
        self._estados_aceptacion: Set[str] = set()
        self._transiciones: Dict[str, Dict[str, str]] = {}

        if estados:
            for estado in estados:
                self.agregar_estado(estado)

        if estado_inicial is not None:
            self.definir_estado_inicial(estado_inicial)

        if estados_aceptacion:
            for estado in estados_aceptacion:
                self.agregar_estado_aceptacion(estado)

    @property
    def alfabeto(self) -> Alfabeto:
        """Retorna el alfabeto formal Sigma del autómata."""
        return self._alfabeto

    def definir_alfabeto(self, simbolos: Iterable[str] | Alfabeto) -> None:
        """Define o actualiza el alfabeto formal Sigma del autómata.

        Args:
            simbolos: Colección de símbolos o instancia de Alfabeto.
        """
        if isinstance(simbolos, Alfabeto):
            self._alfabeto = simbolos
        else:
            self._alfabeto = Alfabeto(simbolos)

        # Limpiar transiciones que usen símbolos que ya no pertenecen al nuevo alfabeto
        for origen, trans in self._transiciones.items():
            simbolos_invalidos = [sim for sim in trans if not self._alfabeto.contiene(sim)]
            for sim in simbolos_invalidos:
                del trans[sim]

    @property
    def estados(self) -> List[str]:
        """Retorna la lista ordenada de estados Q."""
        return list(self._orden_estados)

    @property
    def estado_inicial(self) -> Optional[str]:
        """Retorna el estado inicial q0."""
        return self._estado_inicial

    @property
    def estados_aceptacion(self) -> Set[str]:
        """Retorna el conjunto de estados de aceptación F."""
        return set(self._estados_aceptacion)

    @property
    def transiciones(self) -> Dict[str, Dict[str, str]]:
        """Retorna una copia de la tabla de transiciones delta."""
        return {estado: dict(trans) for estado, trans in self._transiciones.items()}

    def agregar_estado(
        self,
        nombre: str,
        es_inicial: bool = False,
        es_aceptacion: bool = False,
    ) -> None:
        """Agrega un estado a Q.

        Args:
            nombre: Identificador único del estado.
            es_inicial: Si es True, define este estado como q0.
            es_aceptacion: Si es True, agrega este estado a F.

        Raises:
            ErrorAutomata: Si el nombre del estado está vacío o no es una cadena.
        """
        if not isinstance(nombre, str) or not nombre.strip():
            raise ErrorAutomata("El nombre del estado debe ser una cadena no vacía.")

        if nombre not in self._estados:
            self._estados.add(nombre)
            self._orden_estados.append(nombre)
            self._transiciones[nombre] = {}

        if es_inicial:
            self.definir_estado_inicial(nombre)

        if es_aceptacion:
            self.agregar_estado_aceptacion(nombre)

    def eliminar_estado(self, nombre: str) -> None:
        """Elimina un estado de Q y suprime todas sus transiciones entrantes y salientes.

        Args:
            nombre: Identificador del estado a eliminar.

        Raises:
            ErrorAutomata: Si el estado no existe en Q.
        """
        if nombre not in self._estados:
            raise ErrorAutomata(f"El estado '{nombre}' no existe en Q.")

        self._estados.remove(nombre)
        self._orden_estados.remove(nombre)
        self._estados_aceptacion.discard(nombre)

        if self._estado_inicial == nombre:
            self._estado_inicial = None

        # Eliminar transiciones salientes
        if nombre in self._transiciones:
            del self._transiciones[nombre]

        # Eliminar transiciones entrantes
        for origen, trans in self._transiciones.items():
            simbolos_a_eliminar = [sim for sim, destino in trans.items() if destino == nombre]
            for sim in simbolos_a_eliminar:
                del trans[sim]

    def definir_estado_inicial(self, nombre: Optional[str]) -> None:
        """Define el estado inicial q0.

        Raises:
            ErrorAutomata: Si el estado especificado no pertenece a Q.
        """
        if nombre is not None and nombre not in self._estados:
            raise ErrorAutomata(f"El estado inicial '{nombre}' no pertenece a los estados Q.")
        self._estado_inicial = nombre

    def agregar_estado_aceptacion(self, nombre: str) -> None:
        """Agrega un estado al conjunto de estados de aceptación F.

        Raises:
            ErrorAutomata: Si el estado especificado no pertenece a Q.
        """
        if nombre not in self._estados:
            raise ErrorAutomata(f"El estado de aceptación '{nombre}' no pertenece a los estados Q.")
        self._estados_aceptacion.add(nombre)

    def eliminar_estado_aceptacion(self, nombre: str) -> None:
        """Elimina un estado del conjunto de estados de aceptación F."""
        self._estados_aceptacion.discard(nombre)

    def definir_estados_aceptacion(self, nombres: Iterable[str]) -> None:
        """Define el conjunto completo de estados de aceptación F.

        Raises:
            ErrorAutomata: Si algún estado no pertenece a Q.
        """
        nuevos_aceptacion = set()
        for nombre in nombres:
            if nombre not in self._estados:
                raise ErrorAutomata(f"El estado de aceptación '{nombre}' no pertenece a los estados Q.")
            nuevos_aceptacion.add(nombre)
        self._estados_aceptacion = nuevos_aceptacion

    def agregar_transicion(self, origen: str, simbolo: str, destino: str) -> None:
        """Define una transición determinista delta(origen, simbolo) = destino.

        Args:
            origen: Estado origen en Q.
            simbolo: Símbolo del alfabeto en Sigma.
            destino: Estado destino en Q.

        Raises:
            ErrorAutomata: Si los estados o el símbolo no están definidos formalmente.
        """
        if origen not in self._estados:
            raise ErrorAutomata(f"El estado origen '{origen}' no pertenece a Q.")
        if destino not in self._estados:
            raise ErrorAutomata(f"El estado destino '{destino}' no pertenece a Q.")
        if not self._alfabeto.contiene(simbolo):
            raise ErrorAutomata(
                f"El símbolo '{simbolo}' no pertenece al alfabeto Sigma: {self._alfabeto.simbolos}."
            )

        self._transiciones[origen][simbolo] = destino

    def eliminar_transicion(self, origen: str, simbolo: str) -> None:
        """Elimina una transición delta(origen, simbolo) si existe."""
        if origen in self._transiciones and simbolo in self._transiciones[origen]:
            del self._transiciones[origen][simbolo]

    def obtener_transicion(self, origen: str, simbolo: str) -> Optional[str]:
        """Obtiene delta(origen, simbolo) o None si no está definida."""
        if origen not in self._transiciones:
            return None
        return self._transiciones[origen].get(simbolo)

    def obtener_transiciones_desde(self, origen: str) -> Dict[str, str]:
        """Retorna un diccionario con todas las transiciones salientes desde un estado."""
        return dict(self._transiciones.get(origen, {}))

    def validar(self) -> List[str]:
        """Valida la consistencia estructural del autómata.

        Returns:
            Lista de cadenas con los errores encontrados, vacía si es consistente.
        """
        errores: List[str] = []

        if not self._estados:
            errores.append("El autómata no tiene estados definidos.")

        if self._estado_inicial is None:
            errores.append("El estado inicial q0 no está definido.")
        elif self._estado_inicial not in self._estados:
            errores.append(f"El estado inicial '{self._estado_inicial}' no pertenece a Q.")

        for aceptacion in self._estados_aceptacion:
            if aceptacion not in self._estados:
                errores.append(f"El estado de aceptación '{aceptacion}' no pertenece a Q.")

        for origen, trans in self._transiciones.items():
            if origen not in self._estados:
                errores.append(f"El origen de transición '{origen}' no pertenece a Q.")
            for sim, destino in trans.items():
                if not self._alfabeto.contiene(sim):
                    errores.append(f"El símbolo de transición '{sim}' no pertenece a Sigma.")
                if destino not in self._estados:
                    errores.append(f"El destino de transición '{destino}' no pertenece a Q.")

        return errores

    def es_valido(self) -> bool:
        """Verifica si el autómata es estructuralmente válido."""
        return len(self.validar()) == 0

    def es_completo(self) -> bool:
        """Verifica si la función delta es total (definida para todo q en Q y a en Sigma)."""
        if not self._estados or len(self._alfabeto) == 0:
            return False
        for estado in self._estados:
            for simbolo in self._alfabeto:
                if simbolo not in self._transiciones.get(estado, {}):
                    return False
        return True

    def evaluar_cadena(self, cadena: str) -> bool:
        """Evalúa si una cadena de entrada es aceptada por este DFA.

        Args:
            cadena: Cadena compuesta por símbolos en Sigma (puede ser la cadena vacía).

        Returns:
            True si la cadena es aceptada, False en caso contrario.

        Raises:
            ErrorAutomata: Si el estado inicial no está definido o es inválido.
            ErrorAlfabeto: Si algún carácter de la cadena no pertenece a Sigma.
        """
        resultado = self.generar_traza(cadena)
        return resultado.aceptada

    def generar_traza(self, cadena: str) -> ResultadoTraza:
        """Simula la ejecución paso a paso a lo largo de la cinta y retorna la traza completa.

        Args:
            cadena: Cadena de entrada a procesar.

        Returns:
            ResultadoTraza con el estado de aceptación, camino y pasos detallados.
        """
        if self._estado_inicial is None:
            raise ErrorAutomata("No se puede evaluar: el estado inicial q0 no está definido.")
        if self._estado_inicial not in self._estados:
            raise ErrorAutomata(f"El estado inicial '{self._estado_inicial}' no pertenece a los estados Q.")

        # Validar pertenencia al alfabeto formal
        self._alfabeto.verificar_cadena(cadena)

        estado_actual = self._estado_inicial
        camino = [estado_actual]
        pasos: List[PasoTraza] = []

        # Procesar cada símbolo de la cadena de entrada
        for indice, simbolo in enumerate(cadena):
            estado_siguiente = self.obtener_transicion(estado_actual, simbolo)
            pasos.append(
                PasoTraza(
                    indice_paso=indice,
                    estado_actual=estado_actual,
                    simbolo=simbolo,
                    estado_siguiente=estado_siguiente,
                    es_aceptacion=estado_actual in self._estados_aceptacion,
                )
            )

            if estado_siguiente is None:
                # Transición no definida: la ejecución se trunca prematuramente
                return ResultadoTraza(
                    cadena_entrada=cadena,
                    aceptada=False,
                    camino=camino,
                    pasos=pasos,
                    estado_final=None,
                    motivo_rechazo=(
                        f"Transición indefinida desde el estado '{estado_actual}' con el símbolo '{simbolo}'."
                    ),
                )

            estado_actual = estado_siguiente
            camino.append(estado_actual)

        # Paso final en el delimitador de fin de cadena (equivalente a celda de fin)
        pasos.append(
            PasoTraza(
                indice_paso=len(cadena),
                estado_actual=estado_actual,
                simbolo=None,
                estado_siguiente=None,
                es_aceptacion=estado_actual in self._estados_aceptacion,
            )
        )

        aceptada = estado_actual in self._estados_aceptacion
        motivo_rechazo = None
        if not aceptada:
            motivo_rechazo = f"El estado final '{estado_actual}' no es un estado de aceptación."

        return ResultadoTraza(
            cadena_entrada=cadena,
            aceptada=aceptada,
            camino=camino,
            pasos=pasos,
            estado_final=estado_actual,
            motivo_rechazo=motivo_rechazo,
        )

    def convertir_a_nfa(self) -> AutomataNFA:
        """Convierte este DFA en un AutomataNFA equivalente."""
        from src.model.automata_nfa import AutomataNFA
        return AutomataNFA.desde_dfa(self)

    def a_diccionario(self) -> dict:
        """Serializa el autómata a un diccionario compatible con formato JSON."""
        return {
            "alfabeto": self._alfabeto.a_lista(),
            "estados": self.estados,
            "estado_inicial": self._estado_inicial,
            "estados_aceptacion": list(self._estados_aceptacion),
            "transiciones": self.transiciones,
        }

    @classmethod
    def desde_diccionario(cls, datos: dict) -> Automata:
        """Deserializa un autómata a partir de un diccionario."""
        alfabeto = Alfabeto(datos.get("alfabeto", []))
        auto = cls(
            alfabeto=alfabeto,
            estados=datos.get("estados", []),
            estado_inicial=datos.get("estado_inicial"),
            estados_aceptacion=datos.get("estados_aceptacion", []),
        )
        for origen, trans in datos.get("transiciones", {}).items():
            for simbolo, destino in trans.items():
                auto.agregar_transicion(origen, simbolo, destino)
        return auto

    def __repr__(self) -> str:
        return (
            f"Automata(estados={self.estados}, alfabeto={self._alfabeto.simbolos}, "
            f"estado_inicial='{self._estado_inicial}', estados_aceptacion={self.estados_aceptacion})"
        )
