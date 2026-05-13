import speech_recognition as sr
import subprocess
import datetime
import sys
import shutil
import requests
import time
from pathlib import Path

from file_manager import (
    buscar_por_palabras_clave,
    buscar_elementos_por_palabras_clave,
    buscar_en_escritorio,
    listar_pdfs_por_tema,
    crear_carpeta_en_escritorio,
    abrir_ruta,
    mandar_a_papelera
)

from memory import (
    guardar_memoria,
    buscar_todo_en_memoria,
    obtener_contexto_relevante,
    guardar_conversacion,
    inicializar_memoria
)

from system_tools import (
    resumen_estado_sistema,
    resumen_ram,
    resumen_cpu,
    resumen_disco,
    resumen_red,
    resumen_ip,
    resumen_temperatura
)


# ==========================
# CONFIGURACIÓN GENERAL
# ==========================

PALABRAS_ACTIVACION = [
    "argos",
    "argus",
    "arcos",
    "a.r.g.o.s",
    "asistente"
]

MODELO_OLLAMA = "llama3:latest"

BASE_DIR = Path.home() / "ARGOS"
VOICE_MODEL = BASE_DIR / "voices" / "es_MX-ald-medium.onnx"
TTS_OUTPUT = BASE_DIR / "data" / "argos_voice.wav"

r = sr.Recognizer()
proceso_voz = None


# ==========================
# VOZ DE A.R.G.O.S. CON PIPER
# ==========================

