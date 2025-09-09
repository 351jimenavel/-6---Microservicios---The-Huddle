# jwt_helper.py
import os
import jwt
from flask import request, jsonify
from datetime import datetime, timezone, timedelta

JWT_SECRET = os.getenv("SECRET_TOKEN", "cambia-en-.env")
JWT_ALG = os.getenv("JWT_ALG", "HS256")

def extract_bearer(auth_header):
    pref = "Bearer "
    if not auth_header or not auth_header.startswith(pref):
        return None
    return auth_header[len(pref):].strip()

def validar_jwt_o_401():
    """
    - Extrae Authorization: Bearer <token>
    - Verifica firma/exp
    - Devuelve (claims, None) si OK
    - Devuelve (None, resp_401) si falla
    """
    auth = request.headers.get("Authorization")
    token = extract_bearer(auth)
    if not token:
        return None, jsonify({"error": "no autorizado"}), 401
    try:
        claims = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG], leeway=30)
        return claims, None, None
    except jwt.ExpiredSignatureError:
        return None, jsonify({"error": "token expirado"}), 401
    except jwt.InvalidSignatureError:
        return None, jsonify({"error": "firma inválida"}), 401
    except jwt.InvalidTokenError:
        return None, jsonify({"error": "token inválido"}), 401
