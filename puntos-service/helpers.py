'''
Archivo para funciones varias - puntos service
'''
from flask import request, jsonify
import os
from dotenv import load_dotenv
from datetime import datetime, timezone
import sqlite3
import uuid

load_dotenv()

# Funcion para Autenticacion de Token (Cliente externo)
TOKEN_SECRETO = os.getenv("SECRET_TOKEN")
def validar_token():
    auth = request.headers.get("Authorization", "")
    prefijo = "Bearer "
    if not auth or not auth.startswith(prefijo):
        return jsonify({"error":"Cliente desconocido"}), 401
    if auth.split(" ",1)[1] != TOKEN_SECRETO:
        return jsonify({"error":"Cliente desconocido"}), 401    # Unauthorized
    return None

def crear_db(DB_PATH):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS transacciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            evento_id INTEGER NOT NULL,
            puntos INTEGER NOT NULL, 
            created_at TEXT NOT NULL, 
            estado TEXT CHECK (estado IN ('activa','revocada')) DEFAULT 'activa'
        );""")
        conn.commit()
## Notas:
### estado TEXT CHECK (estado IN ('activa','revocada')): asegura que solo se guarde uno de esos dos valores.

def insertar_transaccion(user_id, evento_id, puntos, created_at, DB_PATH):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            "INSERT INTO transacciones (user_id, evento_id, puntos, created_at, estado) VALUES (?,?,?,?, 'activa')",
            (user_id, evento_id, puntos, created_at),
        )
        conn.commit()
        return cur.lastrowid

def generar_created_at():
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")





############################################################################################################################################
def generar_correlation_id():
    """Genera un Correlation ID único en formato GUID."""
    # Es un ID único que acompaña a una petición mientras viaja por todos tus servicios.
    return str(uuid.uuid4())    #uuid4() = identificador único aleatorio.

def listar_por_user(user_id, estado,DB_PATH):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        if estado in ("activa","revocada"):
            cur = conn.execute(
                "SELECT * FROM transacciones WHERE user_id = ? AND estado = ? ORDER BY id DESC",
                (user_id, estado),
            )
        else:
            cur = conn.execute(
                "SELECT * FROM transacciones WHERE user_id = ? ORDER BY id DESC",
                (user_id,),
            )
        rows = cur.fetchall()
        return [dict(r) for r in rows]

def revocar_transaccion(tx_id, DB_PATH):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute("UPDATE transacciones SET estado='revocada' WHERE id = ?", (tx_id,))
        conn.commit()
        return cur.rowcount  # 1 si actualizó, 0 si no existía

