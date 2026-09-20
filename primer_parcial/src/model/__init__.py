"""Paquete del Modelo para Autómata y Alfabeto."""

from src.model.alfabeto import Alfabeto, ErrorAlfabeto
from src.model.automata import Automata, ErrorAutomata, PasoTraza, ResultadoTraza
from src.model.automata_nfa import (
    AutomataNFA,
    PasoRamaNFA,
    RamaTrazaNFA,
    ResultadoTrazaNFA,
)

__all__ = [
    "Alfabeto",
    "ErrorAlfabeto",
    "Automata",
    "ErrorAutomata",
    "PasoTraza",
    "ResultadoTraza",
    "AutomataNFA",
    "PasoRamaNFA",
    "RamaTrazaNFA",
    "ResultadoTrazaNFA",
]
