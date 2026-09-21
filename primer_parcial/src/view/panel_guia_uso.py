"""Panel visual interactivo con la Guía de Uso del sistema."""

from __future__ import annotations
from PyQt6.QtWidgets import (
    QFrame,
    QLabel,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)


class PanelGuiaUso(QFrame):
    """Panel de instrucciones detallado para aprender a usar el editor, simulador y conversor."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setStyleSheet(
            "QFrame { background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; }"
        )
        self._inicializar_ui()

    def _inicializar_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        # Encabezado visual
        etiqueta_titulo = QLabel("📖 Manual Completo de Uso e Instrucciones")
        etiqueta_titulo.setStyleSheet(
            "font-size: 15px; font-weight: bold; color: #1e293b; border: none; background: transparent;"
        )
        layout.addWidget(etiqueta_titulo)

        # Visor de texto enriquecido con formato HTML claro, estilizado y didáctico
        self.visor_texto = QTextBrowser()
        self.visor_texto.setOpenExternalLinks(False)
        self.visor_texto.setStyleSheet(
            "QTextBrowser { border: 1px solid #e2e8f0; border-radius: 6px; padding: 14px; "
            "background-color: #f8fafc; color: #1e293b; font-size: 12px; line-height: 1.6; }"
        )

        contenido_html = """
        <div style="font-family: 'Segoe UI', -apple-system, sans-serif; color: #1e293b;">

            <div style="background-color: #eff6ff; border: 1.5px solid #bfdbfe; border-radius: 6px; padding: 10px 14px; margin-bottom: 14px;">
                <b style="color: #1d4ed8; font-size: 13px;">¡Bienvenido a SimulaAutomata!</b><br>
                Plataforma interactiva para el diseño, simulación paso a paso en cinta y conversión formal de
                <b>Autómatas Finitos Deterministas (AFD)</b> y <b>No Deterministas (AFN)</b>.
            </div>

            <!-- SECCIÓN 1: DIBUJO Y EDICIÓN DE GRAFOS -->
            <h3 style="color: #2563eb; margin-top: 10px; border-bottom: 1.5px solid #e2e8f0; padding-bottom: 4px;">
                1. ¿Cómo diseñar y editar el autómata en el lienzo?
            </h3>
            <p>La barra superior de herramientas te permite alternar entre modos de dibujo:</p>
            <ul style="padding-left: 20px;">
                <li><b>🖱️ Modo Cursor (Esc):</b> Permite seleccionar estados, moverlos arrastrando libremente o hacer clic en una conexión para editar sus símbolos.</li>
                <li><b>✋ Modo Desplazar:</b> Mantén presionado el clic izquierdo y arrastra para mover la vista panorámica del lienzo en cualquier dirección.</li>
                <li><b>➕ Modo Estado:</b> Haz clic en cualquier lugar del lienzo punteado para insertar un nuevo nodo formal (ej. <i>q₀, q₁</i>).</li>
                <li><b>➔ Modo Conectar:</b> Haz un <b>primer clic</b> en el estado origen y un <b>segundo clic</b> en el estado destino. Si haces clic sobre el mismo estado, se creará un <b>bucle curvo superior (<i>self-loop</i>)</b>.</li>
                <li><b>🗑️ Modo Borrar (Supr):</b> Haz clic sobre cualquier nodo o flecha para eliminarlo al instante.</li>
                <li><b>Clic Derecho en un Estado:</b> Abre el menú contextual para:
                    <ul>
                        <li><b>Marcar como Inicial:</b> Dibuja la flecha entrante azul formal desde la izquierda (→ <i>q₀</i>).</li>
                        <li><b>Estado de Aceptación:</b> Alterna el <b>doble círculo concéntrico</b> formal de la teoría de la computación.</li>
                        <li><b>Renombrar o Eliminar</b> el estado.</li>
                    </ul>
                </li>
                <li><b>Curvatura Bidireccional Automática:</b> Si creas conexiones de ida y vuelta entre dos nodos (ej. <i>q₀ → q₁</i> y <i>q₁ → q₀</i>), las flechas se curvan suavemente para no solaparse nunca.</li>
            </ul>

            <!-- SECCIÓN 2: HISTORIAL DESHACER / REHACER -->
            <h3 style="color: #2563eb; margin-top: 16px; border-bottom: 1.5px solid #e2e8f0; padding-bottom: 4px;">
                2. Historial de Acciones: Deshacer y Rehacer (Ctrl+Z / Ctrl+Y)
            </h3>
            <p>El sistema cuenta con un gestor completo de historial que registra todas las modificaciones:</p>
            <ul style="padding-left: 20px;">
                <li><b>↶ Deshacer (Ctrl+Z):</b> Revierte la última acción realizada (creación de nodos, conexiones, edición de caracteres, eliminación, limpieza del lienzo o conversión).</li>
                <li><b>↷ Rehacer (Ctrl+Y o Ctrl+Shift+Z):</b> Restaura la acción que acabas de deshacer.</li>
            </ul>

            <!-- SECCIÓN 3: ALFABETO FORMAL -->
            <h3 style="color: #2563eb; margin-top: 16px; border-bottom: 1.5px solid #e2e8f0; padding-bottom: 4px;">
                3. Definición del Alfabeto Formal (Σ)
            </h3>
            <ul style="padding-left: 20px;">
                <li>Los símbolos deben ser caracteres individuales alfanuméricos (letras <code>a-z, A-Z</code> o dígitos <code>0-9</code>).</li>
                <li>Ingrésalos en la barra superior separados por <b>comas o espacios</b> (ej. <code>0, 1</code> o <code>a, b, c</code>) y haz clic en <b>"Establecer Alfabeto"</b>.</li>
                <li>El validador en tiempo real bloquea caracteres pegados sin espacio (ej. <i>"ab"</i>), comas duplicadas y caracteres especiales inválidos.</li>
            </ul>

            <!-- SECCIÓN 4: SIMULACIÓN EN CINTA -->
            <h3 style="color: #2563eb; margin-top: 16px; border-bottom: 1.5px solid #e2e8f0; padding-bottom: 4px;">
                4. Simulación Paso a Paso en Cinta y Unidad de Control
            </h3>
            <ul style="padding-left: 20px;">
                <li><b>Cadena de Entrada vs Expresiones Regulares:</b>
                    <div style="background-color: #fefce8; border: 1px solid #fde047; padding: 8px 12px; border-radius: 6px; margin: 6px 0;">
                        <b>⚠️ Importante:</b> En la cinta se prueban <b>palabras concretas</b> <i>u ∈ Σ*</i> (ej. <code>0101</code>, <code>aab</code>, <code>bb</code>), <b>NO</b> operadores de expresiones regulares como <code>*</code> (Kleene) o <code>+</code>. Para evaluar una expresión como <i>a*b*</i>, se construyen sus transiciones en el grafo y se prueban palabras de ejemplo (ej. <i>ab</i> → aceptada, <i>ba</i> → rechazada).
                    </div>
                </li>
                <li>En la pestaña <b>"📼 Simulador de Cinta y Traza"</b>, escribe la palabra a evaluar y presiona <b>"Iniciar"</b>.</li>
                <li><b>Estructura de la Cinta:</b>
                    <ul>
                        <li><b>Nivel Superior:</b> Celdas de la cinta con la llave <code>{ u }</code> y el delimitador de fin <code>≡</code>.</li>
                        <li><b>Nivel Inferior:</b> Cajas de estado alineadas verticalmente bajo la cinta con flechas ascendentes (↑).</li>
                    </ul>
                </li>
                <li><b>Iluminación Sincronizada:</b> Al avanzar con <code>Siguiente ▶</code>, la celda leída en la cinta y el <b>nodo activo en el grafo</b> se iluminan en amarillo brillante.</li>
                <li><b>Resultado Final:</b> Al llegar a <code>≡</code>, la insignia marca <span style="color:#15803d; font-weight:bold;">✓ ACEPTADA</span> si el estado final pertenece a <i>F</i>, o <span style="color:#b91c1c; font-weight:bold;">✗ RECHAZADA</span> en caso contrario.</li>
            </ul>

            <!-- SECCIÓN 5: NO DETERMINISMO (AFN) -->
            <h3 style="color: #2563eb; margin-top: 16px; border-bottom: 1.5px solid #e2e8f0; padding-bottom: 4px;">
                5. Autómatas No Deterministas (AFN) y Ramas Paralelas
            </h3>
            <ul style="padding-left: 20px;">
                <li>Un autómata es <b>AFN</b> si tiene múltiples transiciones desde un estado con el mismo símbolo hacia distintos destinos (ej. <i>δ(q₀, a) = {q₀, q₁}</i>).</li>
                <li>Durante la simulación de un AFN, el motor calcula <b>todas las ramas en paralelo</b>:
                    <ul>
                        <li>Las ramas sin transición posible se truncan de inmediato con el símbolo <b>∅</b>.</li>
                        <li>Si al menos una rama finaliza en un estado de aceptación al consumir la palabra completa, la cadena es <b>aceptada</b>.</li>
                    </ul>
                </li>
            </ul>

            <!-- SECCIÓN 6: CONVERSIÓN AFN A AFD (MÉTODO DOCENTE) -->
            <h3 style="color: #2563eb; margin-top: 16px; border-bottom: 1.5px solid #e2e8f0; padding-bottom: 4px;">
                6. Conversión Formal de AFN a AFD (Método de Subconjuntos Docente)
            </h3>
            <p>Al detectar conexiones no deterministas, se habilita el botón púrpura <b>⚡ Convertir AFN a AFD</b>:</p>
            <ol style="padding-left: 20px;">
                <li><b>Paso 1 (Identificación):</b> Construye la Tabla 1 del AFN identificando las transiciones múltiples.</li>
                <li><b>Paso 2 (Expansión):</b> Genera la Tabla 2 expandiendo estados compuestos mediante unión formal:
                    <br><code>δ({qᵢ, qⱼ}, σ) = δ(qᵢ, σ) ∪ δ(qⱼ, σ)</code>.
                </li>
                <li><b>Paso 3 (Notación Kₙ):</b> Renombra formalmente los conjuntos a estados simples:
                    <br><code>K₀ = {q₀}, K₁ = {q₁}, K₂ = {q₀, q₁}, ...</code>.
                </li>
                <li><b>Paso 4 (Estados de Aceptación):</b> Identifica los estados de aceptación:
                    <br><i>"Todo estado compuesto que contenga al menos un estado de aceptación original es de aceptación."</i>
                </li>
                <li><b>Paso 5 (Grafo Completo de Tabla 3):</b> Muestra el grafo con todos los estados Kₙ.
                    <ul>
                        <li>Los estados <b>inalcanzables se destacan en rojo</b> y desconectados del flujo inicial.</li>
                        <li>El cuadro es <b>estático puro</b>: los nodos no se desordenan y la vista se desplaza arrastrando con la mano (la rueda del ratón permite deslizar el documento sin quedar atrapada).</li>
                    </ul>
                </li>
                <li><b>Paso 6 (Poda y Tabla 4 Final):</b> Aplica el algoritmo de accesibilidad BFS desde <i>K₀</i>, elimina los inalcanzables y genera el AFD final simplificado.</li>
            </ol>
            <ul style="padding-left: 20px;">
                <li><b>Aplicar al Editor:</b> El botón <code>✔ Aplicar AFD al Editor y Matriz</code> reemplaza el autómata con el AFD resultante en notación Kₙ y distribución circular armónica.</li>
                <li><b>Pestaña Permanente:</b> Tras la conversión, puedes volver a ver el informe completo cuando quieras en la pestaña <b>"📐 Paso a Paso (AFN → AFD)"</b> ubicada al lado de la Matriz de Transiciones.</li>
            </ul>

            <!-- SECCIÓN 7: MATRIZ DE TRANSICIONES -->
            <h3 style="color: #2563eb; margin-top: 16px; border-bottom: 1.5px solid #e2e8f0; padding-bottom: 4px;">
                7. Matriz de Transiciones y Gestión de Estados
            </h3>
            <ul style="padding-left: 20px;">
                <li>Ubicada en la pestaña <b>"📋 Matriz de Transiciones"</b>, se sincroniza bidireccionalmente en tiempo real con el lienzo gráfico.</li>
                <li>Puedes agregar estados ingresando el nombre y marcando si es inicial o de aceptación.</li>
                <li>Haz <b>doble clic en cualquier celda</b> para editar manualmente el estado destino (o varios separados por comas para AFN).</li>
            </ul>

            <!-- SECCIÓN 8: ATAJOS DE TECLADO -->
            <h3 style="color: #2563eb; margin-top: 16px; border-bottom: 1.5px solid #e2e8f0; padding-bottom: 4px;">
                8. Resumen de Atajos Rápidos de Teclado
            </h3>
            <table border="1" cellpadding="6" style="border-collapse: collapse; border-color: #cbd5e1; width: 100%; font-size: 11.5px;">
                <tr style="background-color: #f1f5f9; font-weight: bold; color: #334155;">
                    <td style="width: 35%;">Atajo / Acción</td>
                    <td>Descripción</td>
                </tr>
                <tr>
                    <td><code>Ctrl + Z</code></td>
                    <td>Deshacer última acción (creación, edición, eliminación, conversión).</td>
                </tr>
                <tr>
                    <td><code>Ctrl + Y</code> / <code>Ctrl + Shift + Z</code></td>
                    <td>Rehacer la última acción deshecha.</td>
                </tr>
                <tr>
                    <td><code>Esc</code></td>
                    <td>Volver al modo Selección / Cursor para mover nodos.</td>
                </tr>
                <tr>
                    <td><code>Supr</code> o <code>Backspace</code></td>
                    <td>Eliminar el estado o conexión seleccionada.</td>
                </tr>
                <tr>
                    <td><code>Rueda del ratón (en lienzo)</code></td>
                    <td>Acercar (+) o alejar (-) el zoom de la pizarra.</td>
                </tr>
                <tr>
                    <td><code>Clic Derecho en Nodo/Flecha</code></td>
                    <td>Abrir menú contextual (inicial, aceptación, renombrar, eliminar).</td>
                </tr>
                <tr>
                    <td><code>Doble Clic en Flecha</code></td>
                    <td>Abrir selector para modificar o agregar caracteres de transición.</td>
                </tr>
                <tr>
                    <td><code>Doble Clic en Celda de Matriz</code></td>
                    <td>Editar directamente la transición en la tabla matricial.</td>
                </tr>
            </table>

            <br>
            <div style="text-align: center; color: #64748b; font-size: 11px; margin-top: 10px;">
                SimulaAutomata — Ciencias de la Computación III — Universidad del Quindío
            </div>
        </div>
        """
        self.visor_texto.setHtml(contenido_html)
        layout.addWidget(self.visor_texto, stretch=1)
