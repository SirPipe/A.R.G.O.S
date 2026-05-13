from pathlib import Path
from datetime import datetime
import shutil
import subprocess

from system_tools import (
    resumen_estado_sistema,
    resumen_temperatura,
    obtener_temperatura
)


HOME = Path.home()
BASE_DIR = HOME / "ARGOS"
REPORTS_DIR = BASE_DIR / "reports"
BACKUPS_DIR = BASE_DIR / "backups"


def abrir_apps_trabajo():
    """
    Abre apps básicas de trabajo.
    Puedes personalizar esta lista después.
    """
    apps_abiertas = []
    apps_no_encontradas = []

    apps = [
        ("firefox", "Firefox"),
        ("code", "Visual Studio Code"),
        ("kgx", "Terminal"),
        ("gnome-terminal", "Terminal"),
        ("nautilus", "Archivos")
    ]

    terminal_abierta = False

    for comando, nombre in apps:
        if nombre == "Terminal" and terminal_abierta:
            continue

        if shutil.which(comando):
            try:
                subprocess.Popen([comando])
                apps_abiertas.append(nombre)

                if nombre == "Terminal":
                    terminal_abierta = True

            except Exception:
                apps_no_encontradas.append(nombre)

    if not apps_abiertas:
        return "No pude abrir apps de trabajo. No encontré las aplicaciones configuradas."

    abiertas = ", ".join(sorted(set(apps_abiertas)))

    if apps_no_encontradas:
        no_encontradas = ", ".join(sorted(set(apps_no_encontradas)))
        return f"Abrí estas apps de trabajo: {abiertas}. No pude abrir: {no_encontradas}."

    return f"Abrí tus apps de trabajo: {abiertas}."


def crear_reporte_sistema():
    """
    Crea un reporte de estado del sistema en ~/ARGOS/reports/
    """
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    fecha = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    archivo = REPORTS_DIR / f"reporte_sistema_{fecha}.txt"

    contenido = []
    contenido.append("REPORTE DEL SISTEMA - A.R.G.O.S.")
    contenido.append("=" * 40)
    contenido.append(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    contenido.append("")
    contenido.append(resumen_estado_sistema())
    contenido.append("")

    archivo.write_text("\n".join(contenido), encoding="utf-8")

    try:
        subprocess.Popen(["xdg-open", str(REPORTS_DIR)])
    except Exception:
        pass

    return f"Reporte del sistema creado en {archivo}."


def obtener_escritorio():
    escritorio = HOME / "Desktop"

    if escritorio.exists():
        return escritorio

    escritorio = HOME / "Escritorio"

    if escritorio.exists():
        return escritorio

    return None


def backup_escritorio():
    """
    Crea un backup del Escritorio en ~/ARGOS/backups/
    """
    escritorio = obtener_escritorio()

    if not escritorio:
        return "No encontré la carpeta Escritorio o Desktop."

    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)

    fecha = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    destino = BACKUPS_DIR / f"backup_escritorio_{fecha}"

    try:
        shutil.copytree(escritorio, destino)
    except Exception as e:
        return f"No pude crear el backup del escritorio. Error: {e}"

    try:
        subprocess.Popen(["xdg-open", str(BACKUPS_DIR)])
    except Exception:
        pass

    return f"Backup del escritorio creado en {destino}."


def revisar_temperatura_simple(limite=80):
    """
    Revisa la temperatura actual y avisa si pasa del límite.
    """
    temp = obtener_temperatura()

    if not temp["disponible"]:
        return "No pude leer la temperatura. Puede que necesites configurar lm-sensors."

    if temp["temperatura"] is None:
        return resumen_temperatura()

    temperatura = temp["temperatura"]

    if temperatura >= limite:
        return f"Alerta. La temperatura está en {temperatura} grados Celsius, supera el límite de {limite} grados."

    return f"La temperatura está normal: {temperatura} grados Celsius. El límite configurado es {limite} grados."
