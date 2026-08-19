"""
Servidor Flask para el TDA Pila interactivo (Paso a paso).
Mantiene el estado de la pila en la sesión del navegador.
"""

import heapq

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
        tipo_estado=session["tipo_estado"],
        active_page="pila"
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


# =====================================================================
# EJERCICIO 2: COLAS - PLANIFICACIÓN DE TAREAS EN PROCESADORES
# =====================================================================
# Enunciado: dado un conjunto de n tareas (cada una con un tiempo de
# ejecución ti) y varios procesadores, se busca un orden de ejecución
# que minimice el tiempo MEDIO de finalización de las tareas.
#
# Algoritmo utilizado (clásico de colas de prioridad):
#   1. Se construye una cola de prioridad de TAREAS ordenada por tiempo
#      ascendente (regla SPT: Shortest Processing Time First). Ejecutar
#      primero las tareas más cortas minimiza el tiempo medio de espera.
#   2. Se mantiene una cola de prioridad de PROCESADORES ordenada por el
#      instante en el que cada uno queda libre (todos inician en 0).
#   3. Se recorre la cola de tareas (de la más corta a la más larga) y,
#      para cada una, se asigna al procesador que antes queda libre
#      (tope de la cola de procesadores); su nuevo instante libre se
#      reinserta en la cola.
# SPT + "procesador más próximo a liberarse" es la solución óptima
# conocida para minimizar el tiempo medio de finalización con varios
# procesadores idénticos. Nota: el número de procesadores es
# configurable en la interfaz (el enunciado dice "n procesadores"; aquí
# se deja como parámetro para que el ejercicio no sea trivial cuando
# procesadores == tareas).

def inicializar_sesion_colas():
    """Inicializa las variables de estado del ejercicio de colas."""
    if "tareas" not in session:
        session["tareas"] = []
    if "siguiente_id" not in session:
        session["siguiente_id"] = 1
    if "num_procesadores" not in session:
        session["num_procesadores"] = 2
    if "resultado_colas" not in session:
        session["resultado_colas"] = None
    if "mensaje_colas" not in session:
        session["mensaje_colas"] = "Dé de alta las tareas (con su tiempo ti) para comenzar."
    if "tipo_colas" not in session:
        session["tipo_colas"] = "info"


@app.route("/colas")
def colas():
    """Ruta principal del ejercicio de colas: planificación de tareas."""
    inicializar_sesion_colas()
    return render_template(
        "colas.html",
        tareas=session["tareas"],
        num_procesadores=session["num_procesadores"],
        resultado=session["resultado_colas"],
        mensaje_estado=session["mensaje_colas"],
        tipo_estado=session["tipo_colas"],
        active_page="colas"
    )


@app.route("/colas/alta", methods=["POST"])
def colas_dar_de_alta():
    """Da de alta una nueva tarea (nombre + tiempo de ejecución ti) en la cola."""
    inicializar_sesion_colas()

    nombre = request.form.get("nombre", "").strip()
    tiempo_raw = request.form.get("tiempo", "").strip()

    # Validamos que el tiempo sea un número positivo
    try:
        tiempo = float(tiempo_raw)
        if tiempo <= 0:
            raise ValueError
        if tiempo == int(tiempo):  # lo mostramos sin decimales si es entero
            tiempo = int(tiempo)
    except (ValueError, TypeError):
        session["mensaje_colas"] = f"Error: '{tiempo_raw}' no es un tiempo (ti) válido. Debe ser un número mayor que 0."
        session["tipo_colas"] = "error"
        return redirect(url_for("colas"))

    if not nombre:
        nombre = f"T{session['siguiente_id']}"

    tareas = session["tareas"]
    tareas.append({
        "id": session["siguiente_id"],
        "nombre": nombre,
        "tiempo": tiempo
    })
    session["siguiente_id"] += 1
    session["tareas"] = tareas
    session["resultado_colas"] = None  # una nueva alta invalida la planificación previa
    session["mensaje_colas"] = f"Tarea '{nombre}' (ti = {tiempo}) dada de alta correctamente."
    session["tipo_colas"] = "success"

    return redirect(url_for("colas"))


@app.route("/colas/eliminar", methods=["POST"])
def colas_eliminar():
    """Elimina una tarea de la cola a partir de su identificador."""
    inicializar_sesion_colas()

    id_tarea = request.form.get("id_tarea", "")
    tareas = session["tareas"]
    tarea_eliminada = next((t for t in tareas if str(t["id"]) == id_tarea), None)

    if tarea_eliminada is None:
        session["mensaje_colas"] = "Error: la tarea seleccionada ya no existe."
        session["tipo_colas"] = "error"
    else:
        tareas = [t for t in tareas if str(t["id"]) != id_tarea]
        session["tareas"] = tareas
        session["resultado_colas"] = None
        session["mensaje_colas"] = f"Tarea '{tarea_eliminada['nombre']}' eliminada de la cola."
        session["tipo_colas"] = "success"

    return redirect(url_for("colas"))


