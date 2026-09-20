"""Panel visual interactivo con la Guía de Uso del sistema."""

from __future__ import annotations
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)


class PanelGuiaUso(QFrame):
    """Panel de instrucciones detallado para aprender a usar el editor y simulador."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setStyleSheet(
            "QFrame { background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; }"
        )
        self._inicializar_ui()

    def _inicializar_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Encabezado visual
        etiqueta_titulo = QLabel("📖 Manual Rápido de Uso e Instrucciones")
        etiqueta_titulo.setStyleSheet(
            "font-size: 15px; font-weight: bold; color: #1e293b; border: none; background: transparent;"
        )
        layout.addWidget(etiqueta_titulo)

        # Visor de texto enriquecido con formato HTML claro y legible
        self.visor_texto = QTextBrowser()
        self.visor_texto.setOpenExternalLinks(False)
        self.visor_texto.setStyleSheet(
            "QTextBrowser { border: 1px solid #e2e8f0; border-radius: 6px; padding: 12px; "
            "background-color: #f8fafc; color: #1e293b; font-size: 12.5px; line-height: 1.6; }"
        )

        contenido_html = """
        <div style="font-family: 'Segoe UI', sans-serif; color: #1e293b;">
            <h3 style="color: #2563eb; margin-top: 0;">1. ¿Cómo crear y pintar un autómata?</h3>
            <ul style="padding-left: 20px;">
                <li><b>Crear Estado:</b> Haz clic en el botón <code>➕⭕ Crear Estado</code> arriba y luego haz clic en cualquier lugar del lienzo punteado. Se creará un estado (ej. <i>q₀</i>).</li>
                <li><b>Arrastrar / Mover:</b> Con el botón <code>🖱️ Mover / Cursor</code> activo, haz clic sobre cualquier estado y arrástralo libremente para acomodarlo.</li>
                <li><b>Estado Inicial (q₀):</b> Haz clic derecho sobre el estado y selecciona <i>"Marcar como Inicial"</i>. Aparecerá una flecha azul con la palabra <i>"inicio"</i>.</li>
                <li><b>Estado de Aceptación (F):</b> Haz clic derecho y elige <i>"Estado de Aceptación"</i>. Se dibujará el <b>doble círculo concéntrico</b> formal.</li>
            </ul>

            <h3 style="color: #2563eb; margin-top: 14px;">2. ¿Cómo conectar estados con flechas?</h3>
            <ul style="padding-left: 20px;">
                <li>Selecciona el botón <code>➔ Conectar Flecha</code>.</li>
                <li><b>Conexión a dos clics:</b> Haz un <b>primer clic</b> en el estado origen y luego un <b>segundo clic</b> en el estado destino (o en el mismo para bucles). También puedes arrastrar si lo prefieres.</li>
                <li>Se abrirá un cuadro para ingresar el símbolo o símbolos permitidos (ej. <b>0</b> o <b>a</b>).</li>
                <li><b>Bucles sobre el mismo estado:</b> Haz clic en el estado y luego otro clic sobre el mismo estado para crear un lazo curvo superior (<i>self-loop</i>).</li>
                <li><b>Editar transición:</b> Haz doble clic sobre cualquier flecha o etiqueta para cambiar o añadir símbolos.</li>
            </ul>

            <h3 style="color: #2563eb; margin-top: 14px;">3. Definición del Alfabeto Formal (Σ)</h3>
            <ul style="padding-left: 20px;">
                <li>Solo se permiten <b>letras</b> (A-Z, a-z) o <b>números</b> (0-9).</li>
                <li>Cada símbolo debe ser exactamente de <b>un solo carácter</b> (ej. <code>0, 1</code> o <code>a, b, c</code>).</li>
                <li>Deben estar separados por <b>comas o espacios</b>. El editor bloquea automáticamente caracteres pegados sin separación (ej. <i>"ab"</i>), comas consecutivas (<i>",,"</i>) y espacios dobles.</li>
            </ul>

            <h3 style="color: #2563eb; margin-top: 14px;">4. ¿Cómo simular una cadena en la cinta?</h3>
            <ul style="padding-left: 20px;">
                <li>En la pestaña <b>"📼 Simulador de Cinta y Traza"</b>, escribe la palabra a evaluar en el campo <i>"Cadena (u)"</i> (ej. <code>0101</code> o <code>aab</code>) y presiona <b>"Iniciar Simulación"</b>.</li>
                <li>Verás la cinta superior con la llave <code>{ u }</code> y el delimitador de fin de cadena <code>≡</code>.</li>
                <li>Usa <code>Paso Siguiente ▶</code> para avanzar. En cada paso:
                    <ul>
                        <li>La celda de la cinta leída se resalta en <b>amarillo</b> con su flecha ascendente (↑).</li>
                        <li><b>¡El nodo activo en el grafo también se ilumina en amarillo brillante!</b></li>
                    </ul>
                </li>
                <li>Al terminar, la insignia marcará en <span style="color:#15803d; font-weight:bold;">verde (✓ ACEPTADA)</span> o <span style="color:#b91c1c; font-weight:bold;">rojo (✗ RECHAZADA)</span>.</li>
            </ul>

            <h3 style="color: #2563eb; margin-top: 14px;">5. Autómatas No Deterministas (NFA)</h3>
            <p>Puedes conectar múltiples flechas con el mismo símbolo desde un estado hacia distintos destinos (ej. δ(q₀, 0) = {q₀, q₁}). Durante la simulación:</p>
            <ul style="padding-left: 20px;">
                <li>Se dibujarán <b>ramas paralelas</b> para cada camino computacional posible.</li>
                <li>Las ramas que alcancen un estado sin transición se truncarán prematuramente con el símbolo <b>∅</b>.</li>
                <li>Si al menos una rama finaliza en un estado de aceptación al llegar a <code>≡</code>, la palabra es <b>aceptada</b>.</li>
            </ul>

            <h3 style="color: #2563eb; margin-top: 14px;">6. Atajos rápidos de teclado</h3>
            <table border="1" cellpadding="6" style="border-collapse: collapse; border-color: #cbd5e1; width: 100%;">
                <tr style="background-color: #f1f5f9; font-weight: bold;">
                    <td>Tecla</td>
                    <td>Acción</td>
                </tr>
                <tr>
                    <td><code>Esc</code></td>
                    <td>Volver al modo Selección / Cursor para arrastrar.</td>
                </tr>
                <tr>
                    <td><code>Supr</code> o <code>Backspace</code></td>
                    <td>Eliminar el estado o flecha seleccionada.</td>
                </tr>
                <tr>
                    <td><code>Clic Derecho</code></td>
                    <td>Menú contextual con opciones del estado o flecha.</td>
                </tr>
                <tr>
                    <td><code>Doble Clic</code></td>
                    <td>Editar símbolos de una transición existente.</td>
                </tr>
            </table>
        </div>
        """
        self.visor_texto.setHtml(contenido_html)
        layout.addWidget(self.visor_texto, stretch=1)
