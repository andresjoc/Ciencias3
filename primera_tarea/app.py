"""
Servidor Flask para el ejercicio de Colas de Prioridad:
Planificación de Tareas en Procesadores (El Trabajo Más Corto Primero / SPT / SJF)
con soporte para Hora de Llegada (r_i).
"""

import heapq
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "clave_colas_sjf"

# Paleta de colores para las tareas en el Gantt visual
COLORES_TAREAS = [
    "#3b82f6",  # azul
    "#10b981",  # verde esmeralda
    "#f59e0b",  # ámbar
    "#8b5cf6",  # violeta
    "#ec4899",  # rosa
    "#06b6d4",  # cian
    "#f97316",  # naranja
    "#14b8a6",  # teal
    "#6366f1",  # índigo
    "#84cc16",  # lima
]


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
        session["mensaje_colas"] = "Dé de alta las tareas (indicando hora de llegada y duración) o cargue un ejemplo para comenzar."
    if "tipo_colas" not in session:
        session["tipo_colas"] = "info"


@app.route("/")
@app.route("/colas")
def index():
    """Ruta principal: Muestra la interfaz gráfica de Colas de Prioridad (SJF/SPT)."""
    inicializar_sesion_colas()

    tareas = session.get("tareas", [])
    num_procesadores = session.get("num_procesadores", 2)
    resultado = session.get("resultado_colas", None)
    mensaje_estado = session.get("mensaje_colas", "")
    tipo_estado = session.get("tipo_colas", "info")

    # Asegurar que todas las tareas tengan el campo 'llegada'
    for t in tareas:
        if "llegada" not in t:
            t["llegada"] = 0

    total_tareas = len(tareas)
    tiempo_total = sum(t["tiempo"] for t in tareas)
    
    # Cola ordenada según llegada y luego prioridad (menor ti primero)
    cola_prioridad = sorted(tareas, key=lambda x: (x["llegada"], x["tiempo"], x["id"]))

    return render_template(
        "colas.html",
        tareas=tareas,
        cola_prioridad=cola_prioridad,
        total_tareas=total_tareas,
        tiempo_total=tiempo_total,
        num_procesadores=num_procesadores,
        resultado=resultado,
        mensaje_estado=mensaje_estado,
        tipo_estado=tipo_estado,
        colores=COLORES_TAREAS
    )


@app.route("/colas/alta", methods=["POST"])
def colas_dar_de_alta():
    """Da de alta una nueva tarea (nombre, hora de llegada ri, y duración ti) en la cola."""
    inicializar_sesion_colas()

    nombre = request.form.get("nombre", "").strip()
    llegada_raw = request.form.get("llegada", "0").strip()
    tiempo_raw = request.form.get("tiempo", "").strip()

    # Validar hora de llegada
    try:
        llegada = float(llegada_raw) if llegada_raw else 0.0
        if llegada < 0:
            raise ValueError
        if llegada == int(llegada):
            llegada = int(llegada)
    except (ValueError, TypeError):
        session["mensaje_colas"] = f"Error: '{llegada_raw}' no es una hora de llegada válida. Debe ser mayor o igual a 0."
        session["tipo_colas"] = "error"
        return redirect(url_for("index"))

    # Validar duración
    try:
        tiempo = float(tiempo_raw)
        if tiempo <= 0:
            raise ValueError
        if tiempo == int(tiempo):
            tiempo = int(tiempo)
    except (ValueError, TypeError):
        session["mensaje_colas"] = f"Error: '{tiempo_raw}' no es una duración (ti) válida. Ingrese un número mayor que 0."
        session["tipo_colas"] = "error"
        return redirect(url_for("index"))

    if not nombre:
        nombre = f"T{session['siguiente_id']}"

    tareas = session["tareas"]
    tareas.append({
        "id": session["siguiente_id"],
        "nombre": nombre,
        "llegada": llegada,
        "tiempo": tiempo
    })
    session["siguiente_id"] += 1
    session["tareas"] = tareas
    session["resultado_colas"] = None
    session["mensaje_colas"] = f"Tarea '{nombre}' (Llegada: {llegada}, Duración: {tiempo}) agregada a la cola."
    session["tipo_colas"] = "success"

    return redirect(url_for("index"))


