"""Controlador principal de la aplicación para coordinar el Modelo y la Vista."""

from __future__ import annotations
from typing import List, Optional, Union

from PyQt6.QtCore import QTimer

from src.model.alfabeto import ErrorAlfabeto
from src.model.automata import Automata, ErrorAutomata, ResultadoTraza
from src.model.automata_nfa import AutomataNFA, ResultadoTrazaNFA
from src.view.ventana_principal import VentanaPrincipal


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

    def al_definir_alfabeto(self, simbolos: List[str]) -> bool:
        """Procesa y valida la actualización del alfabeto formal en el modelo."""
        try:
            self.modelo.definir_alfabeto(simbolos)
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
        if isinstance(self.modelo, AutomataNFA):
            if not destino:
                self.modelo.eliminar_transicion(origen, simbolo)
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
            if hasattr(self.vista, "tabla_transiciones"):
                self.vista.tabla_transiciones.limpiar_advertencia()
            self.vista.mostrar_mensaje_estado(
                f"Transición indefinida/eliminada: δ({origen}, '{simbolo}') = ∅"
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

        try:
            self.modelo.agregar_estado(nombre, es_inicial=es_inicial, es_aceptacion=es_aceptacion)
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
        try:
            self.modelo.eliminar_estado(nombre)
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
        try:
            self.modelo.agregar_estado(nombre, es_inicial=es_inicial, es_aceptacion=es_aceptacion)
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
        try:
            if es_inicial:
                self.modelo.definir_estado_inicial(nombre)
            elif self.modelo.estado_inicial == nombre:
                self.modelo.definir_estado_inicial(None)

            if es_aceptacion:
                self.modelo.agregar_estado_aceptacion(nombre)
            else:
                self.modelo.eliminar_estado_aceptacion(nombre)

            if hasattr(self.vista, "tabla_transiciones"):
                self.vista.tabla_transiciones.actualizar_datos(
                    estados=self.modelo.estados,
                    simbolos=self.modelo.alfabeto.simbolos,
                    transiciones=self.modelo.transiciones,
                    estado_inicial=self.modelo.estado_inicial,
                    estados_aceptacion=self.modelo.estados_aceptacion,
                )
            self._limpiar_simulacion()
            self.vista.mostrar_mensaje_estado(f"Propiedades de '{nombre}' actualizadas.")
        except ErrorAutomata as error:
            self.vista.mostrar_mensaje_estado(f"Error al modificar estado: {error}")

    def al_eliminar_estado_desde_grafo(self, nombre: str) -> None:
        """Elimina del modelo un estado borrado desde el lienzo."""
        try:
            if nombre in self.modelo.estados:
                self.modelo.eliminar_estado(nombre)
                if hasattr(self.vista, "tabla_transiciones"):
                    self.vista.tabla_transiciones.actualizar_datos(
                        estados=self.modelo.estados,
                        simbolos=self.modelo.alfabeto.simbolos,
                        transiciones=self.modelo.transiciones,
                        estado_inicial=self.modelo.estado_inicial,
                        estados_aceptacion=self.modelo.estados_aceptacion,
                    )
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

        try:
            # Si es DFA y ya existe transición a otro destino, convertir a NFA automáticamente
            if not isinstance(self.modelo, AutomataNFA):
                destino_previo = self.modelo.obtener_transicion(origen, simbolo)
                if destino_previo is not None and destino_previo != destino:
                    self.convertir_modelo_a_nfa()

            self.modelo.agregar_transicion(origen, simbolo, destino)
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
        try:
            if isinstance(self.modelo, AutomataNFA):
                self.modelo.eliminar_transicion(origen, simbolo, destino)
            else:
                self.modelo.eliminar_transicion(origen, simbolo)
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

    def al_solicitar_evaluacion(self, cadena: str) -> bool:
        """Inicia la simulación para la cadena u especificada."""
        if not self.modelo.estados:
            if hasattr(self.vista, "panel_simulacion"):
                self.vista.panel_simulacion.mostrar_error_evaluacion(
                    "El autómata no tiene estados definidos en Q."
                )
            return False

        if self.modelo.estado_inicial is None:
            if hasattr(self.vista, "panel_simulacion"):
                self.vista.panel_simulacion.mostrar_error_evaluacion(
                    "El autómata no tiene un estado inicial (q₀) definido."
                )
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
