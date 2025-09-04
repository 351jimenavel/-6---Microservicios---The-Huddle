'''
Archivo para funciones varias - puntos service
'''
from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
from datetime import datetime, timezone
import sqlite3
import uuid

load_dotenv()
DB_PATH = "db/transacciones.db"

# Funcion para Autenticacion de Token
TOKEN_SECRETO = os.getenv("SECRET_TOKEN")
def validar_token():
    auth = request.headers.get("Authorization", "")
    prefijo = "Bearer "
    if not auth or not auth.startswith(prefijo) or auth.split(" ",1)[1] != TOKEN_SECRETO:
        return jsonify({"error":"Cliente desconocido"}), 401    # Unauthorized
    return None

def crear_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS transacciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            evento_id INTEGER NOT NULL,
            puntos INTEGER NOT NULL, 
            created_at TEXT NOT NULL, 
            estado TEXT CHECK (estado IN ('activa','revocada')) DEFAULT 'activa',
            idem_key TEXT UNIQUE
        )""")
        conn.commit()

# insertar, consultar por idem_key, listar por usuario, update estado
# def consultar_por_idem_key(db_path, query, params):
#     with sqlite3.connect(db_path) as conn:
#         conn.row_factory = sqlite3.Row
#         cur = conn.execute(query, params)
#         #conn.execute(query, params)
#         row = cur.fetchone()
#         return row
        #return dict(row) if row else None

def generador_created_at():
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

def generar_correlation_id():
    """Genera un Correlation ID único en formato GUID."""
    return str(uuid.uuid4())

## Notas:
### estado TEXT CHECK (estado IN ('activa','revocada')): asegura que solo se guarde uno de esos dos valores.
### idem_key TEXT UNIQUE: garantiza la idempotencia (si reintentan con la misma key, no se duplica).

