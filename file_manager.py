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


def obtener_escritorio():
    escritorio = HOME / "Desktop"

    if escritorio.exists():
        return escritorio

    escritorio = HOME / "Escritorio"

    if escritorio.exists():
        return escritorio

    return None


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
    """
    Busca solo archivos por palabras clave.
    """
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


def buscar_elementos_por_palabras_clave(palabras, tipo="ambos", limite=10):
    """
    Busca archivos y/o carpetas por palabras clave.

    tipo:
    - "archivo"
    - "carpeta"
    - "ambos"
    """
    resultados = []

    palabras = [
        p.lower().strip()
        for p in palabras
        if len(p.strip()) > 1
    ]

    if not palabras:
        return resultados

    for carpeta_base in CARPETAS_BUSQUEDA:
        if not carpeta_base.exists():
            continue

        try:
            for elemento in carpeta_base.rglob("*"):
                if len(resultados) >= limite:
                    break

                if tipo == "archivo" and not elemento.is_file():
                    continue

                if tipo == "carpeta" and not elemento.is_dir():
                    continue

                nombre = elemento.name.lower()

                if any(p in nombre for p in palabras):
                    resultados.append(elemento)

        except PermissionError:
            continue
        except Exception:
            continue

    return resultados


def buscar_en_escritorio(nombre, tipo="ambos", limite=10):
    """
    Busca archivos o carpetas directamente en el Escritorio/Desktop.
    """
    escritorio = obtener_escritorio()

    if not escritorio:
        return []

    resultados = []
    nombre = nombre.lower().strip()

    if not nombre:
        return []

    try:
        for elemento in escritorio.iterdir():
            if len(resultados) >= limite:
                break

            if tipo == "archivo" and not elemento.is_file():
                continue

            if tipo == "carpeta" and not elemento.is_dir():
                continue

            if nombre in elemento.name.lower():
                resultados.append(elemento)

    except PermissionError:
        pass
    except Exception:
        pass

    return resultados


def listar_pdfs_por_tema(tema, limite=10):
    palabras = tema.lower().split()
    return buscar_por_palabras_clave(palabras, extension=".pdf", limite=limite)


def crear_carpeta_en_escritorio(nombre):
    escritorio = obtener_escritorio()

    if not escritorio:
        return "No encontré la carpeta Escritorio o Desktop."

    nueva_carpeta = escritorio / nombre
    nueva_carpeta.mkdir(parents=True, exist_ok=True)

    abrir_ruta(nueva_carpeta)

    return f"Carpeta {nombre} creada y abierta en el escritorio."


def mandar_a_papelera(ruta):
    """
    Manda un archivo o carpeta a la Papelera.
    No elimina permanentemente.
    """
    ruta = Path(ruta).expanduser().resolve()

    if not ruta.exists():
        return f"No encontré el elemento: {ruta}"

    try:
        if shutil.which("gio"):
            subprocess.run(["gio", "trash", str(ruta)], check=True)
            return f"Moví {ruta.name} a la Papelera."

        trash_dir = HOME / ".local" / "share" / "Trash" / "files"
        trash_dir.mkdir(parents=True, exist_ok=True)

        destino = trash_dir / ruta.name
        contador = 1

        while destino.exists():
            if ruta.suffix:
                destino = trash_dir / f"{ruta.stem}_{contador}{ruta.suffix}"
            else:
                destino = trash_dir / f"{ruta.name}_{contador}"

            contador += 1

        shutil.move(str(ruta), str(destino))
        return f"Moví {ruta.name} a la Papelera."

    except Exception as e:
        return f"No pude moverlo a la Papelera. Error: {e}"


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
