'''
Archivo para funciones varias
'''
from flask import request, jsonify
import os
from dotenv import load_dotenv
import sqlite3

load_dotenv()
DB_PATH = "db/eventos.db"

# Funcion para Autenticacion de Token
TOKEN_SECRETO = os.getenv("SECRET_TOKEN")
def validar_token():
    auth = request.headers.get("Authorization", "")
    prefijo = "Bearer "
    if not auth or not auth.startswith(prefijo) or auth.split(" ",1)[1] != TOKEN_SECRETO:
        return jsonify({"error":"Cliente desconocido"}), 401    # Unauthorized
    return None

def crear_db(DB_PATH):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS eventos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            puntos_base INT NOT NULL, 
            fecha TEXT NOT NULL, 
            activo INT DEFAULT 1
        )""")

        conn.commit()

def consultar_un_evento(db_path, query, params):
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.execute(query, params)
        row = cur.fetchone()
        return dict(row) if row else None

if __name__ == "__main__":
    print("Seeder OK. DB en:", DB_PATH)