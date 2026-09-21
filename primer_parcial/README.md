# SimulaAutomata — Editor Visual Interactivo y Simulador de Autómatas (DFA / NFA)

**SimulaAutomata** es una aplicación de escritorio interactiva desarrollada en Python y PyQt6 bajo una arquitectura estricta **Modelo-Vista-Controlador (MVC)**. Permite **dibujar, pintar, arrastrar y conectar visualmente estados de autómatas** en un lienzo con cuadrícula estilo Draw.io / Figma, editarlos mediante una matriz de transiciones sincronizada en tiempo real, transformar de DFA a NFA y simular paso a paso el procesamiento de cadenas con visualización de cinta y unidad de control.

---

## Características Principales

### 1. Editor Visual e Interactivo de Grafos (Estilo Draw.io / Figma)
- **Lienzo con cuadrícula punteada suave:** Área de trabajo amplia, moderna y clara.
- **Pintar y arrastrar estados (*Drag & Drop*):**
  - Clic en el lienzo para crear estados circulares donde desees con numeración automática ($q_0, q_1, \dots$).
  - Arrastre libre de los nodos con el ratón por todo el lienzo.
  - **Estado Inicial:** Flecha formal entrante desde la izquierda ($\to q_0$) con distintivo `inicio`.
  - **Estados de Aceptación:** Doble círculo concéntrico formal característico de la teoría de la computación.
  - **Menú contextual (Clic Derecho sobre el estado):** Marcar/desmarcar inicial, alternar aceptación, renombrar o eliminar.
- **Conectar flechas de transición:**
  - Clic en el nodo origen y arrastre hacia el nodo destino con línea elástica visible.
  - Al conectar, se solicita el símbolo de la transición (ej. `0, 1` o `a, b`).
  - **Bucles sobre sí mismo (*Self-loops*):** Si conectas un estado a sí mismo, se dibuja automáticamente un arco o lazo curvo superior elegante.
  - **Curvatura bidireccional:** Si existen transiciones en ambos sentidos ($q_0 \to q_1$ y $q_1 \to q_0$), las flechas se curvan suavemente para no solaparse jamás.
  - **Puntas de flecha triangulares orientadas matemáticamente:** Tangentes exactas a la llegada al perímetro del círculo.
  - **Etiquetas de símbolos:** Pequeña pastilla con fondo blanco y bordes redondeados centrada sobre la arista.
  - **Seguimiento en tiempo real:** Mientras arrastras un estado, todas las flechas conectadas se reorientan y siguen al nodo dinámicamente.
  - **Edición rápida:** Doble clic en cualquier flecha para modificar o añadir símbolos.

### 2. Sincronización Total Bidireccional (MVC)
- **Grafo $\leftrightarrow$ Matriz de Transiciones $\leftrightarrow$ Modelo Formal:**
  - Cualquier estado o transición dibujada en el grafo se refleja al instante en la tabla matricial y en el modelo.
  - Cualquier celda editada en la tabla matricial actualiza las flechas y nodos en el grafo interactivo.
- **Iluminación en Simulación:**
  - Al ejecutar una cadena paso a paso, el estado activo en cada momento se ilumina con brillo amarillo tanto en el grafo como en la cinta.

