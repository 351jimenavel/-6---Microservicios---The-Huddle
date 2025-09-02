'''
Archivo para funciones varias
'''
from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
import sqlite3

load_dotenv()

# Funcion para Autenticacion de Token
TOKEN_SECRETO = os.getenv("SECRET_TOKEN")
def validar_token():
    auth = request.headers.get("Authorization", "")
    prefijo = "Bearer "
    if not auth or not auth.startswith(prefijo) or auth.split(" ",1)[1] != TOKEN_SECRETO:
        return jsonify({"error":"Cliente desconocido"}), 401    # Unauthorized
    return None

def crear_db():
    pass

def poblar_db():
    pass

def consultar_db():
    pass