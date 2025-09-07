# Iniciamos codigo base p/ levantar servidor
from flask import Flask, request, jsonify, g
import os
from dotenv import load_dotenv
from helpers import (
    validar_token, crear_db, buscar_por_idem_key, insertar_transaccion,
    generador_created_at, generar_correlation_id, listar_por_user, revocar_transaccion
)
from http_client import consultar_eventos_service

load_dotenv()

app = Flask(__name__)
PUERTO_PUNTOS = int(os.getenv("PUNTOS_PORT"))
DB_PATH = os.getenv("PUNTOS_DB_PATH")
EVENTOS_BASE_URL = os.getenv("EVENTOS_BASE_URL")
# --- init DB al arrancar (idempotente)
crear_db()

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

    # Validacion de autenticacion (cliente externo)
    error = validar_token()
    if error:
        return error
    
    # Correlation ID (propagar o generar)
    correlation_id = request.headers.get('X-Correlation-Id') 
    if not correlation_id:
        correlation_id = generar_correlation_id()
    """
    Generates or retrieves a correlation ID for the incoming request.
    If 'X-Correlation-ID' header is present, it uses that; otherwise,
    it generates a new UUID.
    """
    #g.correlation_id = correlation_id  # Store in Flask's global request context
    
    # Validacion Idempotency-Key
    idem_key = request.headers.get("Idempotency-Key")
    if not idem_key:
        return jsonify({"error":"falta Idempotency-Key"}), 422
    
    # Si el token es valido
    body = request.get_json(silent=True)
    if body is None:
        return jsonify({"error":"json inválido"}), 400      # Bad Request
    
    # Validacion body
    user_id = body.get("user_id")
    evento_id = body.get("evento_id")
    puntos = body.get("puntos")

    if not user_id or not isinstance(user_id, int) or not evento_id or not isinstance(evento_id, int) or not puntos or not isinstance(puntos, int):
            return jsonify({"error": "faltan campos o tipos inválidos"}), 422
    
    # Idempotencia: si ya existe la transacción con esa key, devolver la misma respuesta (201)
    existente = buscar_por_idem_key(idem_key)
    if existente:
        return jsonify({
            "id": existente["id"],
            "user_id": existente["user_id"],
            "evento_id": existente["evento_id"],
            "puntos": existente["puntos"],
            "created_at": existente["created_at"],
            "estado": existente["estado"],
        }), 201

    # Llamar al helper del cliente interno (dentro del archivo http_client) para consultar el evento
    existe_evento = consultar_eventos_service(evento_id, correlation_id)
    # Si el evento existe, sigue con la lógica (insertar transacción, idempotencia, etc.).
    if not existe_evento["ok"]:
        if existe_evento("status") == 404:
            return jsonify({"error": "evento no encontrado"}), 404
        return jsonify({"error": "eventos no disponible"}), 500

    evento = existe_evento["data"]
    puntos_final = puntos if isinstance(puntos, int) else int(evento.get("puntos_base", 0))

    created_at = generador_created_at()

    # Insertar transacción (manejar UNIQUE en idem_key por carrera)
    try:
        tx_id = insertar_transaccion(user_id, evento_id, puntos_final, created_at, idem_key)
    except Exception:
        existente = buscar_por_idem_key(idem_key)
        if existente:
            return jsonify({
                "id": existente["id"],
                "user_id": existente["user_id"],
                "evento_id": existente["evento_id"],
                "puntos": existente["puntos"],
                "created_at": existente["created_at"],
                "estado": existente["estado"],
            }), 201
        return jsonify({"error": "db error"}), 500

    return jsonify({
        "id": tx_id,
        "user_id": user_id,
        "evento_id": evento_id,
        "puntos": puntos_final,
        "created_at": created_at,
        "estado": "activa",
    }), 201

# Endpoint para listar puntos sin filtros (Aun decidiendo si hacer o no)

# Endpoint para mostrar historial de transacciones de un usuario.
# Historial por usuario (simple)
@app.route("/puntos/user/<user_id>", methods=["GET"])
def puntos_por_user(user_id):
    # Auth
    error = validar_token()
    if error:
        return error
    estado = request.args.get("estado")
    rows = listar_por_user(user_id, estado)
    return jsonify({"data": rows}), 200

# Endpoint para revocar puntos a un usuario (Ej: se asigno por el error los puntos)
@app.route("/puntos/<tx_id>", methods=["DELETE"])
def revocar_puntos(tx_id):
    # Auth
    error = validar_token()
    if error:
        return error
    _ = revocar_transaccion(tx_id)
    # Idempotente: devolver 204 aunque ya estuviera revocada o no exista
    return ("", 204)

if __name__ == "__main__":
    app.run(debug=True, port=PUERTO_PUNTOS)