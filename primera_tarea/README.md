# Manual de Instalación y Ejecución

Aplicación web en **Python y Flask** para la **Planificación de Tareas en Procesadores con Colas de Prioridad** (Algoritmo *El trabajo más corto primero* / *Shortest Job First - SJF / SPT*).

Dado un conjunto de \(n\) tareas (cada una con un tiempo \(t_i\)) y \(m\) procesadores, calcula y visualiza el orden de ejecución óptimo que **minimiza el tiempo medio de finalización**, utilizando colas de prioridad (*Min-Heaps* con `heapq`) y un **Diagrama de Gantt interactivo**. Ruta principal: `/`.

---

### 1. Requisitos Previos

- **Python 3.8 o superior** instalado en el sistema ([python.org](https://www.python.org/)).
- **pip** (gestor de paquetes de Python, incluido por defecto con Python).

---

### 2. Pasos de Instalación

#### Paso 1: Abrir la terminal o línea de comandos

Navega hasta la carpeta raíz del proyecto:

```bash
cd "primera_tarea"
```

#### Paso 2 (Opcional pero recomendado): Crear y activar un entorno virtual

- **En Windows:**

  ```powershell
  python -m venv venv
  .\venv\Scripts\activate
  ```

- **En Linux / macOS:**
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

#### Paso 3: Instalar dependencias

Ejecuta el siguiente comando para instalar Flask:

```bash
pip install -r requirements.txt
```

---

### 3. Ejecución del Sistema

Ejecuta el archivo principal:

```bash
python app.py
```

Una vez ejecutado, verás en la consola un mensaje similar a:

```
* Running on http://127.0.0.1:5000
```

---

### 4. Acceso a la Aplicación

Abre tu navegador web e ingresa a:
👉 [http://localhost:5000](http://localhost:5000) o [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## 🏛️ Arquitectura y Diagramas del Sistema

### 1. Diagrama de Componentes (UML)

Estructura modular de la aplicación web y separación de responsabilidades:

![Diagrama de Componentes](documentacion/diagrama_componentes.png)

---

### 2. Diagrama de Actividades - Colas y Planificación SPT (UML)

Flujo completo desde la interacción del usuario hasta la ejecución del algoritmo de asignación óptima con colas de prioridad (`heapq`):

```mermaid
flowchart TD
    Start((● Inicio)) --> A[Usuario accede a la vista /colas]

    subgraph Interaccion ["1. Interacción del Usuario"]
        A --> B[Configurar número de procesadores N]
        B --> C[Dar de alta tareas ingresando nombre y tiempo ti]
        C --> D[Presionar botón 'Calcular Planificación']
    end

    subgraph Controlador ["2. Validación del Sistema"]
        D --> Valida{¿Hay tareas registradas en cola?}
        Valida -->|No| Err[Mostrar advertencia: 'Cola vacía']
        Err --> C
    end

    subgraph AlgoritmoSPT ["3. Lógica Central de Asignación (Colas de Prioridad)"]
        Valida -->|Sí| H1[Construir Cola de Prioridad de TAREAS ordenada por ti ascendente]
        H1 --> H2[Construir Cola de Prioridad de PROCESADORES ordenados por tiempo libre = 0]
        
        H2 --> Bucle{¿Quedan tareas en la cola?}

        Bucle -->|Sí| PopT["Extraer tarea más corta (tope de la cola de tareas)"]
        PopT --> PopP["Extraer procesador que se desocupa primero (tope de procesadores)"]
        
        PopP --> Asignar["Asignar tarea al procesador:<br>• inicio = tiempo_libre<br>• fin = inicio + ti"]
        Asignar --> PushP["Reinsertar procesador en la cola con su nuevo tiempo de liberación = fin"]
        PushP --> Registrar["Guardar tarea en cronograma y registrar tiempo fin"]
        Registrar --> Bucle

        Bucle -->|No| CalcProm["Calcular Tiempo Medio de Finalización:<br>Promedio = Suma(tiempos fin) / Total tareas"]
    end

    subgraph Salida ["4. Presentación de Resultados"]
        CalcProm --> Render[Renderizar cronograma por procesador y métrica promedio]
    end

    Render --> Fin(((◉ Fin)))
```

