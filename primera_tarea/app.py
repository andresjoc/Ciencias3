"""
Servidor Flask para el TDA Pila interactivo (Paso a paso).
Mantiene el estado de la pila en la sesión del navegador.
"""

from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)

# Clave secreta requerida por Flask para encriptar y gestionar la sesión
app.secret_key = "clave"

# Mapeo de correspondencias: Símbolo de cierre -> Símbolo de apertura
PAREJAS = {
    ')': '(',
    ']': '[',
    '}': '{'
}


def inicializar_sesion():
    """Inicializa las variables de estado en la sesión si aún no existen."""
    if "pila" not in session:
        session["pila"] = []
    if "mensaje_estado" not in session:
        session["mensaje_estado"] = "Ingrese un símbolo para comenzar la simulación."
    if "tipo_estado" not in session:
        session["tipo_estado"] = "info"  # info, success, error


@app.route("/")
def index():
    """Ruta principal: Muestra la interfaz gráfica con el estado actual."""
    inicializar_sesion()
    return render_template(
        "index.html",
        pila=session["pila"],
        mensaje_estado=session["mensaje_estado"],
        tipo_estado=session["tipo_estado"]
    )


@app.route("/agregar", methods=["POST"])
def agregar_simbolo():
    """Procesa el ingreso de un único símbolo a la pila."""
    inicializar_sesion()
    
    # Obtenemos y limpiamos el símbolo recibido
    simbolo = request.form.get("simbolo", "").strip()
    
    if not simbolo:
        return redirect(url_for("index"))

    pila_actual = session["pila"]    
    aperturas = PAREJAS.values()  # {'(', '[', '{'}
    cierres = PAREJAS.keys()      # {')', ']', '}'

    # CASO 1: Símbolo de apertura -> Apilar
    if simbolo in aperturas:
        pila_actual.append(simbolo)
        session["mensaje_estado"] = f"Se insertó '{simbolo}' en el tope de la pila."
        session["tipo_estado"] = "info"

    # CASO 2: Símbolo de cierre -> Validar y desapilar
    elif simbolo in cierres:
        # Subcaso 2.1: Pila vacía
        if len(pila_actual) == 0:
            session["mensaje_estado"] = f"Error: La pila está vacía, no se puede cerrar '{simbolo}'."
            session["tipo_estado"] = "error"
        
        # Subcaso 2.2: Coincide con el tope de la pila
        elif pila_actual[-1] == PAREJAS[simbolo]:
            elemento_tope = pila_actual.pop()
            session["mensaje_estado"] = f"Pareja válida: '{elemento_tope}' emparejado con '{simbolo}'."
            session["tipo_estado"] = "success"
        
        # Subcaso 2.3: No coincide con el tope
        else:
            elemento_tope = pila_actual[-1]
            session["mensaje_estado"] = f"Error de correspondencia: Se esperaba el cierre de '{elemento_tope}', no '{simbolo}'."
            session["tipo_estado"] = "error"

    # CASO 3: Carácter no válido
    else:
        session["mensaje_estado"] = f"'{simbolo}' no es un símbolo de agrupación válido."
        session["tipo_estado"] = "error"

    # Notificar a Flask que la sesión fue modificada
    session["pila"] = pila_actual

    return redirect(url_for("index"))


@app.route("/finalizar", methods=["POST"])
def finalizar_evaluacion():
    """Equivalente a presionar 'x': Verifica si la pila quedó vacía."""
    inicializar_sesion()
    pila_actual = session["pila"]

    if len(pila_actual) == 0:
        session["mensaje_estado"] = "La pila está vacía."
        session["tipo_estado"] = "success"
    else:
        elementos_pendientes = " ".join(pila_actual)
        session["mensaje_estado"] = f"Error final: La pila no quedó vacía. Símbolos sin cerrar: \n {elementos_pendientes}"
        session["tipo_estado"] = "error"

    return redirect(url_for("index"))


@app.route("/reiniciar", methods=["POST"])
def reiniciar_pila():
    """Limpia la pila para empezar una nueva prueba."""
    session["pila"] = []
    session["mensaje_estado"] = "La pila ha sido reiniciada."
    session["tipo_estado"] = "info"
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True, port=5000)