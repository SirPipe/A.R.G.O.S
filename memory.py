import sqlite3
from pathlib import Path
from datetime import datetime


DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "memory.db"


def conectar():
    return sqlite3.connect(DB_PATH)


def inicializar_memoria():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            topic TEXT,
            content TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def guardar_memoria(contenido, tema=None):
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
    inicializar_memoria()

    conn = conectar()
    cursor = conn.cursor()

    palabras = [p for p in texto.lower().split() if len(p) > 2]

    if not palabras:
        return []

    condiciones = " OR ".join(["LOWER(content) LIKE ? OR LOWER(topic) LIKE ?" for _ in palabras])
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
    if not resultados:
        return "No encontré recuerdos relacionados."

    texto = "Encontré esto en mi memoria:\n"

    for fecha, tema, contenido in resultados:
        tema_txt = tema if tema else "sin tema"
        texto += f"- Fecha: {fecha}. Tema: {tema_txt}. Recuerdo: {contenido}\n"

    return texto