### 3. Motor de Simulación: Cinta y Unidad de Control
- **Nivel Superior (Cinta):** Tira horizontal contigua con los caracteres de la palabra de entrada $u$, agrupada por una llave horizontal superior $\{$, celda delimitadora de fin ($\equiv$) y extremo abierto con puntos suspensivos ($\dots$).
- **Nivel Inferior (Unidad de Control):** Cajas discretas de estado alineadas verticalmente bajo la cinta con flechas ascendentes ($\uparrow$).
- **Trazas Ramificadas (NFA):** Detección visual de ramas completas (aceptadas en verde $\checkmark$, rechazadas en rojo $\times$) y ramas abortadas prematuramente ante transiciones vacías o indefinidas ($\emptyset$).
- **Controles de Simulación:** Paso anterior, paso siguiente, ejecutar todo y reiniciar con estadísticas de ramas en tiempo real.

---

## Arquitectura del Proyecto (MVC)

Todo el código fuente, clases, variables, métodos y comentarios siguen una estricta convención **100% en español**:

```text
primer_parcial/
├── src/
│   ├── main.py                         # Punto de entrada principal y arranque de PyQt6
│   ├── model/                          # Capa Modelo (Lógica formal y matemática)
│   │   ├── __init__.py
│   │   ├── alfabeto.py                 # Definición formal del alfabeto Sigma y validaciones
│   │   ├── automata.py                 # Modelo formal DFA (5-tupla, validaciones, traza DFA)
│   │   └── automata_nfa.py             # Modelo formal NFA, traza ramificada y ramas abortadas
│   ├── view/                           # Capa Vista (Componentes gráficos PyQt6)
│   │   ├── __init__.py
│   │   ├── ventana_principal.py        # Ventana principal con Splitter (Grafo + Cinta/Tabla)
│   │   ├── items_grafo.py              # ItemNodoEstado e ItemAristaTransicion (Draw.io)
│   │   ├── lienzo_grafo.py             # Lienzo interactivo QGraphicsView con cuadrícula
│   │   ├── barra_herramientas_grafo.py # Barra de herramientas (Cursor, Crear, Conectar, Borrar)
│   │   ├── panel_alfabeto.py           # Interfaz para ingresar y modificar Sigma
│   │   ├── tabla_transiciones.py       # Matriz editable de transiciones y gestión de estados
│   │   ├── panel_simulacion.py         # Controles paso a paso e insignias de estado
│   │   └── lienzo_cinta.py             # Lienzo gráfico de cinta, llave superior y ramas
│   └── controller/                     # Capa Controlador (Coordinación y eventos)
│       ├── __init__.py
│       └── controlador_automata.py     # Enlace bidireccional Grafo <-> Tabla <-> Modelo
├── tests/                              # Batería de 64 pruebas automatizadas (pytest)
│   ├── test_automata.py                # Pruebas del modelo DFA y alfabeto
│   ├── test_controlador.py             # Pruebas de integración del controlador
│   ├── test_lienzo_grafo.py            # Pruebas del editor visual de grafos interactivo
│   ├── test_tabla_transiciones.py      # Pruebas de la tabla matricial de transiciones
│   ├── test_simulacion_traza.py        # Pruebas de la simulación paso a paso DFA
│   └── test_nfa.py                     # Pruebas de no-determinismo, ramas NFA y ∅
├── specs/                              # Especificaciones del proyecto
│   ├── mission.md
│   ├── tech-stack.md
│   └── roadmap.md
├── compilar_ejecutable.py              # Script Python para compilación con PyInstaller
├── compilar.ps1                        # Script PowerShell para compilación rápida
└── SimulaAutomata.spec                 # Archivo de especificación de PyInstaller
```

---

## Requisitos del Sistema

### Para Ejecutar desde el Código Fuente
- **Sistema Operativo:** Windows 10 / 11 (64-bit), Linux o macOS.
- **Python:** Versión 3.10 o superior (recomendado 3.11+).
- **Librerías Python necesarias:**
  ```bash
  pip install PyQt6 pytest pyinstaller
  ```

### Para Ejecutar el Binario Standalone (`.exe`)
- **Sistema Operativo:** Windows 10 o Windows 11 (64-bit).
- **Python / Librerías:** **NO SE REQUIERE** tener Python ni ninguna librería instalada en la máquina. El archivo `.exe` es completamente autónomo.

---

## Ejecución desde Código Fuente

1. **Abrir una terminal** en la carpeta raíz del proyecto:
   ```powershell
   cd "c:\Users\andre\Downloads\Decimo Semestre\Ciencias 3\primer_parcial"
   ```
2. **Instalar dependencias:**
   ```powershell
   pip install PyQt6 pytest pyinstaller
   ```
3. **Lanzar la aplicación:**
   ```powershell
   python src/main.py
   ```

---

## Ejecución de Pruebas Automatizadas

La suite incluye **64 pruebas unitarias e integrales** que cubren el modelo, el editor visual de grafos, las transiciones, el NFA y la simulación:

```powershell
pytest -v
```

Para ejecución resumida:
```powershell
pytest -q
```

---

## Compilación del Binario Standalone (`SimulaAutomata.exe`)

El ejecutable para Windows se compila con:
- `--onefile`: Todo el runtime de Python, PyQt6, Qt C++ y módulos del proyecto en un solo binario.
- `--windowed`: Modo ventana nativa sin consola negra de fondo.
- `--paths .`: Resolución garantizada de paquetes en español.

### Opción 1: Mediante Script de Python (Recomendado)
```powershell
python compilar_ejecutable.py
```

### Opción 2: Mediante Script de PowerShell
```powershell
.\compilar.ps1
```

### Opción 3: Comando Directo de PyInstaller
```powershell
python -m PyInstaller --noconfirm --clean --onefile --windowed --name SimulaAutomata --paths . src/main.py
```

El ejecutable compilado se generará en:
```text
dist\SimulaAutomata.exe
```

---

## Cómo Verificar la Ejecución en un Entorno Limpio (Sin Python)

1. **Copiar únicamente el ejecutable:**
   Tome el archivo `dist\SimulaAutomata.exe` y cópielo a cualquier otra carpeta, memoria USB o computadora con Windows que **no** tenga Python instalado.
2. **Ejecutar el archivo:**
   Haga doble clic en `SimulaAutomata.exe` o ejecútelo desde la consola:
   ```powershell
   .\dist\SimulaAutomata.exe
   ```
3. **Comprobación:**
   - La ventana abrirá de forma nativa e instantánea.
   - Podrá pintar estados, arrastrar nodos con el ratón, tirar flechas, editar la tabla y simular la cinta en tiempo real sin requerir Python.

---

## Guía de Uso del Editor de Grafos y Simulador

### 1. Barra de Herramientas del Grafo
- 🖱️ **Modo Cursor (Esc):** Permite hacer clic y arrastrar cualquier estado por el lienzo, seleccionar elementos o editar flechas.
- ✋ **Modo Desplazar:** Arrastre panorámico libre del lienzo en cualquier dirección con el botón izquierdo presionado.
- ➕ **Crear Estado:** Haga clic en cualquier lugar del lienzo para plantar un nuevo nodo formal ($q_0, q_1, \dots$). El primer estado creado se define automáticamente como estado inicial.
- ➔ **Conectar Flecha:** Conexión interactiva a dos clics: haga clic en el nodo origen y luego en el nodo destino (o sobre el mismo para bucles *self-loop*). Se abrirá un cuadro para seleccionar los caracteres del alfabeto.
- 🗑️ **Borrar (Supr / Backspace):** Haga clic en cualquier estado o flecha para eliminarlo inmediatamente.
- ↶ **Deshacer (Ctrl+Z) / ↷ Rehacer (Ctrl+Y / Ctrl+Shift+Z):** Historial completo para revertir o restaurar cualquier cambio (creaciones, eliminaciones, ediciones, auto-distribución o conversiones).
- 🔍+ / 🔍- / ⟲ 100%: Controles de zoom dedicados (también disponibles mediante la rueda del ratón en el editor).
- 🔄 **Auto-distribuir:** Reorganiza automáticamente todos los estados en una disposición circular armónica.
- 🧹 **Limpiar Grafo:** Borra todos los nodos, flechas e historial del lienzo para empezar de cero.
- ⚡ **Convertir AFN a AFD:** Se activa al detectar transiciones no deterministas para abrir el procedimiento formal docente.
- 📖 **¿Cómo usar el programa?:** Abre la guía interactiva completa en la pestaña derecha.

### 2. Clic Derecho sobre los Estados
- **Marcar como Inicial ($q_0$):** Agrega la flecha formal entrante $\to q$.
- **Estado de Aceptación ($F$):** Agrega el doble círculo concéntrico característico.
- **Renombrar Estado:** Permite cambiar el identificador del estado (ej. $q_0 \to s_0$).
- **Eliminar Estado:** Remueve el estado y todas sus flechas asociadas.

### 3. Clic y Doble Clic en Flechas
- **Doble clic en una flecha:** Permite editar los símbolos permitidos de la transición mediante un menú interactivo.
- **Clic derecho en una flecha:** Acceso directo a edición de caracteres o eliminación.

### 4. Simulación Paso a Paso en Cinta
- En la pestaña **"📼 Simulador de Cinta y Traza"**, escriba la cadena concreta $u \in \Sigma^*$ (ej. `0101`, `aab`) y presione **"Iniciar"**.
  > **Nota Teórica:** La cinta recibe palabras reales de entrada, **no** operadores de expresiones regulares como `*` (Kleene) o `+`.
- A medida que avanza con **"Siguiente ▶"**:
  - En la **Cinta** se resalta en amarillo la celda leída y se desplaza el cabezal lector ($\uparrow$).
  - En el **Grafo** el nodo activo correspondiente se ilumina en amarillo brillante en tiempo real.
  - Al llegar a la celda $\equiv$, se indica con insignia verde ($\checkmark$) si la palabra fue **Aceptada** o roja ($\times$) si fue **Rechazada**.
- En **AFN**, se visualizan ramas paralelas de computación, truncando con $\emptyset$ aquellas que alcanzan transiciones indefinidas.

### 5. Conversión Formal de AFN a AFD (Método Docente de Subconjuntos)
- Al hacer clic en **"⚡ Convertir AFN a AFD"**, se despliega el procedimiento en 6 pasos formales:
  1. **Paso 1:** Tabla 1 (AFN base con transiciones múltiples).
  2. **Paso 2:** Tabla 2 (Expansión de estados compuestos por unión $\delta(q_i, \sigma) \cup \delta(q_j, \sigma)$).
  3. **Paso 3:** Mapeo y renombramiento a notación formal $K_n$ ($K_0, K_1, \dots$).
  4. **Paso 4:** Criterio de aceptación para identificar estados finales y Tabla 3 Formalizada.
  5. **Paso 5:** Grafo completo de la Tabla 3 en visor estático con estados inalcanzables en **rojo** y navegación exclusiva por arrastre de mano.
  6. **Paso 6:** Análisis de accesibilidad (BFS desde $K_0$) y Tabla 4 Final Simplificada.
- **Aplicar al Editor:** Transfiere el AFD resultante al editor con distribución circular.
- **Pestaña Permanente:** Permite consultar el informe continuo en cualquier momento en la pestaña **"📐 Paso a Paso (AFN → AFD)"** ubicada contigua a la Matriz de Transiciones.

---

## Licencia y Créditos

Proyecto desarrollado para la asignatura **Ciencias de la Computación 3 (Lenguajes Formales y Autómatas)**, Décimo Semestre, Universidad del Quindío.
