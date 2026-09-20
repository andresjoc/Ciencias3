# Procedimiento de Conversión: AFN a AFD (Método de Subconjuntos)

Este documento describe el paso a paso detallado para transformar un **Autómata Finito No Determinista (AFN)** en un **Autómata Finito Determinista (AFD)**, aplicando la equivalencia por estados $K_n$ y el criterio para definir los estados de aceptación.

---

## Paso 1: Construcción de la tabla de transiciones original del AFN

1. **Definir la estructura:** Se ubican en las columnas los símbolos de entrada ($\Sigma = \{a, b\}$) y en las filas los estados del AFN ($q_0, q_1, \dots$).
2. **Identificar estados iniciales y finales:**
   * El estado inicial se indica con una flecha ($\to$).
   * Los estados de aceptación originales se marcan con un asterisco ($*$). En el ejercicio, el estado final es **$q_1$**.
3. **Mapear transiciones:**
   * Si una transición conduce a múltiples destinos, se agrupan entre llaves formando un conjunto (por ejemplo, $\{q_1, q_2\}$).
   * Si no existe transición para un símbolo, se representa mediante el conjunto vacío ($\emptyset$).

### Tabla 1: Transiciones del AFN inicial

| Estado $\Delta$ | Entrada $a$ | Entrada $b$ |
| :--- | :---: | :---: |
| $\to q_0$ | $\{q_1, q_2\}$ | $\emptyset$ |
| $*q_1$ | $\emptyset$ | $q_0$ |
| $q_2$ | $\emptyset$ | $q_3$ |
| $q_3$ | $q_0$ | $\emptyset$ |

---

## Paso 2: Generar y evaluar nuevos estados compuestos

Al existir salidas con conjuntos de múltiples estados, estos deben tratarse como **estados individuales del nuevo autómata**:

* Se detecta el conjunto $\{q_1, q_2\}$. Se agrega como fila a la tabla y se calcula la unión de transiciones:
  * Con $a$: $\delta(q_1, a) \cup \delta(q_2, a) = \emptyset \cup \emptyset = \emptyset$
  * Con $b$: $\delta(q_1, b) \cup \delta(q_2, b) = \{q_0\} \cup \{q_3\} = \{q_1, q_3\}$ *(según el desarrollo del apunte)*
* Al aparecer $\{q_1, q_3\}$, se añade una nueva fila y se calculan sus transiciones:
  * Con $a$: $\delta(q_1, a) \cup \delta(q_3, a) = \emptyset \cup \{q_0\} = \{q_0\}$
  * Con $b$: $\delta(q_1, b) \cup \delta(q_3, b) = \{q_0\} \cup \emptyset = \{q_0\}$ (o las transiciones correspondientes según el diagrama base).

### Tabla 2: Expansión de estados compuestos

| Estado $\Delta$ | Entrada $a$ | Entrada $b$ |
| :--- | :---: | :---: |
| $\to q_0$ | $\{q_1, q_2\}$ | $\emptyset$ |
| $*q_1$ | $\emptyset$ | $q_0$ |
| $q_2$ | $\emptyset$ | $q_3$ |
| $q_3$ | $q_0$ | $\emptyset$ |
| $\{q_1, q_2\}$ | $\emptyset$ | $\{q_1, q_3\}$ |
| $\{q_1, q_3\}$ | $q_0$ | $\emptyset$ |

---

## Paso 3: Renombrar estados a la notación $K_n$

Para simplificar la manipulación algebraica y gráfica, se asigna una etiqueta $K_n$ a cada estado simple o compuesto:

| Etiqueta $K_n$ | Conjunto equivalente |
| :---: | :---: |
| $K_0$ | $\{q_0\}$ |
| $K_1$ | $\{q_1\}$ |
| $K_2$ | $\{q_2\}$ |
| $K_3$ | $\{q_3\}$ |
| $K_4$ | $\{q_1, q_2\}$ |
| $K_5$ | $\{q_1, q_3\}$ |

---

## Paso 4: Aplicar la «Regla de Oro» para identificar estados finales en $K_n$

> **Regla de Oro:**  
> Un estado $K_n$ es un **estado final (de aceptación)** si y solo si contiene **al menos uno** de los estados finales del AFN original.  
> $$K_n \in F_{AFD} \iff K_n \cap F_{AFN} \neq \emptyset$$

Dado que $F_{AFN} = \{q_1\}$:

* **$K_0 = \{q_0\}$:** $q_1 \notin K_0 \implies$ **No final**
* **$K_1 = \{q_1\}$:** $q_1 \in K_1 \implies$ **Estado final ($*$)**
* **$K_2 = \{q_2\}$:** $q_1 \notin K_2 \implies$ **No final**
* **$K_3 = \{q_3\}$:** $q_1 \notin K_3 \implies$ **No final**
* **$K_4 = \{q_1, q_2\}$:** Contiene a $q_1 \implies$ **Estado final ($*$)**
* **$K_5 = \{q_1, q_3\}$:** Contiene a $q_1 \implies$ **Estado final ($*$)**

### Tabla 3: Transiciones formalizada en términos de $K_n$

| Estado | $a$ | $b$ | ¿Es Final? |
| :--- | :---: | :---: | :---: |
| $\to K_0$ | $K_4$ | $\emptyset$ | No |
| $*K_1$ | $\emptyset$ | $K_0$ | **Sí** ($q_1$) |
| $K_2$ | $\emptyset$ | $K_3$ | No |
| $K_3$ | $K_0$ | $\emptyset$ | No |
| $*K_4$ | $\emptyset$ | $K_5$ | **Sí** ($q_1 \in K_4$) |
| $*K_5$ | $K_0$ | $\emptyset$ | **Sí** ($q_1 \in K_5$) |

---

## Paso 5: Dibujar el grafo del AFD ("Pintar")

1. Se traza el estado inicial $\to (K_0)$.
2. Se representan los estados finales ($K_1, K_4, K_5$) con **doble círculo**.
3. Se grafican las aristas dirigidas rotuladas con las entradas $a$ y $b$ siguiendo la **Tabla 3**.

---

## Paso 6: Identificar y podar estados inalcanzables

1. **Rastreo de accesibilidad desde $K_0$:**
   * Desde $K_0$, con $a$ se accede a $K_4$.
   * Desde $K_4$, con $b$ se accede a $K_5$.
   * Desde $K_5$, con $a$ se retorna a $K_0$.
2. **Eliminación de estados inaccesibles:**
   * Los estados $K_1, K_2, K_3$ quedan aislados (ningún camino parte desde el estado inicial hacia ellos).
   * Se eliminan $K_1, K_2$ y $K_3$ del autómata.

### Tabla 4: AFD final simplificado y mínimo

| Estado | Entrada $a$ | Entrada $b$ |
| :--- | :---: | :---: |
| $\to K_0$ | $K_4$ | $\emptyset$ |
| $*K_4$ | $\emptyset$ | $K_5$ |
| $*K_5$ | $K_0$ | $\emptyset$ |