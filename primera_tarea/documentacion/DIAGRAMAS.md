# Diagramas del Sistema - Ciencias de la Computación 3 (Tarea 1)

Este documento contiene los diagramas UML que describen la arquitectura y los flujos de ejecución de la aplicación.

---

## 1. Diagrama de Componentes (UML)

Muestra los componentes principales de la aplicación Flask, su interacción mediante HTTP y la gestión del estado en sesión:

![Diagrama de Componentes](diagrama_componentes.png)

---

## 2. Diagrama de Actividades - Planificación de Colas (UML)

Describe el flujo desde la interacción del usuario hasta el algoritmo de asignación óptima de tareas a procesadores (regla SPT con colas de prioridad `heapq`):

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
