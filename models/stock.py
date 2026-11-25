from sedes import SERVIDORES_TIENDAS, SQL_SERVER_IMG
import pandas as pd
import pyodbc

#---------------------------------------------------------------------------------------------------------------------------------
def get_nuevas_conex(sucursal: str) -> pyodbc.Connection:
    # 1. Obtener la configuración de la sucursal
    if sucursal == 'CENTRAL':
        config = SQL_SERVER_IMG.get(sucursal)
    else:
        config = SERVIDORES_TIENDAS.get(sucursal)

    if not config:
        raise ValueError(f"No se encontró la configuración de conexión para la sucursal: {sucursal}")

    # 2. Construir la cadena de conexión con los valores dinámicos
    conn_str = (
        r'DRIVER={ODBC Driver 18 for SQL Server};'
        f"SERVER={config['SERVER']};"
        f"DATABASE={config['DATABASE']};"
        f"UID={config['USER']};"
        f"PWD={config['PASS']};"
        r'TrustServerCertificate=yes;' 
    )

    # 3. Conectar y retornar
    try:
        conn = pyodbc.connect(conn_str)
        return conn
    except pyodbc.Error as ex:
        sqlstate = ex.args[0]
        # Levanta un error más descriptivo sobre el fallo de conexión
        raise ConnectionError(f"Fallo de conexión a la Sucursal {sucursal} ({config['SERVER']}): {sqlstate}") from ex
#---------------------------------------------------------------------------------------------------------------------------------
def get_stock_all(numero_sucursal, tienda, depar):
    conn = None
    try:
        conn = get_nuevas_conex(tienda)
        cursor = conn.cursor()

        if tienda == 'IMPORTADORA':
            deposito = '0118'
        else:
            deposito = f'{numero_sucursal}03'

        if tienda == 'IMPORTADORA':
            db = 'VAD10_IMP'
        else:
            db = 'VAD10'
        
        # 2. Construir la consulta
        sql_query = f"""
            SELECT MP.c_Codigo AS Codigo, 
                   MP.c_Descri AS Descri, 
                   ISNULL(MD.n_cantidad, 0) AS Stock,
                   ME.C_DESCRIPCIO AS Departamento
            FROM {db}..MA_DEPOPROD MD
            LEFT JOIN {db}..MA_PRODUCTOS MP
                   ON MD.c_codarticulo = MP.c_Codigo
            INNER JOIN {db}..MA_DEPARTAMENTOS ME 
                   ON MP.c_Departamento = ME.C_CODIGO
            WHERE c_coddeposito = ?
            AND ME.C_DESCRIPCIO = ?
            ORDER BY n_cantidad;
        """
        
        # 3. UNIFICAR los parámetros en una sola lista
        # El primer ? es 'deposito', los demás son los códigos
        parametros = [deposito] + [depar]
        
        # 4. Ejecutar pasando la lista completa
        cursor.execute(sql_query, parametros)
        
        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()
        data = [dict(zip(columns, row)) for row in rows]
        
        return data
            
    except (ValueError, ConnectionError) as e:
        print(f"Error al procesar la sucursal {numero_sucursal}: {e}")
        return None
        
    except Exception as e:
        print(f"Error en la consulta SQL para sucursal {numero_sucursal}: {e}")
        return None
        
    finally:
        if conn:
            conn.close()
#---------------------------------------------------------------------------------------------------------------------------------
def get_departamentos():
    conn = None
    try:
        conn = get_nuevas_conex('CENTRAL')
        cursor = conn.cursor()

        sql_query = """
            SELECT C_CODIGO, C_DESCRIPCIO 
            FROM MA_DEPARTAMENTOS
        """
        
        # 4. Ejecutar pasando la lista completa
        cursor.execute(sql_query)
        
        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()
        data = [dict(zip(columns, row)) for row in rows]
        
        return data
            
    except (ValueError, ConnectionError) as e:
        print(f"Error al procesar: {e}")
        return None
        
    except Exception as e:
        print(f"Error en la consulta SQL: {e}")
        return None
        
    finally:
        if conn:
            conn.close()
