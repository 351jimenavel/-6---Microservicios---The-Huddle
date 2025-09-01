# Iniciamos codigo base p/ levantar servidor
from flask import Flask, request, jsonify

app = Flask(__name__)
PUERTO_RANKING = 8004

# Endpoint raíz para verificar que el servicio está corriendo correctamente
@app.route("/")
def inicio():
    return jsonify({"status":"ok"}), 200

if __name__ == "__main__":
    app.run(debug=True, port=PUERTO_RANKING)