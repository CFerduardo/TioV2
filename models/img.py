from decode_image import decode_sql_image
import base64

def procesar_imagen_para_js(binario):
    if binario:
        try:
            # USAMOS TU LÓGICA VIEJA: Repara los bytes corruptos de SQL Server
            repaired_bytes = decode_sql_image(binario) 
            # Convertimos a base64 puro para que JS lo lea sin problemas
            return base64.b64encode(repaired_bytes).decode('utf-8')
        except Exception as e:
            print(f"Error decodificando imagen: {e}")
            return None
    return None