def detener_voz():
    global proceso_voz

    try:
        if proceso_voz and proceso_voz.poll() is None:
            proceso_voz.terminate()
            proceso_voz = None

        subprocess.run(
            ["pkill", "-f", "aplay"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        subprocess.run(
            ["pkill", "-f", "piper"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    except Exception:
        pass


def esperar_fin_de_voz():
    global proceso_voz

    try:
        if proceso_voz:
            proceso_voz.wait()
            proceso_voz = None

        time.sleep(0.35)

    except Exception:
        pass


def limpiar_texto_para_voz(texto):
    texto = str(texto)

    reemplazos = {
        "A.R.G.O.S.": "Argos",
        "A.R.G.O.S": "Argos",
        "CPU": "procesador",
        "RAM": "ram",
        "GB": "gigabytes",
        "MB": "megabytes",
        "°C": "grados Celsius",
        "%": "por ciento",
        "/": " ",
        "\\": " ",
        '"': "'"
    }

    for original, reemplazo in reemplazos.items():
        texto = texto.replace(original, reemplazo)

    return texto.strip()


def hablar(texto):
    global proceso_voz

    print(f"A.R.G.O.S.: {texto}")

    texto_limpio = limpiar_texto_para_voz(texto)

    try:
        detener_voz()

        if not VOICE_MODEL.exists():
            print(f"No encontré el modelo de voz: {VOICE_MODEL}")
            return

        TTS_OUTPUT.parent.mkdir(parents=True, exist_ok=True)

        subprocess.run(
            [
                "piper",
                "--model",
                str(VOICE_MODEL),
                "--output_file",
                str(TTS_OUTPUT)
            ],
            input=texto_limpio,
            text=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=60
        )

        proceso_voz = subprocess.Popen(
            ["aplay", "-q", str(TTS_OUTPUT)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    except Exception as e:
        print(f"No pude reproducir voz con Piper: {e}")


def responder_y_guardar(comando, respuesta, source="local"):
    hablar(respuesta)
    guardar_conversacion(comando, respuesta, source=source)


# ==========================
# FUNCIONES DE SISTEMA
# ==========================

def abrir_url(url):
    try:
        subprocess.Popen(["firefox", url])
    except Exception as e:
        hablar(f"No pude abrir Firefox. Error: {e}")


def abrir_terminal():
    terminales = [
        "gnome-terminal",
        "kgx",
        "konsole",
        "xfce4-terminal",
        "xterm",
        "tilix"
    ]

    for terminal in terminales:
        if shutil.which(terminal):
            subprocess.Popen([terminal])
            return True

    return False


def abrir_archivos():
    exploradores = [
        "nautilus",
        "nemo",
        "thunar",
        "dolphin"
    ]

    for explorador in exploradores:
        if shutil.which(explorador):
            subprocess.Popen([explorador])
            return True

    return False


def abrir_vscode():
    if shutil.which("code"):
        subprocess.Popen(["code"])
        return True

    return False


# ==========================
# CONEXIÓN CON OLLAMA
# ==========================

def preguntar_a_ollama(pregunta):
    try:
        contexto = obtener_contexto_relevante(pregunta)

        respuesta = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": MODELO_OLLAMA,
                "prompt": f"""
Eres A.R.G.O.S., un asistente personal local.
Tu nombre completo es Asistente de Red para Gestión, Operación y Seguridad.

Responde siempre en español.
Responde de forma clara, breve y útil.
Si el usuario pide un cálculo, muestra el procedimiento de forma sencilla.
Si el usuario pregunta por algo que ya se habló antes, usa el contexto de memoria.
Si no hay información previa relevante, responde con conocimiento general.
Máximo 4 oraciones, excepto si el usuario pide más detalle.

Contexto relevante de memoria:
{contexto}

Pregunta actual del usuario:
{pregunta}
""",
                "stream": False
            },
            timeout=90
        )

        if respuesta.status_code != 200:
            return f"Ollama respondió con error {respuesta.status_code}. Verifica que el modelo {MODELO_OLLAMA} esté instalado."

        data = respuesta.json()
        return data.get("response", "No pude generar una respuesta.")

    except requests.exceptions.ConnectionError:
        return "No pude conectar con Ollama. Verifica que Ollama esté instalado y funcionando."

    except requests.exceptions.Timeout:
        return "Ollama tardó demasiado en responder."

    except Exception as e:
        return f"Ocurrió un error al consultar Ollama: {e}"


# ==========================
# MANEJO DE ARCHIVOS
# ==========================

def comando_buscar_archivo(comando):
    consulta = comando

    palabras_a_quitar = [
        "busca",
        "buscar",
        "archivo",
        "archivos",
        "documento",
        "documentos",
        "mi",
        "mis"
    ]

    for palabra in palabras_a_quitar:
        consulta = consulta.replace(palabra, "")

    consulta = consulta.strip()

    if not consulta:
        respuesta = "Dime qué archivo quieres buscar."
        responder_y_guardar(comando, respuesta, source="files")
        return

    resultados = buscar_por_palabras_clave(consulta.split(), limite=5)

    if not resultados:
        respuesta = "No encontré archivos relacionados."
        responder_y_guardar(comando, respuesta, source="files")
        return

    print("\nResultados encontrados:")

    for i, archivo in enumerate(resultados, start=1):
        print(f"{i}. {archivo}")

    print()

    respuesta = f"Encontré {len(resultados)} archivos relacionados. Abriré el primer resultado."
    hablar(respuesta)
    abrir_ruta(resultados[0])
    guardar_conversacion(comando, respuesta, source="files")


def comando_mostrar_pdfs(comando):
    tema = comando

    palabras_a_quitar = [
        "muéstrame",
        "muestrame",
        "mostrar",
        "muestra",
        "busca",
        "buscar",
        "pdfs",
        "pdf",
        "de",
        "del",
        "la",
        "el",
        "los",
        "las"
    ]

    for palabra in palabras_a_quitar:
        tema = tema.replace(palabra, "")

    tema = tema.strip()

    if not tema:
        respuesta = "Dime el tema de los PDFs que quieres buscar."
        responder_y_guardar(comando, respuesta, source="files")
        return

    resultados = listar_pdfs_por_tema(tema, limite=10)

    if not resultados:
        respuesta = "No encontré PDFs relacionados."
        responder_y_guardar(comando, respuesta, source="files")
        return

    print("\nPDFs encontrados:")

    for i, archivo in enumerate(resultados, start=1):
        print(f"{i}. {archivo}")

    print()

    respuesta = f"Encontré {len(resultados)} PDFs relacionados. Abriré el primer PDF encontrado."
    hablar(respuesta)
    abrir_ruta(resultados[0])
    guardar_conversacion(comando, respuesta, source="files")


def comando_crear_carpeta(comando):
    nombre = comando

    frases_a_quitar = [
        "crea una carpeta llamada",
        "crear una carpeta llamada",
        "crea carpeta llamada",
        "crear carpeta llamada",
        "crea una carpeta",
        "crear una carpeta",
        "crea carpeta",
        "crear carpeta",
        "en el escritorio",
        "en escritorio",
        "escritorio",
        "desktop",
        "y abrela",
        "y ábrela",
        "abrela",
        "ábrela",
        "abre la",
        "abrirla"
    ]

    for frase in frases_a_quitar:
        nombre = nombre.replace(frase, " ")

    nombre = " ".join(nombre.split()).strip()

    if not nombre:
        respuesta = "Dime el nombre de la carpeta."
        responder_y_guardar(comando, respuesta, source="files")
        return

    resultado = crear_carpeta_en_escritorio(nombre)
    responder_y_guardar(comando, resultado, source="files")


def limpiar_nombre_para_borrar(comando):
    consulta = comando.lower().strip()

    frases_a_quitar = [
        "borra la carpeta",
        "borra carpeta",
        "borra el archivo",
        "borra archivo",
        "borra el elemento",
        "borra elemento",
        "borra",
        "borrar la carpeta",
        "borrar carpeta",
        "borrar el archivo",
        "borrar archivo",
        "borrar",
        "elimina la carpeta",
        "elimina carpeta",
        "elimina el archivo",
        "elimina archivo",
        "elimina el elemento",
        "elimina elemento",
        "elimina",
        "eliminar la carpeta",
        "eliminar carpeta",
        "eliminar el archivo",
        "eliminar archivo",
        "eliminar",
        "manda a la papelera la carpeta",
        "manda a la papelera el archivo",
        "manda a la papelera",
        "mueve a la papelera la carpeta",
        "mueve a la papelera el archivo",
        "mueve a la papelera",
        "que está en el escritorio",
        "que esta en el escritorio",
        "está en el escritorio",
        "esta en el escritorio",
        "en el escritorio",
        "en escritorio",
        "escritorio",
        "desktop",
        "la",
        "el",
        "mi",
        "mis"
    ]

    for frase in frases_a_quitar:
        consulta = consulta.replace(frase, " ")

    consulta = " ".join(consulta.split())
    return consulta


def detectar_tipo_borrado(comando):
    if "carpeta" in comando or "folder" in comando:
        return "carpeta"

    if "archivo" in comando or "documento" in comando:
        return "archivo"

    return "ambos"


def comando_borrar_elemento(comando):
    tipo = detectar_tipo_borrado(comando)
    consulta = limpiar_nombre_para_borrar(comando)

    if not consulta:
        respuesta = "Dime qué archivo o carpeta quieres mandar a la Papelera."
        responder_y_guardar(comando, respuesta, source="files")
        return

    resultados = []

    if "escritorio" in comando or "desktop" in comando:
        resultados = buscar_en_escritorio(consulta, tipo=tipo, limite=5)

    if not resultados:
        resultados = buscar_elementos_por_palabras_clave(consulta.split(), tipo=tipo, limite=5)

    if not resultados:
        respuesta = f"No encontré {tipo} relacionado con {consulta} para borrar."
        responder_y_guardar(comando, respuesta, source="files")
        return

    print("\nElementos encontrados para borrar:")
    for i, elemento in enumerate(resultados, start=1):
        print(f"{i}. {elemento}")

    print()

    elemento = resultados[0]

    respuesta_inicial = f"Encontré {elemento.name}. Lo mandaré a la Papelera."
    hablar(respuesta_inicial)

    resultado = mandar_a_papelera(elemento)
    responder_y_guardar(comando, resultado, source="files")


# ==========================
# MEMORIA
# ==========================

def comando_guardar_memoria(comando):
    contenido = comando

    frases_a_quitar = [
        "recuerda que",
        "recuerdame que",
        "recuérdame que",
        "guarda en memoria que",
        "guarda en memoria",
        "memoriza que",
        "aprende que"
    ]

    for frase in frases_a_quitar:
        contenido = contenido.replace(frase, "")

    contenido = contenido.strip()

    if not contenido:
        respuesta = "Dime qué quieres que recuerde."
        responder_y_guardar(comando, respuesta, source="memory")
        return

    respuesta = guardar_memoria(contenido)
    hablar(respuesta)

    guardar_conversacion(
        comando,
        f"{respuesta} Contenido guardado: {contenido}",
        source="memory"
    )


def comando_buscar_memoria(comando):
    consulta = comando

    frases_a_quitar = [
        "cuando hablamos de",
        "cuándo hablamos de",
        "cuando hablamos",
        "cuándo hablamos",
        "que recuerdas de",
        "qué recuerdas de",
        "que recuerdas",
        "qué recuerdas",
        "recuerdas algo de",
        "recuerdas algo sobre",
        "busca en memoria",
        "busca en tu memoria",
        "busca en tus recuerdos",
        "qué sabes de",
        "que sabes de"
    ]

    for frase in frases_a_quitar:
        consulta = consulta.replace(frase, "")

    consulta = consulta.strip()

    if not consulta:
        respuesta = "Dime qué quieres que busque en mi memoria."
        responder_y_guardar(comando, respuesta, source="memory")
        return

    respuesta = buscar_todo_en_memoria(consulta)

    print("\nMemoria:")
    print(respuesta)
    print()

    hablar(respuesta)
    guardar_conversacion(comando, respuesta, source="memory")


# ==========================
# ESTADO DEL SISTEMA
# ==========================

def comando_estado_sistema(comando):
    if (
        "estado del sistema" in comando
        or "cómo está el sistema" in comando
        or "como está el sistema" in comando
        or "como esta el sistema" in comando
        or "reporte del sistema" in comando
        or "diagnóstico del sistema" in comando
        or "diagnostico del sistema" in comando
    ):
        respuesta = resumen_estado_sistema()

    elif (
        "cuál es mi ip" in comando
        or "cual es mi ip" in comando
        or "dime mi ip" in comando
        or "ip local" in comando
        or comando.strip() == "ip"
        or comando.strip() == "mi ip"
    ):
        respuesta = resumen_ip()

    elif (
        "ram" in comando
        or "memoria ram" in comando
        or ("memoria" in comando and "sistema" in comando)
    ):
        respuesta = resumen_ram()

    elif (
        "cpu" in comando
        or "procesador" in comando
        or "uso del procesador" in comando
    ):
        respuesta = resumen_cpu()

    elif (
        "disco" in comando
        or "almacenamiento" in comando
        or "espacio" in comando
    ):
        respuesta = resumen_disco()

    elif (
        "red" in comando
        or "internet" in comando
        or "conexión" in comando
        or "conexion" in comando
    ):
        respuesta = resumen_red()

    elif (
        "temperatura" in comando
        or "caliente" in comando
        or "grados" in comando
    ):
        respuesta = resumen_temperatura()

    else:
        respuesta = resumen_estado_sistema()

    print("\nEstado del sistema:")
    print(respuesta)
    print()

    responder_y_guardar(comando, respuesta, source="system_status")


def es_comando_estado_sistema(comando):
    frases_clave = [
        "estado del sistema",
        "cómo está el sistema",
        "como está el sistema",
        "como esta el sistema",
        "reporte del sistema",
        "diagnóstico del sistema",
        "diagnostico del sistema",
        "memoria ram",
        "uso del procesador",
        "cuál es mi ip",
        "cual es mi ip",
        "dime mi ip",
        "ip local",
        "mi ip",
        "temperatura del procesador",
        "espacio en disco",
        "cuánto espacio",
        "cuanto espacio",
        "cómo está la red",
        "como esta la red",
        "cómo está el internet",
        "como esta el internet"
    ]

    palabras_exactas = comando.split()

    if any(frase in comando for frase in frases_clave):
        return True

    if "ram" in palabras_exactas:
        return True

    if "cpu" in palabras_exactas:
        return True

    if "procesador" in palabras_exactas:
        return True

    if "disco" in palabras_exactas:
        return True

    if "red" in palabras_exactas:
        return True

    if "internet" in palabras_exactas:
        return True

    if "temperatura" in palabras_exactas:
        return True

    if comando.strip() == "ip":
        return True

    return False


# ==========================
# DETECTORES DE COMANDOS
# ==========================

def es_comando_crear_carpeta(comando):
    return (
        "crea una carpeta" in comando
        or "crear una carpeta" in comando
        or "crea carpeta" in comando
        or "crear carpeta" in comando
    )


def es_comando_borrar(comando):
    return (
        "borra" in comando
        or "borrar" in comando
        or "elimina" in comando
        or "eliminar" in comando
        or "manda a la papelera" in comando
        or "mueve a la papelera" in comando
    )


# ==========================
# COMANDOS DE A.R.G.O.S.
# ==========================

def ejecutar_comando(comando):
    comando = comando.lower().strip()
    print("Comando recibido:", comando)

    if (
        comando == "alto"
        or comando == "callate"
        or comando == "cállate"
        or comando == "silencio"
        or comando == "detente"
        or comando == "para"
        or comando == "stop"
    ):
        detener_voz()
        respuesta = "Voz detenida. Estoy escuchando."
        print(f"A.R.G.O.S.: {respuesta}")
        guardar_conversacion(comando, respuesta, source="system")
        return

    if "youtube" in comando:
        respuesta = "Abriendo YouTube."
        hablar(respuesta)
        abrir_url("https://youtube.com")
        guardar_conversacion(comando, respuesta, source="apps")

    elif "whatsapp" in comando or "guasap" in comando or "what's up" in comando:
        respuesta = "Abriendo WhatsApp."
        hablar(respuesta)
        abrir_url("https://web.whatsapp.com")
        guardar_conversacion(comando, respuesta, source="apps")

    elif "google" in comando:
        respuesta = "Abriendo Google."
        hablar(respuesta)
        abrir_url("https://google.com")
        guardar_conversacion(comando, respuesta, source="apps")

    elif "terminal" in comando:
        if abrir_terminal():
            respuesta = "Abriendo la terminal."
        else:
            respuesta = "No encontré una terminal instalada."

        responder_y_guardar(comando, respuesta, source="apps")

    elif "archivos" in comando or "carpeta personal" in comando or "explorador" in comando:
        if abrir_archivos():
            respuesta = "Abriendo el explorador de archivos."
        else:
            respuesta = "No encontré un explorador de archivos instalado."

        responder_y_guardar(comando, respuesta, source="apps")

    elif "visual studio" in comando or "vscode" in comando or "vs code" in comando:
        if abrir_vscode():
            respuesta = "Abriendo Visual Studio Code."
        else:
            respuesta = "No encontré Visual Studio Code instalado."

        responder_y_guardar(comando, respuesta, source="apps")

    elif "chrome" in comando:
        if shutil.which("google-chrome"):
            subprocess.Popen(["google-chrome"])
            respuesta = "Abriendo Chrome."
        elif shutil.which("chromium"):
            subprocess.Popen(["chromium"])
            respuesta = "Abriendo Chromium."
        elif shutil.which("chromium-browser"):
            subprocess.Popen(["chromium-browser"])
            respuesta = "Abriendo Chromium."
        else:
            respuesta = "No encontré Chrome o Chromium instalado."

        responder_y_guardar(comando, respuesta, source="apps")

    elif "steam" in comando:
        if shutil.which("steam"):
            subprocess.Popen(["steam"])
            respuesta = "Abriendo Steam."
        else:
            respuesta = "No encontré Steam instalado."

        responder_y_guardar(comando, respuesta, source="apps")

    # IMPORTANTE:
    # Los comandos de archivos van antes que estado del sistema.
    # Así evitamos que una carpeta llamada "pipe" active el comando "ip".
    elif es_comando_borrar(comando):
        comando_borrar_elemento(comando)

    elif es_comando_crear_carpeta(comando):
        comando_crear_carpeta(comando)

    elif "pdf" in comando or "pdfs" in comando:
        comando_mostrar_pdfs(comando)

    elif "busca" in comando or "buscar" in comando:
        comando_buscar_archivo(comando)

    elif es_comando_estado_sistema(comando):
        comando_estado_sistema(comando)

    elif (
        "recuerda que" in comando
        or "recuérdame que" in comando
        or "recuerdame que" in comando
        or "guarda en memoria" in comando
        or "memoriza que" in comando
        or "aprende que" in comando
    ):
        comando_guardar_memoria(comando)

    elif (
        "cuando hablamos" in comando
        or "cuándo hablamos" in comando
        or "que recuerdas" in comando
        or "qué recuerdas" in comando
        or "busca en memoria" in comando
        or "busca en tu memoria" in comando
        or "busca en tus recuerdos" in comando
        or "recuerdas algo" in comando
        or "qué sabes de" in comando
        or "que sabes de" in comando
    ):
        comando_buscar_memoria(comando)

    elif "hora" in comando:
        hora = datetime.datetime.now().strftime("%H:%M")
        respuesta = f"Son las {hora}"
        responder_y_guardar(comando, respuesta, source="time")

    elif "fecha" in comando or "día" in comando or "dia" in comando:
        fecha = datetime.datetime.now().strftime("%d/%m/%Y")
        respuesta = f"Hoy es {fecha}"
        responder_y_guardar(comando, respuesta, source="time")

    elif "salir" in comando or "apágate" in comando or "apagate" in comando or "cerrar" in comando:
        respuesta = "Cerrando A.R.G.O.S."
        hablar(respuesta)
        guardar_conversacion(comando, respuesta, source="system")
        esperar_fin_de_voz()
        sys.exit()

    else:
        hablar("Consultando mi inteligencia local.")
        esperar_fin_de_voz()

        respuesta = preguntar_a_ollama(comando)

        print("\nRespuesta IA:")
        print(respuesta)
        print()

        hablar(respuesta)
        guardar_conversacion(comando, respuesta, source="ollama")


# ==========================
# ESCUCHA
# ==========================

def escuchar():
    esperar_fin_de_voz()

    with sr.Microphone() as source:
        print("Escuchando...")
        r.adjust_for_ambient_noise(source, duration=0.5)

        audio = r.listen(source, phrase_time_limit=12)

    try:
        texto = r.recognize_google(audio, language="es-MX").lower()
        print("Dijiste:", texto)
        return texto

    except sr.UnknownValueError:
        print("No entendí.")
        return ""

    except sr.RequestError:
        print("Error con el servicio de reconocimiento de voz.")
        return ""


# ==========================
# ACTIVACIÓN
# ==========================

def contiene_activacion(texto):
    for palabra in PALABRAS_ACTIVACION:
        if palabra in texto:
            return palabra

    return None


def limpiar_comando(texto, palabra_activacion):
    comando = texto.replace(palabra_activacion, "").strip()

    palabras_relleno = [
        "por favor",
        "oye",
        "puedes",
        "puedes hacer",
        "me puedes",
        "quiero que",
        "necesito que"
    ]

    for palabra in palabras_relleno:
        comando = comando.replace(palabra, "").strip()

    return comando


# ==========================
# PROGRAMA PRINCIPAL
# ==========================

def main():
    inicializar_memoria()
    hablar("Sistema A.R.G.O.S. iniciado.")

    while True:
        texto = escuchar()

        if not texto:
            continue

        palabra_activacion = contiene_activacion(texto)

        if palabra_activacion:
            comando = limpiar_comando(texto, palabra_activacion)

            if comando == "":
                detener_voz()
                respuesta = "Estoy escuchando."
                hablar(respuesta)
                guardar_conversacion(texto, respuesta, source="system")
            else:
                if comando not in ["alto", "silencio", "detente", "para", "stop"]:
                    detener_voz()

                ejecutar_comando(comando)

        else:
            print("No dijiste la palabra de activación.")
            print("Ejemplo: argos crea una carpeta llamada pipe en escritorio")


if __name__ == "__main__":
    main()
