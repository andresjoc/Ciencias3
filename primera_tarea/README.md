# Manual de Instalación y Ejecución

## TDA Pila - Simulación de Equilibrado de Símbolos

Este proyecto es una aplicación web basada en **Python y Flask** para visualizar y simular el funcionamiento de una Pila en la verificación de balanceo de paréntesis, corchetes y llaves.

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
