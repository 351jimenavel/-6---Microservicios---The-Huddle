'''
Archivo para funciones varias
'''
from flask import Flask, request, jsonify
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

def crear_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS eventos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            puntos_base INT NOT NULL, 
            fecha TEXT NOT NULL, 
            activo INT DEFAULT 1
        )""")

        conn.commit()
        
def consultar_db():
    pass


if __name__ == "__main__":
    crear_db()
    print("Seeder OK. DB en:", DB_PATH)