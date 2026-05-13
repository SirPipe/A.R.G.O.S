import speech_recognition as sr
import os
import subprocess
import datetime
import sys
import shutil
import requests


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

# Modelo instalado en tu Ollama
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

    texto_limpio = texto.replace('"', "'")
    os.system(f'espeak-ng -v es "{texto_limpio}"')


# ==========================
# FUNCIONES DE SISTEMA
# ==========================

def abrir_url(url):
    """
    Abre una URL en Firefox.
    """
    subprocess.Popen(["firefox", url])


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
# COMANDOS DE A.R.G.O.S.
# ==========================

def ejecutar_comando(comando):
    """
    Primero intenta ejecutar comandos locales.
    Si no reconoce el comando, consulta a Ollama.
    """

    print("Comando recibido:", comando)

    # NAVEGADOR / WEBS
    if "youtube" in comando:
        hablar("Abriendo YouTube.")
        abrir_url("https://youtube.com")

    elif "whatsapp" in comando or "guasap" in comando or "what's up" in comando:
        hablar("Abriendo WhatsApp.")
        abrir_url("https://web.whatsapp.com")

    elif "google" in comando:
        hablar("Abriendo Google.")
        abrir_url("https://google.com")

    # SISTEMA
    elif "terminal" in comando:
        hablar("Abriendo la terminal.")
        abrir_terminal()

    elif "archivos" in comando or "carpeta" in comando or "explorador" in comando:
        hablar("Abriendo el explorador de archivos.")
        abrir_archivos()

    elif "visual studio" in comando or "vscode" in comando or "vs code" in comando or "code" in comando:
        hablar("Abriendo Visual Studio Code.")
        abrir_vscode()

    # FECHA Y HORA
    elif "hora" in comando:
        hora = datetime.datetime.now().strftime("%H:%M")
        hablar(f"Son las {hora}")

    elif "fecha" in comando or "día" in comando or "dia" in comando:
        fecha = datetime.datetime.now().strftime("%d/%m/%Y")
        hablar(f"Hoy es {fecha}")

    # SALIR
    elif "salir" in comando or "apágate" in comando or "apagate" in comando or "cerrar" in comando:
        hablar("Cerrando A.R.G.O.S.")
        sys.exit()

    # IA LOCAL
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

        # Aumentado a 12 segundos para preguntas largas
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
        "quiero que"
    ]

    for palabra in palabras_relleno:
        comando = comando.replace(palabra, "").strip()

    return comando


# ==========================
# PROGRAMA PRINCIPAL
# ==========================

def main():
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