@app.route("/colas/mostrar", methods=["POST"])
def colas_mostrar():
    """Muestra un resumen del estado actual de la cola de tareas pendientes."""
    inicializar_sesion_colas()

    tareas = session["tareas"]
    if not tareas:
        session["mensaje_colas"] = "La cola de tareas está vacía."
    else:
        tiempo_total = sum(t["tiempo"] for t in tareas)
        session["mensaje_colas"] = (
            f"Hay {len(tareas)} tarea(s) en cola, con un tiempo total de {tiempo_total} unidades."
        )
    session["tipo_colas"] = "info"

    return redirect(url_for("colas"))


@app.route("/colas/procesadores", methods=["POST"])
def colas_configurar_procesadores():
    """Configura el número de procesadores disponibles para la planificación."""
    inicializar_sesion_colas()

    valor = request.form.get("num_procesadores", "")
    try:
        num = int(valor)
        if num < 1:
            raise ValueError
    except (ValueError, TypeError):
        session["mensaje_colas"] = "Error: el número de procesadores debe ser un entero mayor o igual a 1."
        session["tipo_colas"] = "error"
        return redirect(url_for("colas"))

    session["num_procesadores"] = num
    session["resultado_colas"] = None
    session["mensaje_colas"] = f"Número de procesadores actualizado a {num}."
    session["tipo_colas"] = "info"

    return redirect(url_for("colas"))


@app.route("/colas/procesar", methods=["POST"])
def colas_procesar():
    """
    Calcula la planificación: recorre la cola de prioridad de tareas
    (ordenadas por ti ascendente) y las asigna, una a una, al procesador
    que antes queda libre, para minimizar el tiempo medio de finalización.
    """
    inicializar_sesion_colas()

    tareas = session["tareas"]
    num_procesadores = session["num_procesadores"]

    if not tareas:
        session["mensaje_colas"] = "No hay tareas en la cola para procesar."
        session["tipo_colas"] = "error"
        return redirect(url_for("colas"))

    # 1. Cola de prioridad de tareas: la tarea más corta siempre primero (SPT)
    cola_tareas = [(t["tiempo"], t["id"], t["nombre"]) for t in tareas]
    heapq.heapify(cola_tareas)

    # 2. Cola de prioridad de procesadores: el que antes queda libre, primero
    cola_procesadores = [(0, proc_id) for proc_id in range(1, num_procesadores + 1)]
    heapq.heapify(cola_procesadores)

    procesadores = {proc_id: [] for proc_id in range(1, num_procesadores + 1)}
    orden_ejecucion = []
    tiempos_finalizacion = []

    while cola_tareas:
        tiempo_tarea, _, nombre_tarea = heapq.heappop(cola_tareas)
        disponible_en, proc_id = heapq.heappop(cola_procesadores)

        inicio = disponible_en
        fin = inicio + tiempo_tarea

        procesadores[proc_id].append({
            "nombre": nombre_tarea,
            "tiempo": tiempo_tarea,
            "inicio": inicio,
            "fin": fin
        })
        heapq.heappush(cola_procesadores, (fin, proc_id))

        orden_ejecucion.append(nombre_tarea)
        tiempos_finalizacion.append(fin)

    promedio = sum(tiempos_finalizacion) / len(tiempos_finalizacion)

    session["resultado_colas"] = {
        "procesadores": procesadores,
        "orden": orden_ejecucion,
        "promedio": round(promedio, 2)
    }
    session["mensaje_colas"] = (
        f"Planificación calculada. Tiempo medio de finalización: {round(promedio, 2)} unidades."
    )
    session["tipo_colas"] = "success"

    return redirect(url_for("colas"))


@app.route("/colas/salir", methods=["POST"])
def colas_salir():
    """Opción 'Salir' del menú: limpia la cola y finaliza la sesión de trabajo."""
    session["tareas"] = []
    session["siguiente_id"] = 1
    session["resultado_colas"] = None
    session["mensaje_colas"] = "Sesión finalizada. La cola de tareas se ha vaciado."
    session["tipo_colas"] = "info"

    return redirect(url_for("colas"))


if __name__ == "__main__":
    app.run(debug=True, port=5000)