'''
Archivo para funciones varias
'''
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone, timedelta
import jwt

# FUNC hash_password(password)
def hash_password(password):
    return generate_password_hash(password)

# FUNC verify_password(password, hash_guardado)
def verificar_password(password, hash_guardado):
    return check_password_hash(hash_guardado, password)
    
# FUNC sign_jwt(claims, secret, alg, exp_sec)
def sign_jwt(claims, secret_key, algoritmo, exp_seconds):
    #  Obtener hora actual (now)
    
    hora_actual = datetime.now(timezone.utc)
    expirado_at = hora_actual + timedelta(seconds=exp_seconds) 
    #  Crear payload con:
    payload = {
        # **claims para desempaquetar un diccionario dentro de otro (ej: {sub: user_id, role: "user"})
        **claims,
        # JWT reconoce exp, iat, nbf como claims reservadas.
        # issued at = now (momento de emisión)
        "iat":hora_actual,
        # exp = now + exp_seg (momento de expiración)
        "exp": expirado_at
    }
    #  Codificar y firmar con secret y alg
    '''
    *jwt.encode* is a function that takes the payload, secret key, and algorithm to create and sign the JWT, returning the encoded token as a string.
    '''
    #  Devolver token (string)
    return jwt.encode(payload, secret_key, algorithm=algoritmo)
    

# FUNC verify_jwt(token, secret, alg, leeway_sec) -> claims or error
def verificar_jwt(token, secret_key, algoritmo, leeway_sec):
    """
    Devuelve los claims decodificados o lanza excepción jwt.* si es inválido/expirado.
    Deja que app.py capture las excepciones y devuelva 401.
    """
    # "leeway" refers to a grace period allowed for the exp (expiration time) and nbf (not before time) claims. This is useful to account for potential clock skew between the server issuing the JWT and the server verifying it.
    try:
        # Decodificar token con secret y algoritmo
        print("Token verificado exitosamente")
        return jwt.decode(token, secret_key, algorithms=[algoritmo], leeway=leeway_sec)
    # Validar firma y expiración
    except Exception as e:
    # Cuando se hace raise <error>, el programa “salta” al bloque try/except mas cercano (o crashea si nadie lo captura)
            raise e
    
# --- Extraer Bearer del header Authorization ---
# FUNC extract_bearer(header)
def extraer_bearer(auth_header):
    #  Si auth_header empieza con "Bearer ":
    prefijo = "Bearer "
    if not auth_header or not auth_header.startswith(prefijo):
        # devolver null
        return None
    #  Si no:
    # devolver el token que está después de "Bearer"
    return auth_header[len(prefijo):].strip()