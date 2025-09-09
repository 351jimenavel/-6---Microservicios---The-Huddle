# Iniciamos codigo base p/ levantar servidor
from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
from helpers import (crear_db, insertar_transaccion, generar_created_at, listar_por_user, revocar_transaccion)
from http_client import consultar_eventos_service
from jwt_helper import validar_jwt_o_401

load_dotenv()

app = Flask(__name__)

PUERTO_PUNTOS = int(os.getenv("PUNTOS_PORT"))
DB_PATH = os.getenv("PUNTOS_DB_PATH")
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

Llama a Puntos Service (POST /puntos).

Puntos valida el token → pide a Eventos Service “¿este evento existe?” usando X-Internal-Token.

Si sí → guarda transacción en DB de puntos.

'''

# Endpoint para asignar puntos a un usuario.
@app.route("/puntos", methods=["POST"])
def asignar_puntos():

    # 1) Auth (JWT)
    claims, err_resp, err_code = validar_jwt_o_401()
    if err_resp:
        return err_resp, err_code
    
    # 3) Body
    # Validacion body
    body = request.get_json(silent=True)
    if body is None:
        return jsonify({"error":"json invalido"}), 400      # Bad Request
    
    evento_id = body.get("evento_id")
    puntos = body.get("puntos")
    
    # 4) user_id desde JWT (sub)
    user_id = claims.get("sub") # user_id REAL tomado del JWT
    if not user_id:
        return jsonify({"error": "token sin 'sub' (user_id)"}), 401
    try:
        user_id_int = int(user_id)
    except ValueError:
        return jsonify({"error": "user_id invalido"}), 422

    # 5) Validaciones mínimas
    if evento_id is None:
        return jsonify({"error": "evento_id requerido"}), 400
    if not isinstance(evento_id, int):
        return jsonify({"error": "evento_id debe ser int"}), 422
    
    if puntos is not None:
        if not isinstance(puntos, int) or puntos < 0:
            return jsonify({"error": "puntos invalidos"}), 400
    
    # 6) Consultar evento en Eventos Service
    # Llamar al helper del cliente interno (dentro del archivo http_client) para consultar el evento
    existe_evento = consultar_eventos_service(evento_id)
    # Si el evento existe, sigue con la lógica (insertar transacción, idempotencia, etc.).
    if not existe_evento.get("ok"):
        if existe_evento.get("status") == 404:
            return jsonify({"error": "evento no encontrado"}), 404
        return jsonify({"error": "eventos no disponible"}), 500

    evento = existe_evento["data"]

    # 7) Definir puntos_final (si no vino en body, usar puntos_base del evento)
    if puntos is None:
        puntos_final = int(evento.get("puntos_base", 0))
    else:
        puntos_final = puntos

    # 8) Insertar transacción
    created_at = generar_created_at()

    try:
        tx_id = insertar_transaccion(user_id_int, evento_id, puntos_final, created_at, DB_PATH)
    except Exception:
        return jsonify({"error": "db error"}), 500

    return jsonify({
        "id": tx_id,
        "user_id": user_id,
        "evento_id": evento_id,
        "puntos": puntos_final,
        "created_at": created_at,
        "estado": "activa",
    }), 201


    
#########################################################################
# Endpoint para listar puntos sin filtros (Aun decidiendo si hacer o no)
# Endpoint para mostrar historial de transacciones de un usuario.
# Historial por usuario (simple)
@app.route("/puntos/user/<int:user_id>", methods=["GET"])
def puntos_por_user(user_id):
    # Auth
    claims, err_resp, err_code = validar_jwt_o_401()
    if err_resp:
        return err_resp, err_code
    
    estado = request.args.get("estado")
    rows = listar_por_user(user_id, estado,DB_PATH)
    return jsonify({"data": rows}), 200

# Endpoint para revocar puntos a un usuario (Ej: se asigno por el error los puntos)
@app.route("/puntos/<int:tx_id>", methods=["DELETE"])
def revocar_puntos(tx_id):
    # Auth
    claims, err_resp, err_code = validar_jwt_o_401()
    if err_resp:
        return err_resp, err_code
    
    _ = revocar_transaccion(tx_id, DB_PATH)
    # Idempotente: devolver 204 aunque ya estuviera revocada o no exista
    return ("", 204)

if __name__ == "__main__":
    app.run(debug=True, port=PUERTO_PUNTOS)