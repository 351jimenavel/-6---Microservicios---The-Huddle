# Iniciamos codigo base p/ levantar servidor
from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
from pathlib import Path
from helpers import crear_db, consultar_un_evento
from jwt_helper import validar_jwt_o_401
import sqlite3

# cargar el .env desde la raíz del proyecto
load_dotenv()

app = Flask(__name__)
PUERTO_EVENTOS = os.getenv("EVENTOS_PORT")
DB_PATH = os.getenv("EVENTOS_DB_PATH")
TOKEN_SECRETO = os.getenv("SECRET_TOKEN")
INTERNAL_TOKEN = os.getenv("INTERNAL_TOKEN")
# --- init DB al arrancar (idempotente)
crear_db(DB_PATH)

# Endpoint raíz para verificar que el servicio está corriendo correctamente
@app.route("/")
def inicio():
    return jsonify({
        "service":"eventos",
        "status":"ok"}), 200

# Endpoint para crear eventos (POST), listar eventos (GET) o realizar filtros (GET)
@app.route("/eventos", methods=["GET","POST"])
def crear_evento():

    ## logica METODO GET
    if request.method == "GET":
        args = request.args
        params = []

        activo_string = args.get("activo")
        query = "SELECT * FROM eventos WHERE 1=1"
        ## Filtro opcional (por evento activo o no activo (1 o 0))
        if activo_string and (activo_string == "0" or activo_string == "1"):
            activo = int(activo_string)
            query += " AND activo = ?"
            params.append(activo)
        else:
            return jsonify({"error":"activo debe ser 0 o 1"}), 422
        
        query += " ORDER BY id DESC"

        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row       # row_factory permite convertir filas a dict fácilmente.
            cur  = conn.execute(query, params)
            rows = cur.fetchall()

        # Serializamos filas a lista de dicts apta para jsonify
        response = []
        for r in rows:
            response.append(dict(r))

        return jsonify({"data":response}), 200

    ## logica METODO POST
    if request.method == "POST":

        claims, err_resp, err_code = validar_jwt_o_401()
        if err_resp:
            return err_resp, err_code
        
        # Si el token es valido
        data = request.get_json(silent=True)

        if data is None:
            return jsonify({"error":"json inválido"}), 400      # Bad Request
        
        nombre_evento = data.get("nombre")
        puntos_base = data.get("puntos_base")
        fecha = data.get("fecha")

        if not nombre_evento or not isinstance(puntos_base, int):
            return jsonify({"error": "faltan campos o tipos inválidos"}), 422   # Entidad no procesable
        
        print("Nuevo evento creado")
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cur = conn.execute(
                    "INSERT INTO eventos (nombre, puntos_base, fecha) VALUES (?,?,?)",
                    (nombre_evento, puntos_base, fecha)
                )
                evento_id = cur.lastrowid
        except Exception as e:
            print("DB ERROR:", repr(e))
            return jsonify({"error": "db error"}), 500
        
        return jsonify({"id":evento_id,"evento": nombre_evento, "puntos": puntos_base, "fecha":fecha, "activo": 1}), 201

# Endpoint para devolver detalles de un evento especifico (GET + id de un evento)
@app.route("/eventos/<int:evento_id>", methods=["GET"])
def detalle_evento(evento_id):

    # 1) Requerir Bearer <TOKEN_SERVICIO>
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify({"error": "credencial requerida"}), 401
    
    token = auth_header.split(" ", 1)[1]
    if token != INTERNAL_TOKEN:   # el mismo que usa Puntos Service
        return jsonify({"error": "token inválido"}), 403

    # 2) Consultar evento en DB
    query = f"SELECT id, activo FROM eventos WHERE id = ?"
    row = consultar_un_evento(
        DB_PATH,
        query,
        (evento_id,)
    )

    if not row:
        return jsonify({"error": "evento no encontrado"}), 404
    
    return jsonify(row), 200
        
if __name__ == "__main__":
    app.run(debug=True, port=PUERTO_EVENTOS)


############################################################################################################################