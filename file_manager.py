from pathlib import Path
import os
import shutil
import subprocess


HOME = Path.home()
CARPETAS_BUSQUEDA = [
    HOME / "Desktop",
    HOME / "Escritorio",
    HOME / "Documents",
    HOME / "Documentos",
    HOME / "Downloads",
    HOME / "Descargas",
    HOME / "ARGOS",
]


def abrir_ruta(ruta):
    ruta = Path(ruta)

    if not ruta.exists():
        return f"No existe la ruta: {ruta}"

    try:
        subprocess.Popen(["xdg-open", str(ruta)])
        return f"Abriendo {ruta.name}"
    except Exception as e:
        return f"No pude abrir la ruta. Error: {e}"


def buscar_archivos(texto_busqueda, extension=None, limite=10):
    texto_busqueda = texto_busqueda.lower().strip()
    resultados = []

    for carpeta in CARPETAS_BUSQUEDA:
        if not carpeta.exists():
            continue

        try:
            for archivo in carpeta.rglob("*"):
                if len(resultados) >= limite:
                    break

                if not archivo.is_file():
                    continue

                nombre = archivo.name.lower()

                if extension and archivo.suffix.lower() != extension.lower():
                    continue

                if texto_busqueda in nombre:
                    resultados.append(archivo)

        except PermissionError:
            continue
        except Exception:
            continue

    return resultados


def buscar_por_palabras_clave(palabras, extension=None, limite=10):
    resultados = []

    palabras = [
        p.lower()
        for p in palabras
        if len(p.strip()) > 2
    ]

    for carpeta in CARPETAS_BUSQUEDA:
        if not carpeta.exists():
            continue

        try:
            for archivo in carpeta.rglob("*"):
                if len(resultados) >= limite:
                    break

                if not archivo.is_file():
                    continue

                if extension and archivo.suffix.lower() != extension.lower():
                    continue

                nombre = archivo.name.lower()

                if any(p in nombre for p in palabras):
                    resultados.append(archivo)

        except PermissionError:
            continue
        except Exception:
            continue

    return resultados


def listar_pdfs_por_tema(tema, limite=10):
    palabras = tema.lower().split()
    return buscar_por_palabras_clave(palabras, extension=".pdf", limite=limite)


def crear_carpeta_en_escritorio(nombre):
    escritorio = HOME / "Desktop"

    if not escritorio.exists():
        escritorio = HOME / "Escritorio"

    if not escritorio.exists():
        return "No encontré la carpeta Escritorio o Desktop."

    nueva_carpeta = escritorio / nombre
    nueva_carpeta.mkdir(parents=True, exist_ok=True)

    abrir_ruta(nueva_carpeta)

    return f"Carpeta {nombre} creada y abierta en el escritorio."


def mover_archivo(origen, destino):
    origen = Path(origen)
    destino = Path(destino)

    if not origen.exists():
        return "No encontré el archivo de origen."

    destino.mkdir(parents=True, exist_ok=True)

    try:
        shutil.move(str(origen), str(destino / origen.name))
        return f"Archivo movido a {destino}"
    except Exception as e:
        return f"No pude mover el archivo. Error: {e}"


def copiar_archivo(origen, destino):
    origen = Path(origen)
    destino = Path(destino)

    if not origen.exists():
        return "No encontré el archivo de origen."

    destino.mkdir(parents=True, exist_ok=True)

    try:
        shutil.copy2(str(origen), str(destino / origen.name))
        return f"Archivo copiado a {destino}"
    except Exception as e:
        return f"No pude copiar el archivo. Error: {e}"
