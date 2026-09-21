"""Controlador principal de la aplicación para coordinar el Modelo y la Vista."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QMessageBox

from src.model.alfabeto import ErrorAlfabeto
from src.model.automata import Automata, ErrorAutomata, ResultadoTraza
from src.model.automata_nfa import AutomataNFA, ResultadoTrazaNFA
from src.model.conversion_nfa_dfa import ResultadoConversionDFA
from src.view.dialogo_conversion_dfa import DialogoConversionDFA
from src.view.ventana_principal import VentanaPrincipal


@dataclass
class SnapshotHistorial:
    """Snapshot inmutable del estado del autómata y posiciones en el lienzo para Deshacer/Rehacer."""
    datos_modelo: dict
    posiciones_nodos: Dict[str, Tuple[float, float]]
    descripcion: str


class ControladorAutomata:
    """Controlador que gestiona la interacción entre el modelo del Autómata y la interfaz gráfica.

    Coordina:
    - Alfabeto Sigma (PanelAlfabeto).
    - Editor Visual de Grafos estilo Draw.io (LienzoGrafo).
    - Matriz de transiciones (TablaTransiciones).
    - Simulación de cinta y unidad de control paso a paso (PanelSimulacion).
    """

    def __init__(self, modelo: Automata | AutomataNFA, vista: VentanaPrincipal) -> None:
        self.modelo = modelo
        self.vista = vista
        self._traza_actual: Optional[Union[ResultadoTraza, ResultadoTrazaNFA]] = None
        self._paso_actual: int = 0
        self._sincronizando_grafo = False

        # Pila de historial para operaciones Deshacer (Ctrl+Z) y Rehacer (Ctrl+Y)
        self._historial_deshacer: List[SnapshotHistorial] = []
        self._historial_rehacer: List[SnapshotHistorial] = []
        self._restaurando_historial: bool = False
        self._ultimo_resultado_conversion: Optional[object] = None

        self._temporizador_animacion = QTimer()
        self._temporizador_animacion.setInterval(450)
        self._temporizador_animacion.timeout.connect(self._al_tick_temporizador_simulacion)

        self._conectar_senales()
        self._inicializar_estado_vista()

    def _conectar_senales(self) -> None:
        """Conecta las señales de los componentes visuales con los métodos de acción."""
        # 1. Señales del panel del alfabeto
        if hasattr(self.vista, "panel_alfabeto"):
            self.vista.panel_alfabeto.alfabeto_solicitado.connect(self.al_definir_alfabeto)

        # 2. Señales de la tabla de transiciones
        if hasattr(self.vista, "tabla_transiciones"):
            self.vista.tabla_transiciones.transicion_modificada.connect(self.al_modificar_transicion)
            self.vista.tabla_transiciones.estado_agregado.connect(self.al_agregar_estado)
            self.vista.tabla_transiciones.estado_eliminado.connect(self.al_eliminar_estado)

        # 3. Señales del panel de simulación
        if hasattr(self.vista, "panel_simulacion"):
            self.vista.panel_simulacion.evaluacion_solicitada.connect(self.al_solicitar_evaluacion)
            self.vista.panel_simulacion.avanzar_paso_solicitado.connect(self.al_avanzar_paso)
            self.vista.panel_simulacion.retroceder_paso_solicitado.connect(self.al_retroceder_paso)
            self.vista.panel_simulacion.ejecutar_todo_solicitado.connect(self.al_ejecutar_todo_automatico)
            self.vista.panel_simulacion.reiniciar_simulacion_solicitado.connect(self.al_reiniciar_simulacion)

        # 4. Señales del editor visual de grafos (LienzoGrafo)
        if hasattr(self.vista, "lienzo_grafo"):
            self.vista.lienzo_grafo.estado_creado.connect(self.al_crear_estado_desde_grafo)
            self.vista.lienzo_grafo.estado_modificado.connect(self.al_modificar_estado_desde_grafo)
            self.vista.lienzo_grafo.estado_eliminado.connect(self.al_eliminar_estado_desde_grafo)
            self.vista.lienzo_grafo.transicion_solicitada.connect(self.al_crear_transicion_desde_grafo)
            self.vista.lienzo_grafo.transicion_eliminada.connect(self.al_eliminar_transicion_desde_grafo)
            self.vista.lienzo_grafo.grafo_limpiado.connect(self.al_limpiar_grafo_completo)

        # 5. Señales para la conversión de AFN a AFD (Construcción de Subconjuntos)
        if hasattr(self.vista, "barra_herramientas_grafo"):
            self.vista.barra_herramientas_grafo.conversion_dfa_solicitada.connect(
                self.al_solicitar_conversion_a_dfa
            )
            self.vista.barra_herramientas_grafo.auto_organizar_solicitado.connect(
                self.al_auto_organizar_grafo
            )
        if hasattr(self.vista, "tabla_transiciones"):
            self.vista.tabla_transiciones.conversion_dfa_solicitada.connect(
                self.al_solicitar_conversion_a_dfa
            )

        # 6. Señales globales para Deshacer (Ctrl+Z) y Rehacer (Ctrl+Y / Ctrl+Shift+Z)
        if hasattr(self.vista, "deshacer_solicitado"):
            self.vista.deshacer_solicitado.connect(self.deshacer)
        if hasattr(self.vista, "rehacer_solicitado"):
            self.vista.rehacer_solicitado.connect(self.rehacer)

    def _inicializar_estado_vista(self) -> None:
        """Sincroniza los componentes de la vista con los datos iniciales del modelo."""
        simbolos_iniciales = self.modelo.alfabeto.simbolos
        if simbolos_iniciales and hasattr(self.vista, "panel_alfabeto"):
            self.vista.panel_alfabeto.actualizar_alfabeto(simbolos_iniciales)
            self.vista.mostrar_mensaje_estado(
                f"Alfabeto inicial cargado: Σ = {{ {', '.join(simbolos_iniciales)} }}"
            )

        self._sincronizar_tabla()
        self._actualizar_vista_simulacion()
        self._actualizar_botones_historial()

    def _sincronizar_tabla(self) -> None:
        """Actualiza la tabla de transiciones y el grafo con el estado vigente del modelo."""
        if hasattr(self.vista, "tabla_transiciones"):
            self.vista.tabla_transiciones.actualizar_datos(
                estados=self.modelo.estados,
                simbolos=self.modelo.alfabeto.simbolos,
                transiciones=self.modelo.transiciones,
                estado_inicial=self.modelo.estado_inicial,
                estados_aceptacion=self.modelo.estados_aceptacion,
            )

        if hasattr(self.vista, "lienzo_grafo") and not self._sincronizando_grafo:
            self._sincronizando_grafo = True
            try:
                self.vista.lienzo_grafo.establecer_alfabeto_permitido(self.modelo.alfabeto.simbolos)
                self.vista.lienzo_grafo.sincronizar_desde_modelo(
                    estados=self.modelo.estados,
                    transiciones=self.modelo.transiciones,
                    estado_inicial=self.modelo.estado_inicial,
                    estados_aceptacion=self.modelo.estados_aceptacion,
                )
            finally:
                self._sincronizando_grafo = False

        # Actualizar botón de conversión a DFA en la barra de herramientas
        if hasattr(self.vista, "barra_herramientas_grafo"):
            es_nfa = self.modelo.es_no_deterministico()
            self.vista.barra_herramientas_grafo.actualizar_estado_no_deterministico(es_nfa)

    def al_definir_alfabeto(self, simbolos: List[str]) -> bool:
        """Procesa y valida la actualización del alfabeto formal en el modelo."""
        snap = self._capturar_snapshot("Cambio de alfabeto")
        try:
            self.modelo.definir_alfabeto(simbolos)
            self._comprometer_snapshot(snap)
            simbolos_actuales = self.modelo.alfabeto.simbolos
            if hasattr(self.vista, "panel_alfabeto"):
                self.vista.panel_alfabeto.actualizar_alfabeto(simbolos_actuales)
            self.vista.mostrar_mensaje_estado(
                f"Alfabeto establecido con éxito: Σ = {{ {', '.join(simbolos_actuales)} }}"
            )
            self._sincronizar_tabla()
            self._limpiar_simulacion()
            return True
        except (ErrorAlfabeto, ErrorAutomata) as error:
            if hasattr(self.vista, "panel_alfabeto"):
                self.vista.panel_alfabeto.mostrar_error(str(error))
            self.vista.mostrar_mensaje_estado(f"Error en alfabeto: {error}")
            return False

    def al_modificar_transicion(self, origen: str, simbolo: str, destino: str) -> bool:
        """Procesa la modificación manual de una celda en la tabla de transiciones."""
        snap = self._capturar_snapshot(f"Modificar transición δ({origen}, '{simbolo}')")
        if isinstance(self.modelo, AutomataNFA):
            if not destino:
                self.modelo.eliminar_transicion(origen, simbolo)
                self._comprometer_snapshot(snap)
                if hasattr(self.vista, "tabla_transiciones"):
                    self.vista.tabla_transiciones.limpiar_advertencia()
                self.vista.mostrar_mensaje_estado(
                    f"Transición NFA eliminada: δ({origen}, '{simbolo}') = ∅"
                )
                self._sincronizar_tabla()
                self._limpiar_simulacion()
                return True

            limpio = destino.replace("{", "").replace("}", "").replace(";", ",")
            destinos = [d.strip() for d in limpio.split(",") if d.strip()]
            if not destinos:
                destinos = [d.strip() for d in limpio.split() if d.strip()]

            for dest in destinos:
                if dest not in self.modelo.estados:
                    mensaje = f"El estado destino '{dest}' no existe en Q: {self.modelo.estados}."
                    if hasattr(self.vista, "tabla_transiciones"):
                        self.vista.tabla_transiciones.mostrar_advertencia(mensaje)
                    self.vista.mostrar_mensaje_estado(f"Validación rechazada: {mensaje}")
                    self._sincronizar_tabla()
                    return False

            try:
                self.modelo.eliminar_transicion(origen, simbolo)
                for dest in destinos:
                    self.modelo.agregar_transicion(origen, simbolo, dest)
                self._comprometer_snapshot(snap)
                if hasattr(self.vista, "tabla_transiciones"):
                    self.vista.tabla_transiciones.limpiar_advertencia()
                self.vista.mostrar_mensaje_estado(
                    f"Transición NFA actualizada: δ({origen}, '{simbolo}') = {{{', '.join(sorted(destinos))}}}"
                )
                self._sincronizar_tabla()
                self._limpiar_simulacion()
                return True
            except (ErrorAutomata, ErrorAlfabeto) as error:
                if hasattr(self.vista, "tabla_transiciones"):
                    self.vista.tabla_transiciones.mostrar_advertencia(str(error))
                self.vista.mostrar_mensaje_estado(f"Error en transición: {error}")
                self._sincronizar_tabla()
                return False

        # Comportamiento para DFA
        if not destino:
            self.modelo.eliminar_transicion(origen, simbolo)
            self._comprometer_snapshot(snap)
            if hasattr(self.vista, "tabla_transiciones"):
                self.vista.tabla_transiciones.limpiar_advertencia()
            self.vista.mostrar_mensaje_estado(
                f"Transición indefinida/eliminada: δ({origen}, '{simbolo}') = ∅"
            )
            self._sincronizar_tabla()
            self._limpiar_simulacion()
            return True

        # Si el usuario ingresó múltiples destinos separados por comas, convertir automáticamente a NFA
        limpio = destino.replace("{", "").replace("}", "").replace(";", ",")
        partes = [d.strip() for d in limpio.split(",") if d.strip()]
        if len(partes) > 1:
            for dest in partes:
                if dest not in self.modelo.estados:
                    mensaje = f"El estado destino '{dest}' no existe en Q: {self.modelo.estados}."
                    if hasattr(self.vista, "tabla_transiciones"):
                        self.vista.tabla_transiciones.mostrar_advertencia(mensaje)
                    self.vista.mostrar_mensaje_estado(f"Validación rechazada: {mensaje}")
                    self._sincronizar_tabla()
                    return False

            self.modelo = self.modelo.convertir_a_nfa()
            self.modelo.eliminar_transicion(origen, simbolo)
            for dest in partes:
                self.modelo.agregar_transicion(origen, simbolo, dest)
            self._comprometer_snapshot(snap)
            if hasattr(self.vista, "tabla_transiciones"):
                self.vista.tabla_transiciones.limpiar_advertencia()
            self.vista.mostrar_mensaje_estado(
                f"Transición NFA actualizada: δ({origen}, '{simbolo}') = {{{', '.join(sorted(partes))}}}"
            )
            self._sincronizar_tabla()
            self._limpiar_simulacion()
            return True

        if destino not in self.modelo.estados:
            mensaje = f"El estado destino '{destino}' no existe en Q: {self.modelo.estados}."
            if hasattr(self.vista, "tabla_transiciones"):
                self.vista.tabla_transiciones.mostrar_advertencia(mensaje)
            self.vista.mostrar_mensaje_estado(f"Validación rechazada: {mensaje}")
            self._sincronizar_tabla()
            return False

        try:
            self.modelo.agregar_transicion(origen, simbolo, destino)
            self._comprometer_snapshot(snap)
            if hasattr(self.vista, "tabla_transiciones"):
                self.vista.tabla_transiciones.limpiar_advertencia()
            self.vista.mostrar_mensaje_estado(
                f"Transición actualizada: δ({origen}, '{simbolo}') = {destino}"
            )
            self._sincronizar_tabla()
            self._limpiar_simulacion()
            return True
        except (ErrorAutomata, ErrorAlfabeto) as error:
            if hasattr(self.vista, "tabla_transiciones"):
                self.vista.tabla_transiciones.mostrar_advertencia(str(error))
            self.vista.mostrar_mensaje_estado(f"Error en transición: {error}")
            self._sincronizar_tabla()
            return False

    def al_agregar_estado(self, nombre: str, es_inicial: bool, es_aceptacion: bool) -> bool:
        """Registra un nuevo estado en el modelo y sincroniza la vista."""
        if nombre in self.modelo.estados:
            if hasattr(self.vista, "tabla_transiciones"):
                self.vista.tabla_transiciones.mostrar_advertencia(
                    f"El estado '{nombre}' ya existe en el autómata."
                )
            return False

        snap = self._capturar_snapshot(f"Agregar estado '{nombre}'")
        try:
            self.modelo.agregar_estado(nombre, es_inicial=es_inicial, es_aceptacion=es_aceptacion)
            self._comprometer_snapshot(snap)
            if hasattr(self.vista, "tabla_transiciones"):
                self.vista.tabla_transiciones.limpiar_advertencia()
            self.vista.mostrar_mensaje_estado(f"Estado '{nombre}' agregado exitosamente a Q.")
            self._sincronizar_tabla()
            self._limpiar_simulacion()
            return True
        except ErrorAutomata as error:
            if hasattr(self.vista, "tabla_transiciones"):
                self.vista.tabla_transiciones.mostrar_advertencia(str(error))
            self.vista.mostrar_mensaje_estado(f"Error al agregar estado: {error}")
            return False

    def al_eliminar_estado(self, nombre: str) -> bool:
        """Elimina un estado en el modelo y sincroniza la vista."""
        if nombre not in self.modelo.estados:
            return False
        snap = self._capturar_snapshot(f"Eliminar estado '{nombre}'")
        try:
            self.modelo.eliminar_estado(nombre)
            self._comprometer_snapshot(snap)
            if hasattr(self.vista, "tabla_transiciones"):
                self.vista.tabla_transiciones.limpiar_advertencia()
            self.vista.mostrar_mensaje_estado(f"Estado '{nombre}' eliminado de Q.")
            self._sincronizar_tabla()
            self._limpiar_simulacion()
            return True
        except ErrorAutomata as error:
            if hasattr(self.vista, "tabla_transiciones"):
                self.vista.tabla_transiciones.mostrar_advertencia(str(error))
            self.vista.mostrar_mensaje_estado(f"Error al eliminar estado: {error}")
            return False

    # ==========================================================================
    # Sincronización desde el Editor de Grafos (Draw.io)
    # ==========================================================================

    def al_crear_estado_desde_grafo(
        self,
        nombre: str,
        x: float,
        y: float,
        es_inicial: bool,
        es_aceptacion: bool,
    ) -> None:
        """Registra en el modelo un estado dibujado directamente en el lienzo."""
        snap = self._capturar_snapshot(f"Crear estado '{nombre}' en lienzo")
        try:
            self.modelo.agregar_estado(nombre, es_inicial=es_inicial, es_aceptacion=es_aceptacion)
            self._comprometer_snapshot(snap)
            if hasattr(self.vista, "tabla_transiciones"):
                self.vista.tabla_transiciones.actualizar_datos(
                    estados=self.modelo.estados,
                    simbolos=self.modelo.alfabeto.simbolos,
                    transiciones=self.modelo.transiciones,
                    estado_inicial=self.modelo.estado_inicial,
                    estados_aceptacion=self.modelo.estados_aceptacion,
                )
            self._limpiar_simulacion()
            self.vista.mostrar_mensaje_estado(f"Estado '{nombre}' creado en el lienzo.")
        except ErrorAutomata as error:
            self.vista.mostrar_mensaje_estado(f"Error al crear estado: {error}")

    def al_modificar_estado_desde_grafo(
        self,
        nombre: str,
        es_inicial: bool,
        es_aceptacion: bool,
    ) -> None:
        """Actualiza atributos inicial/aceptación de un nodo modificado en el lienzo."""
        snap = self._capturar_snapshot(f"Modificar estado '{nombre}'")
        try:
            if es_inicial:
                self.modelo.definir_estado_inicial(nombre)
            elif self.modelo.estado_inicial == nombre:
                self.modelo.definir_estado_inicial(None)

            if es_aceptacion:
                self.modelo.agregar_estado_aceptacion(nombre)
            else:
                self.modelo.eliminar_estado_aceptacion(nombre)

            self._comprometer_snapshot(snap)
            self._sincronizar_tabla()
            self._limpiar_simulacion()
            self.vista.mostrar_mensaje_estado(f"Propiedades de '{nombre}' actualizadas.")
        except ErrorAutomata as error:
            self.vista.mostrar_mensaje_estado(f"Error al modificar estado: {error}")

    def al_eliminar_estado_desde_grafo(self, nombre: str) -> None:
        """Elimina del modelo un estado borrado desde el lienzo."""
        if nombre not in self.modelo.estados:
            return
        snap = self._capturar_snapshot(f"Eliminar estado '{nombre}'")
        try:
            self.modelo.eliminar_estado(nombre)
            self._comprometer_snapshot(snap)
            self._sincronizar_tabla()
            self._limpiar_simulacion()
            self.vista.mostrar_mensaje_estado(f"Estado '{nombre}' eliminado.")
        except ErrorAutomata as error:
            self.vista.mostrar_mensaje_estado(f"Error al eliminar estado: {error}")

    def al_crear_transicion_desde_grafo(
        self,
        origen: str,
        simbolo: str,
        destino: str,
    ) -> None:
        """Agrega una transición conectada con flecha en el lienzo hacia el modelo."""
        if not self.modelo.alfabeto.contiene(simbolo):
            self.vista.mostrar_mensaje_estado(
                f"El símbolo '{simbolo}' no pertenece a Sigma: {self.modelo.alfabeto.simbolos}."
            )
            self._sincronizar_tabla()
            return

        snap = self._capturar_snapshot(f"Crear transición δ({origen}, '{simbolo}') = {destino}")
        try:
            # Si es DFA y ya existe transición a otro destino, convertir a NFA automáticamente
            if not isinstance(self.modelo, AutomataNFA):
                destino_previo = self.modelo.obtener_transicion(origen, simbolo)
                if destino_previo is not None and destino_previo != destino:
                    self.convertir_modelo_a_nfa()

            self.modelo.agregar_transicion(origen, simbolo, destino)
            self._comprometer_snapshot(snap)
            self._sincronizar_tabla()
            self._limpiar_simulacion()
            self.vista.mostrar_mensaje_estado(
                f"Transición conectada: δ({origen}, '{simbolo}') = {destino}"
            )
        except (ErrorAutomata, ErrorAlfabeto) as error:
            self.vista.mostrar_mensaje_estado(f"Error en transición: {error}")
            self._sincronizar_tabla()

    def al_eliminar_transicion_desde_grafo(
        self,
        origen: str,
        simbolo: str,
        destino: str,
    ) -> None:
        """Elimina una transición borrada desde el lienzo."""
        snap = self._capturar_snapshot(f"Eliminar transición δ({origen}, '{simbolo}')")
        try:
            if isinstance(self.modelo, AutomataNFA):
                self.modelo.eliminar_transicion(origen, simbolo, destino)
            else:
                self.modelo.eliminar_transicion(origen, simbolo)
            self._comprometer_snapshot(snap)
            self._sincronizar_tabla()
            self._limpiar_simulacion()
            self.vista.mostrar_mensaje_estado(
                f"Transición eliminada: δ({origen}, '{simbolo}')"
            )
        except ErrorAutomata as error:
            self.vista.mostrar_mensaje_estado(f"Error al eliminar transición: {error}")

    # ==========================================================================
    # Métodos de Simulación y Traza Paso a Paso
    # ==========================================================================

    def _mostrar_alerta_advertencia(self, titulo: str, mensaje: str) -> None:
        """Muestra un mensaje de advertencia visible en la barra de estado y mediante QMessageBox."""
        if hasattr(self.vista, "mostrar_mensaje_estado"):
            self.vista.mostrar_mensaje_estado(f"⚠ {titulo}: {mensaje.splitlines()[0]}")
        import os
        if not os.environ.get("PYTEST_CURRENT_TEST"):
            QMessageBox.warning(self.vista, titulo, mensaje)

    def al_solicitar_evaluacion(self, cadena: str) -> bool:
        """Inicia la simulación para la cadena u especificada."""
        if not self.modelo.estados:
            mensaje = "El autómata no tiene estados definidos en Q."
            if hasattr(self.vista, "panel_simulacion"):
                self.vista.panel_simulacion.mostrar_error_evaluacion(mensaje)
            self._mostrar_alerta_advertencia("Sin Estados", mensaje)
            return False

        if self.modelo.estado_inicial is None:
            mensaje = "El autómata no tiene un estado inicial (q₀) definido."
            if hasattr(self.vista, "panel_simulacion"):
                self.vista.panel_simulacion.mostrar_error_evaluacion(mensaje)
            self._mostrar_alerta_advertencia("Sin Estado Inicial", mensaje)
            return False

        if not self.modelo.estados_aceptacion:
            mensaje_simulacion = "No se puede leer la cadena: el autómata no tiene ningún estado final (de aceptación) definido."
            mensaje_alerta = (
                "No se puede leer la cadena porque el autómata no tiene ningún estado final (de aceptación) definido.\n\n"
                "Para definir un estado final:\n"
                "• Haga clic derecho sobre un estado en el lienzo y seleccione «Estado de Aceptación (F)» (se dibujará con doble círculo), o\n"
                "• Marque la casilla «Aceptación (F)» al agregar estados en la matriz de transiciones."
            )
            if hasattr(self.vista, "panel_simulacion"):
                self.vista.panel_simulacion.mostrar_error_evaluacion(mensaje_simulacion)
            self._mostrar_alerta_advertencia("Sin Estado Final", mensaje_alerta)
            return False

        try:
            self._temporizador_animacion.stop()
            traza = self.modelo.generar_traza(cadena)
            self._traza_actual = traza
            self._paso_actual = 0
            self._actualizar_vista_simulacion()

            estado_acept = "aceptada" if traza.aceptada else "rechazada"
            self.vista.mostrar_mensaje_estado(
                f"Simulación lista para '{cadena}'. Resultado final: {estado_acept}."
            )
            return True
        except (ErrorAlfabeto, ErrorAutomata) as error:
            self._temporizador_animacion.stop()
            self._traza_actual = None
            self._paso_actual = 0
            if hasattr(self.vista, "panel_simulacion"):
                self.vista.panel_simulacion.mostrar_error_evaluacion(str(error))
            self.vista.mostrar_mensaje_estado(f"Error de validación: {error}")
            self._mostrar_alerta_advertencia("Error en Cadena de Entrada", str(error))
            return False

    def _obtener_total_pasos(self) -> int:
        """Obtiene la cantidad total de pasos de la traza activa."""
        if self._traza_actual is None:
            return 0
        if isinstance(self._traza_actual, ResultadoTrazaNFA):
            return self._traza_actual.total_pasos
        return len(self._traza_actual.pasos)

    def al_avanzar_paso(self) -> None:
        """Avanza un paso en la simulación activa."""
        self._temporizador_animacion.stop()
        total = self._obtener_total_pasos()
        if self._traza_actual and self._paso_actual < total - 1:
            self._paso_actual += 1
            self._actualizar_vista_simulacion()

    def al_retroceder_paso(self) -> None:
        """Retrocede un paso en la simulación activa."""
        self._temporizador_animacion.stop()
        if self._traza_actual and self._paso_actual > 0:
            self._paso_actual -= 1
            self._actualizar_vista_simulacion()

    def al_ejecutar_todo(self) -> None:
        """Avanza directamente al paso final de la simulación de forma síncrona."""
        self._temporizador_animacion.stop()
        total = self._obtener_total_pasos()
        if self._traza_actual and total > 0:
            self._paso_actual = total - 1
            self._actualizar_vista_simulacion()

    def al_ejecutar_todo_automatico(self) -> None:
        """Ejecuta la simulación paso a paso automáticamente con animación temporizada."""
        total = self._obtener_total_pasos()
        if not self._traza_actual or total <= 0:
            return

        if self._paso_actual >= total - 1:
            # Si ya está en el último paso, reiniciar al primero para volver a ejecutar
            self._paso_actual = 0
            self._actualizar_vista_simulacion()

        if self._temporizador_animacion.isActive():
            self._temporizador_animacion.stop()
        else:
            self._temporizador_animacion.start()

    def _al_tick_temporizador_simulacion(self) -> None:
        """Avanza un paso de animación del temporizador automático."""
        total = self._obtener_total_pasos()
        if self._traza_actual and self._paso_actual < total - 1:
            self._paso_actual += 1
            self._actualizar_vista_simulacion()
            if self._paso_actual >= total - 1:
                self._temporizador_animacion.stop()
        else:
            self._temporizador_animacion.stop()

    def al_reiniciar_simulacion(self) -> None:
        """Regresa la simulación al paso inicial (paso 0)."""
        self._temporizador_animacion.stop()
        if self._traza_actual:
            self._paso_actual = 0
            self._actualizar_vista_simulacion()

    def al_limpiar_grafo_completo(self) -> None:
        """Limpia por completo el modelo, el editor visual, la tabla y la simulación."""
        self._temporizador_animacion.stop()
        self.registrar_snapshot("Limpiar lienzo y autómata")
        self.modelo.limpiar()
        if hasattr(self.vista, "lienzo_grafo"):
            self.vista.lienzo_grafo.limpiar_grafo(notificar=False)
            self.vista.lienzo_grafo.resaltar_estado(None)
        if hasattr(self.vista, "tabla_transiciones"):
            self.vista.tabla_transiciones.actualizar_datos(
                estados=[],
                simbolos=self.modelo.alfabeto.simbolos,
                transiciones={},
                estado_inicial=None,
                estados_aceptacion=set(),
            )
        if hasattr(self.vista, "panel_simulacion"):
            self.vista.panel_simulacion.limpiar()
        self._ultimo_resultado_conversion = None
        if hasattr(self.vista, "ocultar_paso_a_paso_conversion"):
            self.vista.ocultar_paso_a_paso_conversion()
        self._limpiar_simulacion()
        self.vista.mostrar_mensaje_estado("Grafo y datos del autómata limpiados por completo.")

    def _actualizar_vista_simulacion(self) -> None:
        """Notifica al panel de simulación y resalta el estado activo en el grafo."""
        total_pasos = self._obtener_total_pasos()
        if hasattr(self.vista, "panel_simulacion"):
            self.vista.panel_simulacion.actualizar_estado(
                traza=self._traza_actual,
                paso_actual=self._paso_actual,
                total_pasos=total_pasos,
            )

        # Resaltar en el grafo el estado activo en el paso actual
        if hasattr(self.vista, "lienzo_grafo"):
            estado_activo = None
            if self._traza_actual:
                if isinstance(self._traza_actual, ResultadoTrazaNFA):
                    for rama in self._traza_actual.ramas:
                        for p in rama.pasos:
                            if p.indice_paso == self._paso_actual:
                                estado_activo = p.estado_actual
                                break
                        if estado_activo:
                            break
                elif self._paso_actual < len(self._traza_actual.pasos):
                    estado_activo = self._traza_actual.pasos[self._paso_actual].estado_actual
            self.vista.lienzo_grafo.resaltar_estado(estado_activo)

    def _limpiar_simulacion(self) -> None:
        """Reinicia la simulación ante cambios estructurales en el autómata."""
        self._temporizador_animacion.stop()
        self._traza_actual = None
        self._paso_actual = 0
        self._actualizar_vista_simulacion()

    def convertir_modelo_a_nfa(self) -> AutomataNFA:
        """Convierte el modelo DFA actual a AutomataNFA."""
        if not isinstance(self.modelo, AutomataNFA):
            self.modelo = self.modelo.convertir_a_nfa()
            self._sincronizar_tabla()
            self._limpiar_simulacion()
            self.vista.mostrar_mensaje_estado(
                "Modelo convertido exitosamente a Autómata No Determinista (NFA)."
            )
        return self.modelo

    def al_solicitar_conversion_a_dfa(self) -> None:
        """Abre el diálogo interactivo para convertir de AFN a AFD con tabla de proceso."""
        if not self.modelo.estados_aceptacion:
            mensaje_alerta = (
                "No se puede convertir a AFD porque el autómata no tiene ningún estado final (de aceptación) definido.\n\n"
                "La conversión formal requiere el conjunto de estados de aceptación F para determinar los estados finales del AFD (Paso 4).\n\n"
                "Para definir un estado final:\n"
                "• Haga clic derecho sobre un estado en el lienzo y seleccione «Estado de Aceptación (F)» (se dibujará con doble círculo), o\n"
                "• Active la casilla «Aceptación (F)» en la matriz de transiciones."
            )
            self._mostrar_alerta_advertencia("Sin Estado Final", mensaje_alerta)
            return

        if self.modelo.estado_inicial is None:
            mensaje_alerta = "No se puede convertir a AFD: el autómata no tiene un estado inicial (q₀) definido."
            self._mostrar_alerta_advertencia("Sin Estado Inicial", mensaje_alerta)
            return

        if not self.modelo.es_no_deterministico():
            self.vista.mostrar_mensaje_estado(
                "El autómata actual ya es determinista (AFD). No requiere conversión."
            )
            import os
            if not os.environ.get("PYTEST_CURRENT_TEST"):
                QMessageBox.information(
                    self.vista,
                    "Autómata ya es Determinista",
                    "El autómata actual ya es Determinista (AFD).\n\n"
                    "Cada estado tiene a lo sumo una transición definida por símbolo. "
                    "La conversión formal aplica a autómatas no deterministas (AFN) con transiciones múltiples."
                )
            return

        # Si el modelo aún no es instancia de AutomataNFA formal pero tiene no determinismo
        if not isinstance(self.modelo, AutomataNFA):
            self.convertir_modelo_a_nfa()

        dialogo = DialogoConversionDFA(self.modelo, parent=self.vista)
        dialogo.aplicar_afd_solicitado.connect(self.al_aplicar_conversion_dfa)
        dialogo.exec()

    def al_aplicar_conversion_dfa(self, resultado: object) -> None:
        """Sustituye el modelo por el AFD equivalente generado y sincroniza toda la interfaz."""
        dfa_a_aplicar = getattr(resultado, "dfa_final", getattr(resultado, "dfa", None))
        if dfa_a_aplicar is None:
            return
        self.registrar_snapshot("Conversión de AFN a AFD")
        self._ultimo_resultado_conversion = resultado
        self.modelo = dfa_a_aplicar
        self._sincronizar_tabla()
        self._limpiar_simulacion()

        # Distribuir geométricamente los nuevos estados del AFD en el lienzo
        if hasattr(self.vista, "lienzo_grafo"):
            self.vista.lienzo_grafo.auto_organizar_nodos()

        if hasattr(self.vista, "mostrar_paso_a_paso_conversion"):
            self.vista.mostrar_paso_a_paso_conversion(resultado)

        self.vista.mostrar_mensaje_estado(
            f"✔ Conversión completada: AFN transformado exitosamente a AFD con {len(self.modelo.estados)} estados deterministas (Notación Kn)."
        )

    # ==========================================================================
    # Gestión de Historial: Deshacer (Ctrl+Z) y Rehacer (Ctrl+Y / Ctrl+Shift+Z)
    # ==========================================================================

    def _capturar_posiciones_grafo(self) -> Dict[str, Tuple[float, float]]:
        """Obtiene las coordenadas (x, y) de todos los nodos actuales del lienzo."""
        posiciones: Dict[str, Tuple[float, float]] = {}
        if hasattr(self.vista, "lienzo_grafo") and hasattr(self.vista.lienzo_grafo, "nodos"):
            for nombre, nodo in self.vista.lienzo_grafo.nodos.items():
                posiciones[nombre] = (float(nodo.pos().x()), float(nodo.pos().y()))
        return posiciones

    def _capturar_snapshot(self, descripcion: str = "") -> SnapshotHistorial:
        """Crea un snapshot del estado del modelo y posiciones en el lienzo."""
        return SnapshotHistorial(
            datos_modelo=self.modelo.a_diccionario(),
            posiciones_nodos=self._capturar_posiciones_grafo(),
            descripcion=descripcion,
        )

    def _comprometer_snapshot(self, snapshot: SnapshotHistorial) -> None:
        """Guarda un snapshot en la pila de deshacer y limpia la de rehacer."""
        if self._restaurando_historial:
            return
        self._historial_deshacer.append(snapshot)
        if len(self._historial_deshacer) > 50:
            self._historial_deshacer.pop(0)
        self._historial_rehacer.clear()
        self._actualizar_botones_historial()

    def registrar_snapshot(self, descripcion: str = "") -> None:
        """Captura y guarda el estado actual en el historial de deshacer."""
        snapshot = self._capturar_snapshot(descripcion)
        self._comprometer_snapshot(snapshot)

    def _actualizar_botones_historial(self) -> None:
        """Actualiza el estado habilitado/deshabilitado de los botones Deshacer y Rehacer."""
        if hasattr(self.vista, "barra_herramientas_grafo"):
            self.vista.barra_herramientas_grafo.actualizar_estado_historial(
                puede_deshacer=len(self._historial_deshacer) > 0,
                puede_rehacer=len(self._historial_rehacer) > 0,
            )

    def deshacer(self) -> bool:
        """Deshace la última acción realizada, restaurando el modelo y las posiciones previas."""
        if not self._historial_deshacer:
            self.vista.mostrar_mensaje_estado("No hay más acciones para deshacer.")
            return False

        # Guardar estado actual en la pila de rehacer antes de restaurar
        snapshot_actual = self._capturar_snapshot("Estado previo a deshacer")
        self._historial_rehacer.append(snapshot_actual)

        snapshot_previo = self._historial_deshacer.pop()
        self._restaurar_snapshot(snapshot_previo)
        self._actualizar_botones_historial()
        self.vista.mostrar_mensaje_estado(
            f"↶ Deshecho: {snapshot_previo.descripcion or 'Acción revertida'}."
        )
        return True

    def rehacer(self) -> bool:
        """Rehace la última acción deshecha."""
        if not self._historial_rehacer:
            self.vista.mostrar_mensaje_estado("No hay más acciones para rehacer.")
            return False

        snapshot_actual = self._capturar_snapshot("Estado previo a rehacer")
        self._historial_deshacer.append(snapshot_actual)

        snapshot_siguiente = self._historial_rehacer.pop()
        self._restaurar_snapshot(snapshot_siguiente)
        self._actualizar_botones_historial()
        self.vista.mostrar_mensaje_estado(
            f"↷ Rehecho: {snapshot_siguiente.descripcion or 'Acción restaurada'}."
        )
        return True

    def _restaurar_snapshot(self, snapshot: SnapshotHistorial) -> None:
        """Restaura completamente el modelo y la vista a partir de un snapshot."""
        self._restaurando_historial = True
        try:
            # Reconstruir modelo polimórficamente (DFA o NFA)
            self.modelo = Automata.desde_diccionario(snapshot.datos_modelo)

            if hasattr(self.vista, "panel_alfabeto"):
                self.vista.panel_alfabeto.actualizar_alfabeto(self.modelo.alfabeto.simbolos)

            if hasattr(self.vista, "tabla_transiciones"):
                self.vista.tabla_transiciones.actualizar_datos(
                    estados=self.modelo.estados,
                    simbolos=self.modelo.alfabeto.simbolos,
                    transiciones=self.modelo.transiciones,
                    estado_inicial=self.modelo.estado_inicial,
                    estados_aceptacion=self.modelo.estados_aceptacion,
                )

            if hasattr(self.vista, "lienzo_grafo"):
                self._sincronizando_grafo = True
                try:
                    self.vista.lienzo_grafo.establecer_alfabeto_permitido(self.modelo.alfabeto.simbolos)
                    self.vista.lienzo_grafo.sincronizar_desde_modelo(
                        estados=self.modelo.estados,
                        transiciones=self.modelo.transiciones,
                        estado_inicial=self.modelo.estado_inicial,
                        estados_aceptacion=self.modelo.estados_aceptacion,
                        posiciones_restauradas=snapshot.posiciones_nodos,
                    )
                finally:
                    self._sincronizando_grafo = False

            if hasattr(self.vista, "barra_herramientas_grafo"):
                es_nfa = self.modelo.es_no_deterministico()
                self.vista.barra_herramientas_grafo.actualizar_estado_no_deterministico(es_nfa)

            # Sincronizar visibilidad del panel paso a paso según el autómata restaurado
            es_nfa_actual = self.modelo.es_no_deterministico()
            tiene_estados_kn = any(e.startswith("K") for e in self.modelo.estados)
            if es_nfa_actual or not tiene_estados_kn:
                if hasattr(self.vista, "ocultar_paso_a_paso_conversion"):
                    self.vista.ocultar_paso_a_paso_conversion()
            elif self._ultimo_resultado_conversion:
                if hasattr(self.vista, "mostrar_paso_a_paso_conversion"):
                    self.vista.mostrar_paso_a_paso_conversion(self._ultimo_resultado_conversion)

            self._limpiar_simulacion()
        finally:
            self._restaurando_historial = False

    def al_auto_organizar_grafo(self) -> None:
        """Distribuye automáticamente los nodos guardando el estado previo en el historial."""
        self.registrar_snapshot("Auto-distribuir nodos")
        if hasattr(self.vista, "lienzo_grafo"):
            self.vista.lienzo_grafo.auto_organizar_nodos()
        self.vista.mostrar_mensaje_estado("Nodos auto-distribuidos en el lienzo.")

