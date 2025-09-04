'''
LOGICA CLIENTE INTERNO S2S
'''
import os
import requests

EVENTOS_BASE_URL = os.getenv("EVENTOS_BASE_URL")
INTERNAL_TOKEN = os.getenv("INTERNAL_TOKEN")

## Helper del cliente interno -- POST/puntos lo llama para consultar si el evento existe dentro de el

def consultar_eventos_service(evento_id , correlation_id):
    header = {"X-Internal-Token": INTERNAL_TOKEN, "X-Correlation-Id": correlation_id}
    response = requests.get(f"{EVENTOS_BASE_URL}/eventos/{evento_id}", headers=header)

    if response:
        return { "ok": True, "data": response }