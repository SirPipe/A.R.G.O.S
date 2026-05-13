import speech_recognition as sr
import os
import subprocess
import datetime
import sys
import shutil
import requests

from file_manager import (
    buscar_por_palabras_clave,
    listar_pdfs_por_tema,
    crear_carpeta_en_escritorio,
    abrir_ruta
)

from memory import (
    guardar_memoria,
    buscar_memorias,
    formatear_memorias,
    inicializar_memoria
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

# Modelo instalado en Ollama
MODELO_OLLAMA = "llama3:latest"

r = sr.Recognizer()


# ==========================
# VOZ DE A.R.G.O.S.
# ==========================

def hablar(texto):
    """
    Hace que A.R.G.O.S. hable usando espeak-ng.
    """
    print(f"A.R.G.O.S.: {texto}")

    texto_limpio = str(texto).replace('"', "'")
    os.system(f'espeak-ng -v es "{texto_limpio}"')


# ==========================
# FUNCIONES DE SISTEMA
# ==========================

def abrir_url(url):
    """
    Abre una URL en Firefox.
    """
    try:
        subprocess.Popen(["firefox", url])
    except Exception as e:
        hablar(f"No pude abrir Firefox. Error: {e}")


def abrir_terminal():
    """
    Busca una terminal instalada y la abre.
    """
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
            return

    hablar("No encontré una terminal instalada.")


def abrir_archivos():
    """
    Abre el explorador de archivos de Ubuntu.
    """
    exploradores = [
        "nautilus",
        "nemo",
        "thunar",
        "dolphin"
    ]

    for explorador in exploradores:
        if shutil.which(explorador):
            subprocess.Popen([explorador])
            return

    hablar("No encontré un explorador de archivos instalado.")


def abrir_vscode():
    """
    Abre Visual Studio Code si está instalado.
    """
    if shutil.which("code"):
        subprocess.Popen(["code"])
    else:
        hablar("No encontré Visual Studio Code instalado.")


def abrir_programa(nombre_programa):
    """
    Intenta abrir un programa por nombre.
    """
    if shutil.which(nombre_programa):
        subprocess.Popen([nombre_programa])
        hablar(f"Abriendo {nombre_programa}.")
    else:
        hablar(f"No encontré el programa {nombre_programa} instalado.")


# ==========================
# CONEXIÓN CON OLLAMA
# ==========================

def preguntar_a_ollama(pregunta):
    """
    Envía preguntas generales a Ollama.
    Si el comando no es local, A.R.G.O.S. responde con IA.
    """
    try:
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
Si el usuario hace una pregunta científica, responde con una explicación fácil de entender.
Máximo 4 oraciones, excepto si el usuario pide más detalle.

Pregunta del usuario:
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
    """
    Busca archivos por palabras clave.
    Ejemplos:
    - argos busca mi tesis
    - argos busca documento vidanta
    """
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
        hablar("Dime qué archivo quieres buscar.")
        return

    resultados = buscar_por_palabras_clave(consulta.split(), limite=5)

    if not resultados:
        hablar("No encontré archivos relacionados.")
        return

    hablar(f"Encontré {len(resultados)} archivos relacionados.")
    print("\nResultados encontrados:")

    for i, archivo in enumerate(resultados, start=1):
        print(f"{i}. {archivo}")

    print()
    hablar("Abriré el primer resultado.")
    abrir_ruta(resultados[0])


def comando_mostrar_pdfs(comando):
    """
    Busca PDFs relacionados con un tema.
    Ejemplos:
    - argos muéstrame pdfs de vidanta
    - argos busca pdfs de tesis
    """
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
        hablar("Dime el tema de los PDFs que quieres buscar.")
        return

    resultados = listar_pdfs_por_tema(tema, limite=10)

    if not resultados:
        hablar("No encontré PDFs relacionados.")
        return

    hablar(f"Encontré {len(resultados)} PDFs relacionados.")
    print("\nPDFs encontrados:")

    for i, archivo in enumerate(resultados, start=1):
        print(f"{i}. {archivo}")

    print()
    hablar("Abriré el primer PDF encontrado.")
    abrir_ruta(resultados[0])


def comando_crear_carpeta(comando):
    """
    Crea una carpeta en el escritorio y la abre.
    Ejemplo:
    - argos crea una carpeta llamada pipe en escritorio y ábrela
    """
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
        "en escritorio",
        "en el escritorio",
        "y abrela",
        "y ábrela",
        "abrela",
        "ábrela",
        "abre la",
        "abrirla"
    ]

    for frase in frases_a_quitar:
        nombre = nombre.replace(frase, "")

    nombre = nombre.strip()

    if not nombre:
        hablar("Dime el nombre de la carpeta.")
        return

    resultado = crear_carpeta_en_escritorio(nombre)
    hablar(resultado)


# ==========================
# MEMORIA
# ==========================

def comando_guardar_memoria(comando):
    """
    Guarda una memoria.
    Ejemplos:
    - argos recuerda que hablamos del examen de física el 12/01/2026
    - argos guarda en memoria que mi proyecto se llama ARGOS
    """
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
        hablar("Dime qué quieres que recuerde.")
        return

    respuesta = guardar_memoria(contenido)
    hablar(respuesta)


