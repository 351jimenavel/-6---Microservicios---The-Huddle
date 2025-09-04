# Iniciamos codigo base p/ levantar servidor
from flask import Flask, request, jsonify, g
import os
from dotenv import load_dotenv
from helpers import validar_token, crear_db,generador_created_at, generar_correlation_id
import sqlite3
import requests
import uuid
from http_client import consultar_eventos_service

load_dotenv()

app = Flask(__name__)
PUERTO_PUNTOS = 8003
DB_PATH = "db/transacciones.db"
EVENTOS_BASE_URL = os.getenv("EVENTOS_BASE_URL")
# --- init DB al arrancar (idempotente)
crear_db(DB_PATH)

# Endpoint raíz para verificar que el servicio está corriendo correctamente
@app.route("/")
def inicio():
    return jsonify({"service":"puntos","status":"ok"}), 200

'''
FLUJO:
** Cliente asigna puntos a un usuario:

Llama a Puntos Service (POST /puntos + Idempotency-Key).

Puntos valida el token → pide a Eventos Service “¿este evento existe?” usando X-Internal-Token.

Si sí → guarda transacción en DB de puntos.

-------
** Cliente revisa historial:

Llama a Puntos Service (GET /puntos/user/{id}).

-------
** Si hubo error (asignación incorrecta)

Cliente llama a Puntos Service (DELETE /puntos/{tx_id}) → estado “revocada”.

'''


# Endpoint para asignar puntos a un usuario (usa Idempotency-Key para no duplicar).
@app.route("/puntos", methods=["POST"])
def puntos():

    # Validacion de autenticacion
    error = validar_token()
    if error:
        return error
    
    # Si el token es valido
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error":"json inválido"}), 400      # Bad Request
    
    # Validacion Idempotency-Key
    idem_key = request.headers["Idempotency-Key"]
    if not idem_key:
        return jsonify({"error":"falta Idempotency-Key"}), 422

    # Toma o genera un correlation_id
    """
    Generates or retrieves a correlation ID for the incoming request.
    If 'X-Correlation-ID' header is present, it uses that; otherwise,
    it generates a new UUID.
    """
    correlation_id = request.headers.get('X-Correlation-ID') or generar_correlation_id()
    g.correlation_id = correlation_id  # Store in Flask's global request context

    # Llamar al helper del cliente interno (dentro del archivo http_client) para consultar el evento
    existe_evento = consultar_eventos_service(evento_id, correlation_id)
    # Si el evento existe, sigue con la lógica (insertar transacción, idempotencia, etc.).
    if existe_evento:
        pass

    # Ya existe una transacción con esa Idempotency-Key? Consultar a db
    query = "SELECT * FROM transacciones WHERE idem_key = ?"
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute(query, idem_key)
            #conn.execute(query, params)
            row = cur.fetchone()
            return row
    except Exception as e:
        print("DB -idem ERROR:", repr(e))
        return jsonify({"error": "db -idem error"}), 500
    
    if row:
        return jsonify({"data":row}), 201
    else:
        # Verificar que el evento exista en la tabla de eventos de eventos-service
        # Validar el evento contra eventos-service (S2S)
        pass

    #Cuando hacia el llamado a la funcion que esta en helpers
    #if #consultar_por_idem_key(DB_PATH,"SELECT * FROM transacciones WHERE idem_key = ?", idem_key):
    #    return jsonify({"data":})

    
    # Validacion body
    user_id = data.get("user_id")
    evento_id = data.get("evento_id")
    puntos = data.get("puntos")

    if not user_id or not isinstance(user_id, int) or not evento_id or not isinstance(evento_id, int) or not puntos or not isinstance(puntos, int):
            return jsonify({"error": "faltan campos o tipos inválidos"}), 422

    created_at = generador_created_at()
    print("Nueva transaccion ingresada")


    # Insertar transaccion en la db
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.execute("INSERT INTO transacciones (user_id,evento_id,puntos, created_at, estado) VALUES (?,?,?,?,?)",())
            id = cur.lastrowid
    except Exception as e:
            print("DB ERROR:", repr(e))
            return jsonify({"error": "db error"}), 500
    
    return jsonify({"id":id,"user_id": user_id, "evento_id": evento_id, "puntos": puntos_base, "created_at": created_at, "estado": 1}), 201

# Endpoint para mostrar historial de transacciones de un usuario.
@app.route("/puntos/user/<user_id>", methods=["GET"])
def puntos_por_user():
    pass

# Endpoint para revocar puntos a un usuario (Ej: se asigno por el error los puntos)
@app.route("/puntos/<tx_id>", methods=["DELETE"])
def revocar_puntos():
    pass



if __name__ == "__main__":
    app.run(debug=True, port=PUERTO_PUNTOS)