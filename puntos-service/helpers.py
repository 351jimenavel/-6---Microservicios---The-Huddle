'''
Archivo para funciones varias - puntos service
'''
from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
import sqlite3

load_dotenv()
DB_PATH = "db/transacciones.db"

# Funcion para Autenticacion de Token
TOKEN_SECRETO = os.getenv("SECRET_TOKEN")

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

## Notas:
### estado TEXT CHECK (estado IN ('activa','revocada')): asegura que solo se guarde uno de esos dos valores.
### idem_key TEXT UNIQUE: garantiza la idempotencia (si reintentan con la misma key, no se duplica).

