import sqlite3
from pathlib import Path
from datetime import datetime


# ==========================
# BASE DE DATOS DE MEMORIA
# ==========================

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "memory.db"


def conectar():
    return sqlite3.connect(DB_PATH)


def inicializar_memoria():
    """
    Crea las tablas necesarias para memoria explícita y memoria automática.
    """
    conn = conectar()
    cursor = conn.cursor()

    # Memorias explícitas: cuando el usuario dice "recuerda que..."
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            topic TEXT,
            content TEXT NOT NULL
        )
    """)

    # Conversaciones automáticas: todo lo que el usuario pregunta y A.R.G.O.S. responde
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            user_text TEXT NOT NULL,
            assistant_text TEXT NOT NULL,
            source TEXT DEFAULT 'auto'
        )
    """)

    conn.commit()
    conn.close()


# ==========================
# MEMORIA EXPLÍCITA
# ==========================

def guardar_memoria(contenido, tema=None):
    """
    Guarda una memoria importante manualmente.
    """
    inicializar_memoria()

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO memories (created_at, topic, content) VALUES (?, ?, ?)",
        (datetime.now().isoformat(timespec="seconds"), tema, contenido)
    )

    conn.commit()
    conn.close()

    return "He guardado eso en mi memoria."


def buscar_memorias(texto, limite=5):
    """
    Busca memorias explícitas por palabras clave.
    """
    inicializar_memoria()

    conn = conectar()
    cursor = conn.cursor()

    palabras = [p for p in texto.lower().split() if len(p) > 2]

    if not palabras:
        conn.close()
        return []

    condiciones = " OR ".join([
        "LOWER(content) LIKE ? OR LOWER(topic) LIKE ?"
        for _ in palabras
    ])

    parametros = []

    for palabra in palabras:
        parametros.extend([f"%{palabra}%", f"%{palabra}%"])

    cursor.execute(
        f"""
        SELECT created_at, topic, content
        FROM memories
        WHERE {condiciones}
        ORDER BY created_at DESC
        LIMIT ?
        """,
        parametros + [limite]
    )

    resultados = cursor.fetchall()
    conn.close()

    return resultados


def formatear_memorias(resultados):
    """
    Convierte memorias explícitas a texto legible.
    """
    if not resultados:
        return "No encontré recuerdos explícitos relacionados."

    texto = "Recuerdos explícitos encontrados:\n"

    for fecha, tema, contenido in resultados:
        tema_txt = tema if tema else "sin tema"
        texto += f"- Fecha: {fecha}. Tema: {tema_txt}. Recuerdo: {contenido}\n"

    return texto


# ==========================
# MEMORIA AUTOMÁTICA
# ==========================

def guardar_conversacion(usuario, asistente, source="auto"):
    """
    Guarda automáticamente una interacción entre el usuario y A.R.G.O.S.
    """
    inicializar_memoria()

    usuario = str(usuario).strip()
    asistente = str(asistente).strip()

    if not usuario or not asistente:
        return

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO conversations (created_at, user_text, assistant_text, source)
        VALUES (?, ?, ?, ?)
        """,
        (
            datetime.now().isoformat(timespec="seconds"),
            usuario,
            asistente,
            source
        )
    )

    conn.commit()
    conn.close()


def buscar_conversaciones(texto, limite=8):
    """
    Busca conversaciones pasadas por palabras clave.
    """
    inicializar_memoria()

    conn = conectar()
    cursor = conn.cursor()

    palabras = [p for p in texto.lower().split() if len(p) > 2]

    if not palabras:
        conn.close()
        return []

    condiciones = " OR ".join([
        "LOWER(user_text) LIKE ? OR LOWER(assistant_text) LIKE ?"
        for _ in palabras
    ])

    parametros = []

    for palabra in palabras:
        parametros.extend([f"%{palabra}%", f"%{palabra}%"])

    cursor.execute(
        f"""
        SELECT created_at, user_text, assistant_text
        FROM conversations
        WHERE {condiciones}
        ORDER BY created_at DESC
        LIMIT ?
        """,
        parametros + [limite]
    )

    resultados = cursor.fetchall()
    conn.close()

    return resultados


def formatear_conversaciones(resultados):
    """
    Convierte conversaciones pasadas a texto legible.
    """
    if not resultados:
        return "No encontré conversaciones pasadas relacionadas."

    texto = "Conversaciones pasadas encontradas:\n"

    for fecha, usuario, asistente in resultados:
        texto += f"- Fecha: {fecha}\n"
        texto += f"  Usuario: {usuario}\n"
        texto += f"  A.R.G.O.S.: {asistente}\n"

    return texto


# ==========================
# CONTEXTO PARA IA
# ==========================

def obtener_contexto_relevante(texto, limite_memorias=5, limite_conversaciones=6):
    """
    Busca recuerdos y conversaciones relacionadas para dárselas a Ollama como contexto.
    """
    memorias = buscar_memorias(texto, limite=limite_memorias)
    conversaciones = buscar_conversaciones(texto, limite=limite_conversaciones)

    partes = []

    if memorias:
        partes.append("Memorias explícitas:")
        for fecha, tema, contenido in memorias:
            tema_txt = tema if tema else "sin tema"
            partes.append(f"- {fecha} | {tema_txt}: {contenido}")

    if conversaciones:
        partes.append("Conversaciones pasadas:")
        for fecha, usuario, asistente in conversaciones:
            partes.append(f"- {fecha} | Usuario: {usuario} | A.R.G.O.S.: {asistente}")

    if not partes:
        return "No hay contexto previo relevante."

    return "\n".join(partes)


def buscar_todo_en_memoria(texto):
    """
    Busca tanto memorias explícitas como conversaciones automáticas.
    """
    memorias = buscar_memorias(texto)
    conversaciones = buscar_conversaciones(texto)

    respuesta = ""

    if memorias:
        respuesta += formatear_memorias(memorias) + "\n"

    if conversaciones:
        respuesta += formatear_conversaciones(conversaciones)

    if not respuesta.strip():
        respuesta = "No encontré nada relacionado en mi memoria."

    return respuesta
