"""Modelo para la representación formal del alfabeto de entrada."""

from __future__ import annotations
from typing import Iterable, List, Set


class ErrorAlfabeto(ValueError):
    """Excepción lanzada cuando ocurre un error de validación u operación en el alfabeto."""
    pass


class Alfabeto:
    """Representa el alfabeto formal de entrada (Sigma).

    Mantiene símbolos únicos preservando el orden de inserción para la
    presentación en tablas y visualizaciones.
    """

    def __init__(self, simbolos: Iterable[str] | None = None) -> None:
        self._simbolos: List[str] = []
        self._conjunto_simbolos: Set[str] = set()

        if simbolos is not None:
            for simbolo in simbolos:
                self.agregar_simbolo(simbolo)

    @property
    def simbolos(self) -> List[str]:
        """Retorna la lista ordenada de símbolos en el alfabeto."""
        return list(self._simbolos)

    def agregar_simbolo(self, simbolo: str) -> None:
        """Agrega un símbolo al alfabeto.

        Args:
            simbolo: Cadena no vacía que representa un símbolo del alfabeto.

        Raises:
            ErrorAlfabeto: Si el símbolo no es una cadena o está vacío.
        """
        if not isinstance(simbolo, str):
            raise ErrorAlfabeto(f"El símbolo debe ser una cadena, recibido: {type(simbolo).__name__}")
        if len(simbolo) == 0:
            raise ErrorAlfabeto("El símbolo del alfabeto no puede ser una cadena vacía.")

        if simbolo not in self._conjunto_simbolos:
            self._simbolos.append(simbolo)
            self._conjunto_simbolos.add(simbolo)

    def eliminar_simbolo(self, simbolo: str) -> None:
        """Elimina un símbolo del alfabeto si existe.

        Args:
            simbolo: El símbolo a eliminar.

        Raises:
            ErrorAlfabeto: Si el símbolo no pertenece al alfabeto.
        """
        if simbolo not in self._conjunto_simbolos:
            raise ErrorAlfabeto(f"El símbolo '{simbolo}' no existe en el alfabeto.")
        self._simbolos.remove(simbolo)
        self._conjunto_simbolos.remove(simbolo)

    def contiene(self, simbolo: str) -> bool:
        """Verifica si un símbolo pertenece al alfabeto."""
        return simbolo in self._conjunto_simbolos

    def validar_cadena(self, cadena: str) -> bool:
        """Verifica si todos los caracteres de la cadena pertenecen a este alfabeto."""
        return all(caracter in self._conjunto_simbolos for caracter in cadena)

    def verificar_cadena(self, cadena: str) -> None:
        """Valida una cadena de entrada contra este alfabeto.

        Raises:
            ErrorAlfabeto: Si algún carácter de la cadena no pertenece a Sigma.
        """
        for caracter in cadena:
            if caracter not in self._conjunto_simbolos:
                raise ErrorAlfabeto(
                    f"Símbolo no válido '{caracter}' en la cadena de entrada. "
                    f"Los símbolos permitidos son: {sorted(self._conjunto_simbolos)}"
                )

    def a_lista(self) -> List[str]:
        """Retorna una copia de los símbolos como lista."""
        return list(self._simbolos)

    def __contains__(self, simbolo: str) -> bool:
        return simbolo in self._conjunto_simbolos

    def __iter__(self):
        return iter(self._simbolos)

    def __len__(self) -> int:
        return len(self._simbolos)

    def __repr__(self) -> str:
        return f"Alfabeto({self._simbolos})"

    def __eq__(self, otro: object) -> bool:
        if isinstance(otro, Alfabeto):
            return self._conjunto_simbolos == otro._conjunto_simbolos
        return False
