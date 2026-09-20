"""Script de compilación automatizada para generar el binario standalone (.exe).

Empaqueta la aplicación completa bajo la arquitectura MVC usando PyInstaller:
- Modo archivo único (--onefile)
- Modo ventana gráfica sin consola negra (--windowed)
- Inclusión de rutas y módulos en español (src/model, src/view, src/controller)
"""

from __future__ import annotations
import os
import sys
import subprocess


def compilar() -> int:
    """Ejecuta PyInstaller con todos los parámetros requeridos para empaquetar la aplicación."""
    directorio_raiz = os.path.dirname(os.path.abspath(__file__))
    archivo_principal = os.path.join(directorio_raiz, "src", "main.py")
    nombre_ejecutable = "SimulaAutomata"

    print("=" * 70)
    print(f"Iniciando compilación de {nombre_ejecutable} (.exe standalone)...")
    print(f"Directorio raíz: {directorio_raiz}")
    print(f"Punto de entrada: {archivo_principal}")
    print("=" * 70)

    # Argumentos de PyInstaller
    argumentos = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--windowed",
        f"--name={nombre_ejecutable}",
        f"--paths={directorio_raiz}",
        archivo_principal,
    ]

    print("Comando de compilación:")
    print(" ".join(argumentos))
    print("-" * 70)

    resultado = subprocess.run(argumentos, cwd=directorio_raiz)

    if resultado.returncode == 0:
        ruta_salida = os.path.join(directorio_raiz, "dist", f"{nombre_ejecutable}.exe")
        tamano_mb = os.path.getsize(ruta_salida) / (1024 * 1024) if os.path.exists(ruta_salida) else 0
        print("=" * 70)
        print("¡Compilación finalizada con ÉXITO!")
        print(f"Ejecutable generado en: {ruta_salida}")
        print(f"Tamaño del binario: {tamano_mb:.2f} MB")
        print("=" * 70)
    else:
        print("=" * 70)
        print(f"ERROR: La compilación falló con código de salida {resultado.returncode}.")
        print("=" * 70)

    return resultado.returncode


if __name__ == "__main__":
    sys.exit(compilar())
