# Iniciamos codigo base p/ levantar servidor
from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
from helpers import validar_token

load_dotenv()

app = Flask(__name__)
PUERTO_EVENTOS = 8002
TOKEN_SECRETO = os.getenv("SECRET_TOKEN")

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

# Endpoint para crear eventos (POST), listar eventos (GET) o detallar un evento (GET + id del evento)
@app.route("/eventos", methods=["GET", "POST"])
def eventos():

    if request.method == "POST":
        error = validar_token()
        if error:
            return error
        
        # Si el token es valido
        data = request.get_json(silent=True)
        if data is None:
            return jsonify({"error":"json inválido"}), 400      # Bad Request
        
        nombre_evento = data.get("nombre")
        puntos_base = data.get("puntos_base")

        if not nombre_evento and not isinstance(puntos_base, int):
            return jsonify({"error": "faltan campos o tipos inválidos"}), 422
        
        print("Nuevo evento creado")
        return jsonify({"evento": nombre_evento, "puntos": puntos_base}), 201

    if request.method == "GET":
        return jsonify({"metodo":"get"}), 200
        # 1- devolver lista de eventos que existen
        # 2- devolver detalle de un evento especifico

if __name__ == "__main__":
    app.run(debug=True, port=PUERTO_EVENTOS)