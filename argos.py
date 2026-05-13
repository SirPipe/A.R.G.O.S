import speech_recognition as sr
import subprocess
import datetime
import sys
import shutil
import requests

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

r = sr.Recognizer()
proceso_voz = None


# ==========================
# VOZ DE A.R.G.O.S.
# ==========================

def detener_voz():
    global proceso_voz

    try:
        if proceso_voz and proceso_voz.poll() is None:
            proceso_voz.terminate()
            proceso_voz = None

        subprocess.run(
            ["pkill", "-f", "espeak-ng"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    except Exception:
        pass


def hablar(texto):
    global proceso_voz

    print(f"A.R.G.O.S.: {texto}")

    texto_limpio = str(texto).replace('"', "'")

    try:
        detener_voz()
        proceso_voz = subprocess.Popen(
            ["espeak-ng", "-v", "es", texto_limpio],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except Exception as e:
        print(f"No pude reproducir voz: {e}")


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
    """
    Manda archivos o carpetas a la Papelera.
    Ejemplos:
    - argos borra la carpeta pipe que está en el escritorio
    - argos elimina el archivo prueba
    - argos manda a la papelera pipe
    """
    tipo = detectar_tipo_borrado(comando)
    consulta = limpiar_nombre_para_borrar(comando)

    if not consulta:
        respuesta = "Dime qué archivo o carpeta quieres mandar a la Papelera."
        responder_y_guardar(comando, respuesta, source="files")
        return

    resultados = []

    if "escritorio" in comando:
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
# COMANDOS DE A.R.G.O.S.
# ==========================

def ejecutar_comando(comando):
    comando = comando.lower().strip()
    print("Comando recibido:", comando)

    # CONTROL DE VOZ
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

    # NAVEGADOR / WEBS
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

    # PROGRAMAS
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

    # MEMORIA
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

    # ARCHIVOS
    elif (
        "borra" in comando
        or "borrar" in comando
        or "elimina" in comando
        or "eliminar" in comando
        or "manda a la papelera" in comando
        or "mueve a la papelera" in comando
    ):
        comando_borrar_elemento(comando)

    elif "crea una carpeta" in comando or "crear una carpeta" in comando or "crea carpeta" in comando or "crear carpeta" in comando:
        comando_crear_carpeta(comando)

    elif "pdf" in comando or "pdfs" in comando:
        comando_mostrar_pdfs(comando)

    elif "busca" in comando or "buscar" in comando:
        comando_buscar_archivo(comando)

    # FECHA Y HORA
    elif "hora" in comando:
        hora = datetime.datetime.now().strftime("%H:%M")
        respuesta = f"Son las {hora}"
        responder_y_guardar(comando, respuesta, source="time")

    elif "fecha" in comando or "día" in comando or "dia" in comando:
        fecha = datetime.datetime.now().strftime("%d/%m/%Y")
        respuesta = f"Hoy es {fecha}"
        responder_y_guardar(comando, respuesta, source="time")

    # CONTROL DEL ASISTENTE
    elif "salir" in comando or "apágate" in comando or "apagate" in comando or "cerrar" in comando:
        respuesta = "Cerrando A.R.G.O.S."
        hablar(respuesta)
        guardar_conversacion(comando, respuesta, source="system")
        sys.exit()

    # IA LOCAL
    else:
        hablar("Consultando mi inteligencia local.")
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
            print("Ejemplo: argos borra la carpeta pipe que está en el escritorio")


if __name__ == "__main__":
    main()
