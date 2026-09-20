"""Punto de entrada principal para ejecutar la aplicación de escritorio."""

from __future__ import annotations
import os
import sys

# Asegurar que el directorio raíz del proyecto esté en sys.path
ruta_raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ruta_raiz not in sys.path:
    sys.path.insert(0, ruta_raiz)

from PyQt6.QtWidgets import QApplication

from src.controller.controlador_automata import ControladorAutomata
from src.model.automata import Automata
from src.view.tema import aplicar_tema_claro
from src.view.ventana_principal import VentanaPrincipal


def crear_aplicacion() -> tuple[QApplication, Automata, VentanaPrincipal, ControladorAutomata]:
    """Inicializa los componentes MVC y la aplicación Qt.

    Returns:
        Tupla con (app, modelo, vista, controlador).
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    aplicar_tema_claro(app)

    modelo = Automata()
    vista = VentanaPrincipal()
    controlador = ControladorAutomata(modelo=modelo, vista=vista)

    return app, modelo, vista, controlador


def main() -> int:
    """Función principal de arranque."""
    app, _modelo, vista, _controlador = crear_aplicacion()
    vista.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