def comando_buscar_memoria(comando):
    """
    Busca recuerdos guardados.
    Ejemplos:
    - argos cuándo hablamos del examen de física
    - argos qué recuerdas de vidanta
    """
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
        "busca en tu memoria"
    ]

    for frase in frases_a_quitar:
        consulta = consulta.replace(frase, "")

    consulta = consulta.strip()

    if not consulta:
        hablar("Dime qué quieres que busque en mi memoria.")
        return

    resultados = buscar_memorias(consulta)
    respuesta = formatear_memorias(resultados)

    print("\nMemoria:")
    print(respuesta)
    print()

    hablar(respuesta)


# ==========================
# COMANDOS DE A.R.G.O.S.
# ==========================

def ejecutar_comando(comando):
    """
    Primero intenta ejecutar comandos locales.
    Si no reconoce el comando, consulta a Ollama.
    """

    comando = comando.lower().strip()
    print("Comando recibido:", comando)

    # ==========================
    # NAVEGADOR / WEBS
    # ==========================

    if "youtube" in comando:
        hablar("Abriendo YouTube.")
        abrir_url("https://youtube.com")

    elif "whatsapp" in comando or "guasap" in comando or "what's up" in comando:
        hablar("Abriendo WhatsApp.")
        abrir_url("https://web.whatsapp.com")

    elif "google" in comando:
        hablar("Abriendo Google.")
        abrir_url("https://google.com")

    # ==========================
    # PROGRAMAS
    # ==========================

    elif "terminal" in comando:
        hablar("Abriendo la terminal.")
        abrir_terminal()

    elif "archivos" in comando or "carpeta personal" in comando or "explorador" in comando:
        hablar("Abriendo el explorador de archivos.")
        abrir_archivos()

    elif "visual studio" in comando or "vscode" in comando or "vs code" in comando:
        hablar("Abriendo Visual Studio Code.")
        abrir_vscode()

    elif "chrome" in comando:
        if shutil.which("google-chrome"):
            hablar("Abriendo Chrome.")
            subprocess.Popen(["google-chrome"])
        elif shutil.which("chromium"):
            hablar("Abriendo Chromium.")
            subprocess.Popen(["chromium"])
        elif shutil.which("chromium-browser"):
            hablar("Abriendo Chromium.")
            subprocess.Popen(["chromium-browser"])
        else:
            hablar("No encontré Chrome o Chromium instalado.")

    elif "steam" in comando:
        if shutil.which("steam"):
            hablar("Abriendo Steam.")
            subprocess.Popen(["steam"])
        else:
            hablar("No encontré Steam instalado.")

    # ==========================
    # ARCHIVOS
    # ==========================

    elif "crea una carpeta" in comando or "crear una carpeta" in comando or "crea carpeta" in comando or "crear carpeta" in comando:
        comando_crear_carpeta(comando)

    elif "pdf" in comando or "pdfs" in comando:
        comando_mostrar_pdfs(comando)

    elif "busca" in comando or "buscar" in comando:
        comando_buscar_archivo(comando)

    # ==========================
    # MEMORIA
    # ==========================

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
        or "recuerdas algo" in comando
    ):
        comando_buscar_memoria(comando)

    # ==========================
    # FECHA Y HORA
    # ==========================

    elif "hora" in comando:
        hora = datetime.datetime.now().strftime("%H:%M")
        hablar(f"Son las {hora}")

    elif "fecha" in comando or "día" in comando or "dia" in comando:
        fecha = datetime.datetime.now().strftime("%d/%m/%Y")
        hablar(f"Hoy es {fecha}")

    # ==========================
    # CONTROL DEL ASISTENTE
    # ==========================

    elif "salir" in comando or "apágate" in comando or "apagate" in comando or "cerrar" in comando:
        hablar("Cerrando A.R.G.O.S.")
        sys.exit()

    # ==========================
    # IA LOCAL
    # ==========================

    else:
        hablar("Consultando mi inteligencia local.")
        respuesta = preguntar_a_ollama(comando)

        print("\nRespuesta IA:")
        print(respuesta)
        print()

        hablar(respuesta)


# ==========================
# ESCUCHA
# ==========================

def escuchar():
    """
    Escucha por micrófono y convierte voz a texto.
    """
    with sr.Microphone() as source:
        print("Escuchando...")
        r.adjust_for_ambient_noise(source, duration=0.5)

        # 12 segundos para permitir preguntas largas
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
    """
    Verifica si el usuario dijo una palabra de activación.
    """
    for palabra in PALABRAS_ACTIVACION:
        if palabra in texto:
            return palabra

    return None


def limpiar_comando(texto, palabra_activacion):
    """
    Quita la palabra de activación y limpia el comando.
    """
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
                hablar("Estoy escuchando.")
            else:
                ejecutar_comando(comando)

        else:
            print("No dijiste la palabra de activación.")
            print("Ejemplo: argos abre youtube")


if __name__ == "__main__":
    main()
