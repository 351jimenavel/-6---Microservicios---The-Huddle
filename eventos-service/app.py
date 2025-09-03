# Iniciamos codigo base p/ levantar servidor
from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
from helpers import validar_token, crear_db, consultar_un_evento
import sqlite3

load_dotenv()

app = Flask(__name__)
PUERTO_EVENTOS = 8002
DB_PATH = "db/eventos.db"
TOKEN_SECRETO = os.getenv("SECRET_TOKEN")
# --- init DB al arrancar (idempotente)
crear_db(DB_PATH)

# Funcion para Autenticacion de Token
# def validar_token():
#     auth = request.headers.get("Authorization", "")
#     prefijo = "Bearer "
#     if not auth or not auth.startswith(prefijo) or auth.split(" ",1)[1] != TOKEN_SECRETO:
#         return jsonify({"error":"Cliente desconocido"}), 401    # Unauthorized

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

        # Validacion de autenticacion
        error = validar_token()
        if error:
            return error
        
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

# Endpoint para devolver detalles de un evento especifico (GET + id de un evento activo)
@app.route("/eventos/<int:evento_id>", methods=["GET"])
def detalle_evento(evento_id):

    # Validacion de autenticacion
    error = validar_token()
    if error:
        return error
    
    query = f"SELECT id, nombre, puntos_base, fecha, activo FROM eventos WHERE id = ? AND activo = 1"
    row = consultar_un_evento(
        DB_PATH,
        query,
        (evento_id,)
    )
    print({'Evento ID': f'{evento_id}'})

    if not row:
        return jsonify({"error": "evento no encontrado"}), 404
    
    return jsonify(row), 200
        
if __name__ == "__main__":
    app.run(debug=True, port=PUERTO_EVENTOS)