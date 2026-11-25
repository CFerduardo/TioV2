import pyodbc
import struct
from charset_normalizer import from_bytes
from pathlib import Path


def decode_sql_image(encoded_data):
   
    if isinstance(encoded_data, str):
        try:
            encoded_bytes = bytes.fromhex(encoded_data)
        except ValueError:
            clean_hex = ''.join(c for c in encoded_data if c.lower() in '0123456789abcdef')
            if len(clean_hex) % 2 != 0:
                clean_hex = clean_hex[:-1]  
            encoded_bytes = bytes.fromhex(clean_hex)
    else:
        encoded_bytes = encoded_data
   
    if len(encoded_bytes) > 1 and encoded_bytes[1] == 0:
        decoded_bytes = bytearray()
        skip_pace = 2 
       
        for i in range(len(encoded_bytes) // skip_pace):
            arrindex = i * skip_pace
            if arrindex + 1 >= len(encoded_bytes):
                break
               
            current_byte = encoded_bytes[arrindex]
            next_byte = encoded_bytes[arrindex + 1]
           
            if i % 2 == 0:
                if next_byte != 0:
                    try:
                        transformed = bytes([current_byte, next_byte]).decode('utf-16le').encode('cp1252')
                        decoded_bytes.append(transformed[0])
                    except:
                        decoded_bytes.append(current_byte)
                else:
                    decoded_bytes.append(current_byte)
            else:
                if next_byte != 0:
                    try:
                        transformed = bytes([current_byte, next_byte]).decode('utf-16le').encode('cp1252')
                        decoded_bytes.append(transformed[0])
                    except:
                        decoded_bytes.append(current_byte)
                else:
                    decoded_bytes.append(current_byte)
       
        return bytes(decoded_bytes)
   
    return encoded_bytes  

def save_repaired_image(input_data, output_path):
  
    decoded_data = decode_sql_image(input_data)
   
    try:
        with open(output_path, 'wb') as f:
            f.write(decoded_data)
       
        if decoded_data.startswith(b'\xFF\xD8\xFF'):
            print(f"JPEG válido guardado en {output_path}")
            return True
        else:
            print(f"Datos guardados en {output_path} pero no son JPEG estándar")
            return False
    except IOError as e:
        print(f"Error al guardar archivo: {e}")
        return False

def simple_decode(encoded_data):
   
    if isinstance(encoded_data, str):
        try:
            encoded_bytes = bytes.fromhex(encoded_data)
        except ValueError:
            clean_hex = ''.join(c for c in encoded_data if c.lower() in '0123456789abcdef')
            if len(clean_hex) % 2 != 0:
                clean_hex = clean_hex[:-1]
            encoded_bytes = bytes.fromhex(clean_hex)
    else:
        encoded_bytes = encoded_data
   
    return encoded_bytes[::2]


def encode_sql_image(raw_bytes):
   
    if isinstance(raw_bytes, str):
        try:
            raw_bytes = bytes.fromhex(raw_bytes)
        except ValueError:
            clean_hex = ''.join(c for c in raw_bytes if c.lower() in '0123456789abcdef')
            if len(clean_hex) % 2 != 0:
                clean_hex = clean_hex[:-1]
            raw_bytes = bytes.fromhex(clean_hex)

    return b''.join(bytes((b, 0)) for b in raw_bytes)

def example_encode_and_verify(input_path, output_path_encoded, output_path_decoded):
    with open(input_path, 'rb') as f:
        original = f.read()

    encoded = encode_sql_image(original)
    with open(output_path_encoded, 'wb') as f:
        f.write(encoded)

    repaired = decode_sql_image(encoded)
    with open(output_path_decoded, 'wb') as f:
        f.write(repaired)

    return original == repaired


