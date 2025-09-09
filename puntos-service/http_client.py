"""
CLIENTE INTERNO S2S
"""
import os
import requests
import time

EVENTOS_BASE_URL = os.getenv("EVENTOS_BASE_URL")
INTERNAL_TOKEN   = os.getenv("INTERNAL_TOKEN")

def consultar_eventos_service(evento_id):
    # Headers alineados a al endpoint
    headers = {
        "Authorization": f"Bearer {INTERNAL_TOKEN}",
    }

    url = f"{EVENTOS_BASE_URL}/eventos/{evento_id}"
    delays = [0, 0.2, 0.5, 1.0]  # intento inicial + reintentos con backoff

    for delay in delays:
        if delay:
            time.sleep(delay)

        try:
            resp = requests.get(url, headers=headers, timeout=2)
        except requests.exceptions.RequestException:
            # Error de red/timeout -> reintentar en la proxima iteración
            continue

        # 200 OK -> intentar parsear JSON
        if resp.status_code == 200:
            try:
                data = resp.json()
            except Exception:
                # Respuesta no parseable -> tratar como fallo temporal y reintentar
                continue
            return {"ok": True, "data": data}

        # 404 -> no reintentar ya que no existe
        if resp.status_code == 404:
            return {"ok": False, "status": 404}

        # 5xx -> reintentar (posible problema temporal del servicio)
        if 500 <= resp.status_code < 600:
            continue

        # Otros codigos (401/403/400...) -> fallo definitivo
        return {"ok": False, "status": resp.status_code}

    # Agotó reintentos
    return {"ok": False, "status": 503}     # Después de los 4 intentos, si nunca obtuvo una respuesta valida, devuelve 503 Service Unavailable.
