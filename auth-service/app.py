# Iniciamos codigo base p/ levantar servidor
from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
from pathlib import Path
import sqlite3
from helpers import hash_password, verificar_password, sign_jwt, verificar_jwt, extraer_bearer
import jwt

# cargar el .env desde la raíz del proyecto
load_dotenv()

app = Flask(__name__)
PUERTO_AUTH = os.getenv("AUTH_PORT")
DB_PATH = os.getenv("AUTH_DB_PATH")
JWT_SECRET = os.getenv("SECRET_TOKEN")   # Clave secreta para firmar JWT
JWT_ALG = os.getenv("JWT_ALG")
JWT_TTL = int(os.getenv("JWT_TTL"))  # tiempo de vida del token (3600 seg)

#body = { "user1": {"email":"jimena@example.com", "password":"generate_password_hash(password)"}}

# LOGICA DB
def get_conn():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def iniciar_db():
    with get_conn() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT DEFAULT 'user',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP)
        """)
        conn.commit()
iniciar_db()

# Endpoints
# 1. Endpoint raíz para verificar que el servicio está corriendo correctamente
@app.route("/")
def inicio():
    return jsonify({"status":"ok"}), 200

# POST /auth/register
@app.route("/auth/register", methods=["POST"])
def register():
    # Cuerpo esperado: {email, password}
    data = request.get_json(silent=True)
    email = data.get("email").strip().lower()
    password = data.get("password")
    # 1- Validar email tiene formato correcto y no esté vacío
    if not email or "@" not in email:
        return jsonify({"error":"email no encontrado como corresponde"}), 403 # Forb
    # 2- Validar que password tenga longitud mínima (ej: 3 caracteres)
    if len(password) < 3:
        return jsonify({"error":"password no puede tener mas de 3 caracteres"}), 403

    # Revisar en DB si ya existe usuario con ese email
    with get_conn() as conn:
        cur = conn.execute("""SELECT id from users WHERE email = ?
        """, (email,))
        row = cur.fetchone()
        # si email ya existe -> 409
        if row:
            return jsonify({"error":"el email ya existe"}), 409 # Conflict
        # si no existe:
        # Hashear el password
        password_hash = hash_password(password)
        # Guardar en DB (email, hash, role="user")
        cur = conn.execute("""INSERT INTO users (email, password_hash) VALUES (?,?)
        """, (email, password_hash))
        conn.commit()
        # Obtener ID generado
        user_id = cur.lastrowid
    # Devolver 201 Created con {"user_id": user_id}
    return jsonify({"user_id":user_id}), 201

body = {"email":"jimena@example.com", "password":"ABC"}

# Cuerpo esperado: {email, password}
# POST /auth/login
@app.route("/auth/login", methods=["POST"])
def login():

    #  Validar que email y password no estén vacíos
    data = request.get_json(silent=True)
    email = data.get("email").strip().lower()
    password = data.get("password")
    if not email or not password:
        return jsonify({"error":"campos incompletos"}), 400
    
    #  Buscar usuario por email en DB
    with get_conn() as conn:
        cur = conn.execute("""SELECT id, password_hash, role FROM users WHERE email = ?
        """, (email,))
        user = cur.fetchone()
    #    * Si no existe → 401 Unauthorized {"code": "BAD_AUTH"}
    if not user:
        return jsonify({"error":"cliente desconocido, user no existe"}), 401

    #  Verificar password ingresado contra el hash guardado
    #    * Si no coincide → 401 Unauthorized
    if not verificar_password(password, user["password_hash"]):
        return jsonify({"error":"cliente desconocido, password no coincide"}), 401
    
    # Si coincide:
    # * Crear claims: {sub: user_id, role: user_role}
    claims = {"sub": str(user["id"]), "role": user["role"]}
    # * Firmar JWT con secret, algoritmo y TTL
    token = sign_jwt(claims, JWT_SECRET, JWT_ALG, JWT_TTL)
    # * Devolver 200 OK con:
    #   {access_token: token, token_type: "Bearer", expires_in: TTL}
    return jsonify({"access_token": token, "token_type": "Bearer", "expires_in": JWT_TTL}), 200



# GET /auth/me
@app.route("/auth/me", methods=["GET", "POST"])
def my_perfil():
    # Requiere encabezado: Authorization: Bearer <token>
    auth = request.headers.get("Authorization")
    # Extraer token con extract_bearer
    #  * Si no existe → 401 Unauthorized
    token = extraer_bearer(auth)
    if not token:
        return jsonify({"error": "cliente no autorizado"}), 401

    # Verificar token con verify_jwt
    try:
        # claims = verify_jwt(token, ENV.JWT_SECRET, ENV.JWT_ALG, leeway=30)
        claims = verificar_jwt(token,JWT_SECRET,JWT_ALG,leeway_sec=30)
    #  * Si inválido o expirado → 401 Unauthorized
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "El token ha expirado"}), 401
    except jwt.InvalidSignatureError:
        return jsonify({"error": "Firma no valida"}), 401
    except jwt.InvalidTokenError as e:
        return jsonify({"error": "Token invalido", "detail": str(e)}), 401
    # Si valido, retornar mensaje + 200:
    return jsonify({"status":"ok","user_id": claims.get("sub"), "role": claims.get("role")}), 200

if __name__ == "__main__":
    app.run(debug=True, port=PUERTO_AUTH)

###############################################################################################################################################