@app.route("/colas/ejemplo", methods=["POST"])
def colas_cargar_ejemplo():
    """Carga un conjunto de tareas de ejemplo con horas de llegada variadas."""
    inicializar_sesion_colas()

    tareas_ejemplo = [
        {"id": 1, "nombre": "T1", "llegada": 0, "tiempo": 3},
        {"id": 2, "nombre": "T2", "llegada": 1, "tiempo": 5},
        {"id": 3, "nombre": "T3", "llegada": 2, "tiempo": 2},
        {"id": 4, "nombre": "T4", "llegada": 3, "tiempo": 1},
        {"id": 5, "nombre": "T5", "llegada": 4, "tiempo": 4},
        {"id": 6, "nombre": "T6", "llegada": 5, "tiempo": 2},
    ]
    session["tareas"] = tareas_ejemplo
    session["siguiente_id"] = 7
    session["num_procesadores"] = 2
    session["resultado_colas"] = None
    session["mensaje_colas"] = "Ejemplo cargado con 6 tareas (con horas de llegada ri) y 2 procesadores. Presione 'Calcular Planificación'."
    session["tipo_colas"] = "info"

    return redirect(url_for("index"))


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

    return redirect(url_for("index"))


@app.route("/colas/procesadores", methods=["POST"])
def colas_configurar_procesadores():
    """Configura el número de procesadores disponibles para la planificación."""
    inicializar_sesion_colas()

    valor = request.form.get("num_procesadores", "")
    try:
        num = int(valor)
        if num < 1 or num > 10:
            raise ValueError
    except (ValueError, TypeError):
        session["mensaje_colas"] = "Error: el número de procesadores debe ser un entero entre 1 y 10."
        session["tipo_colas"] = "error"
        return redirect(url_for("index"))

    session["num_procesadores"] = num
    session["resultado_colas"] = None
    session["mensaje_colas"] = f"Configuración actualizada: {num} procesador(es) activos."
    session["tipo_colas"] = "info"

    return redirect(url_for("index"))


@app.route("/colas/procesar", methods=["POST"])
def colas_procesar():
    """
    Calcula la planificación con el algoritmo SJF (Shortest Job First)
    considerando Horas de Llegada (ri):
    - Las tareas se liberan en el instante de tiempo ri.
    - La cola de listos (Min-Heap) contiene las tareas que ya han llegado en el instante actual,
      ordenadas por su menor duración ti.
    - Se asigna cada tarea al procesador que primero queda libre.
    """
    inicializar_sesion_colas()

    tareas = session["tareas"]
    num_procesadores = session["num_procesadores"]

    if not tareas:
        session["mensaje_colas"] = "No hay tareas en la cola para procesar. Agregue tareas o cargue el ejemplo."
        session["tipo_colas"] = "error"
        return redirect(url_for("index"))

    # Ordenar tareas por hora de llegada inicial
    tareas_pendientes = sorted(tareas, key=lambda x: (x.get("llegada", 0), x["tiempo"], x["id"]))

    # Cola de procesadores: (tiempo_disponible, proc_id)
    cola_procesadores = [(0, proc_id) for proc_id in range(1, num_procesadores + 1)]
    heapq.heapify(cola_procesadores)

    # Cola de listos (Ready queue): Min-Heap por (duracion, llegada, id, nombre)
    cola_listos = []
    idx_llegadas = 0
    n_tareas = len(tareas_pendientes)

    procesadores = {proc_id: [] for proc_id in range(1, num_procesadores + 1)}
    orden_ejecucion = []
    tiempos_finalizacion = []
    tiempos_espera = []
    tiempos_retorno = []
    pasos = []
    paso_idx = 1

    # Asignación de colores
    color_map = {}
    for i, t in enumerate(tareas_pendientes):
        color_map[t["nombre"]] = COLORES_TAREAS[i % len(COLORES_TAREAS)]

    while idx_llegadas < n_tareas or cola_listos:
        # Extraer el procesador que antes queda disponible
        t_disp, proc_id = heapq.heappop(cola_procesadores)

        # Encolar en 'listos' todas las tareas que ya hayan llegado en t <= t_disp
        while idx_llegadas < n_tareas and tareas_pendientes[idx_llegadas].get("llegada", 0) <= t_disp:
            t_curr = tareas_pendientes[idx_llegadas]
            heapq.heappush(cola_listos, (t_curr["tiempo"], t_curr.get("llegada", 0), t_curr["id"], t_curr["nombre"]))
            idx_llegadas += 1

        if not cola_listos:
            # Si no hay tareas listas aún, el tiempo salta a la llegada de la próxima tarea
            if idx_llegadas < n_tareas:
                t_siguiente = tareas_pendientes[idx_llegadas].get("llegada", 0)
                t_disp = max(t_disp, t_siguiente)
                while idx_llegadas < n_tareas and tareas_pendientes[idx_llegadas].get("llegada", 0) <= t_disp:
                    t_curr = tareas_pendientes[idx_llegadas]
                    heapq.heappush(cola_listos, (t_curr["tiempo"], t_curr.get("llegada", 0), t_curr["id"], t_curr["nombre"]))
                    idx_llegadas += 1

        if not cola_listos:
            heapq.heappush(cola_procesadores, (t_disp, proc_id))
            break

        # Extraer la tarea de menor duración de la cola de listos (SJF)
        tiempo_tarea, llegada_tarea, tarea_id, nombre_tarea = heapq.heappop(cola_listos)

        inicio = max(t_disp, llegada_tarea)
        fin = inicio + tiempo_tarea
        espera = inicio - llegada_tarea
        retorno = fin - llegada_tarea

        tarea_info = {
            "id": tarea_id,
            "nombre": nombre_tarea,
            "llegada": llegada_tarea,
            "tiempo": tiempo_tarea,
            "inicio": inicio,
            "fin": fin,
            "espera": espera,
            "retorno": retorno,
            "color": color_map.get(nombre_tarea, "#3b82f6")
        }

        procesadores[proc_id].append(tarea_info)
        heapq.heappush(cola_procesadores, (fin, proc_id))

        orden_ejecucion.append(nombre_tarea)
        tiempos_finalizacion.append(fin)
        tiempos_espera.append(espera)
        tiempos_retorno.append(retorno)

        pasos.append({
            "paso": paso_idx,
            "tarea": nombre_tarea,
            "llegada": llegada_tarea,
            "tiempo": tiempo_tarea,
            "procesador": proc_id,
            "inicio": inicio,
            "fin": fin,
            "espera": espera,
            "retorno": retorno,
            "color": color_map.get(nombre_tarea, "#3b82f6")
        })
        paso_idx += 1

    # Métricas de optimización
    promedio_finalizacion = sum(tiempos_finalizacion) / len(tiempos_finalizacion) if tiempos_finalizacion else 0
    promedio_espera = sum(tiempos_espera) / len(tiempos_espera) if tiempos_espera else 0
    promedio_retorno = sum(tiempos_retorno) / len(tiempos_retorno) if tiempos_retorno else 0
    makespan = max((t["fin"] for p in procesadores.values() for t in p), default=0)

    # Calcular posiciones y anchos porcentuales para el Gantt
    for proc_id, lista in procesadores.items():
        for t in lista:
            if makespan > 0:
                t["pct_start"] = round((t["inicio"] / makespan) * 100, 2)
                t["pct_width"] = round((t["tiempo"] / makespan) * 100, 2)
            else:
                t["pct_start"] = 0
                t["pct_width"] = 0

    # Marcas de tiempo para el eje horizontal del Gantt
    marcas_tiempo = list(range(0, int(makespan) + 1, max(1, int(makespan) // 8 or 1)))
    if int(makespan) not in marcas_tiempo:
        marcas_tiempo.append(int(makespan))

    session["resultado_colas"] = {
        "procesadores": procesadores,
        "orden": orden_ejecucion,
        "promedio": round(promedio_finalizacion, 2),
        "promedio_espera": round(promedio_espera, 2),
        "promedio_retorno": round(promedio_retorno, 2),
        "makespan": makespan,
        "suma_tiempos": sum(tiempos_finalizacion),
        "pasos": pasos,
        "marcas_tiempo": marcas_tiempo
    }

    session["mensaje_colas"] = (
        f"Planificación SJF calculada correctamente. Tiempo total de ejecución (Makespan): {makespan} unidades."
    )
    session["tipo_colas"] = "success"

    return redirect(url_for("index"))


@app.route("/colas/salir", methods=["POST"])
def colas_salir():
    """Vacía la cola de tareas y reinicia los resultados."""
    session["tareas"] = []
    session["siguiente_id"] = 1
    session["resultado_colas"] = None
    session["mensaje_colas"] = "Cola vaciada y sesión reiniciada."
    session["tipo_colas"] = "info"

    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True, port=5000)
