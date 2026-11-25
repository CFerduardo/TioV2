from sedes import SERVIDORES_TIENDAS
from models.codigos_cmp import LCODIGOS_COMPRAS
import pandas as pd
import pyodbc

#---------------------------------------------------------------------------------------------------------------------------------
def get_nuevas_conex(sucursal: str) -> pyodbc.Connection:
    # 1. Obtener la configuración de la sucursal
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
def get_stock(numero_sucursal, tienda):
    conn = None
    try:
        conn = get_nuevas_conex(tienda)
        cursor = conn.cursor()
        
        # 1. Creamos los placeholders (?, ?, ?)
        lista_codigos_placeholder = ', '.join(['?'] * len(LCODIGOS_COMPRAS))

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
                   ISNULL(MD.n_cantidad, 0) AS Stock
            FROM {db}..MA_DEPOPROD MD
            LEFT JOIN {db}..MA_PRODUCTOS MP
                   ON MD.c_codarticulo = MP.c_Codigo
            WHERE c_coddeposito = ?
            AND c_codarticulo IN ({lista_codigos_placeholder})
            ORDER BY n_cantidad;
        """
        
        # 3. UNIFICAR los parámetros en una sola lista
        # El primer ? es 'deposito', los demás son los códigos
        parametros = [deposito] + list(LCODIGOS_COMPRAS)
        
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
def get_stock_impor(tienda):
    conn = None
    try:
        conn = get_nuevas_conex(tienda)
        cursor = conn.cursor()
        
        # 1. Creamos los placeholders (?, ?, ?)
        lista_codigos_placeholder = ', '.join(['?'] * len(LCODIGOS_COMPRAS))

        # 2. Construir la consulta
        sql_query = f"""
            SELECT 'Codigo' AS Codigo,
                   ISNULL(SUM(MD.n_cantidad), 0) AS Stock
            FROM VAD10_IMP..MA_DEPOPROD MD
            WHERE c_coddeposito = '0118'
            AND c_codarticulo IN ({lista_codigos_placeholder});
        """
        
        # 3. UNIFICAR los parámetros en una sola lista
        # El primer ? es 'deposito', los demás son los códigos
        parametros = list(LCODIGOS_COMPRAS)
        
        # 4. Ejecutar pasando la lista completa
        cursor.execute(sql_query, parametros)
        row = cursor.fetchone()
        
        if row and row[1] is not None:  # n_cantidad está en posición 1
            return int(row[1])
        else:
            return 0 
            
    except (ValueError, ConnectionError) as e:
        print(f"Error al procesar {tienda}: {e}")
        return None
        
    except Exception as e:
        print(f"Error en la consulta SQL para {tienda}: {e}")
        return None
        
    finally:
        if conn:
            conn.close()
#---------------------------------------------------
def cantidad():
    numeros = len(LCODIGOS_COMPRAS)
    return numeros
#---------------------------------------------------
def stock_imp():
    cantidad_impor = get_stock_impor('IMPORTADORA')
    return cantidad_impor

#----------------------------------------------------------
#----------------------------------------------------------

def consultar_sede_reposicion(sede, config, inicio, fin, inserts_codigos):

    # Determinar el nombre de la base de datos
    db_name = "VAD10_IMP" if sede == "IMPORTADORA" else "VAD10"
    
    conn_str = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={config['SERVER']};"
        f"DATABASE={db_name};"
        f"UID={config['USER']};"
        f"PWD={config['PASS']};"
        f"Connect Timeout=5;"
        f"TrustServerCertificate=yes;"
    )

    query = f"""
    SET NOCOUNT ON;
    DECLARE @FechaInicio DATETIME = '{inicio}';
    DECLARE @FechaFin DATETIME = '{fin}';
    DECLARE @FiltroCodigos TABLE (codigo VARCHAR(50));
    
    INSERT INTO @FiltroCodigos VALUES {inserts_codigos};

    SELECT 
        '{sede}' AS [Tiendas],
        CAST(SUM(ISNULL(sub.stockActual, 0)) AS INT) AS [Stock Actual],
        CAST(SUM(ISNULL(sub.entradas, 0)) AS INT) AS [Recepciones],
        CAST(SUM(ISNULL(sub.salidas, 0)) AS INT) AS [Salidas (Ventas)],
        CAST(SUM(ISNULL(sub.montoSugerido, 0)) AS INT) AS [Sugerido a Reponer]
    FROM (
        SELECT
            MDP.n_cantidad AS stockActual,
            SUM(CASE WHEN TR.c_tipomov = 'CARGO' THEN TR.n_cantidad ELSE 0 END) AS entradas,
            SUM(CASE WHEN TR.c_tipomov = 'DESCARGO' THEN TR.n_cantidad ELSE 0 END) AS salidas,
            CASE
                WHEN ISNULL(MDP.n_cantidad, 0) < ISNULL(SUM(CASE WHEN TR.c_tipomov = 'DESCARGO' THEN TR.n_cantidad ELSE 0 END), 0) THEN
                    (ISNULL(SUM(CASE WHEN TR.c_tipomov = 'DESCARGO' THEN TR.n_cantidad ELSE 0 END), 0) - (CASE WHEN ISNULL(MDP.n_cantidad, 0) < 0 THEN 0 ELSE ISNULL(MDP.n_cantidad, 0) END)) * 1.2
                WHEN ISNULL(MDP.n_cantidad, 0) <= 0 AND ISNULL(SUM(CASE WHEN TR.c_tipomov = 'DESCARGO' THEN TR.n_cantidad ELSE 0 END), 0) > 0 THEN
                    ISNULL(SUM(CASE WHEN TR.c_tipomov = 'DESCARGO' THEN TR.n_cantidad ELSE 0 END), 0) * 1.2
                ELSE 0
            END AS montoSugerido
        FROM [MA_PRODUCTOS] MP
        LEFT JOIN [MA_DEPOPROD] MDP ON MP.c_codigo = MDP.c_codarticulo
        LEFT JOIN [TR_INVENTARIO] TR ON MP.c_codigo = TR.c_codarticulo
            AND TR.f_fecha BETWEEN @FechaInicio AND @FechaFin
        WHERE MP.c_codigo IN (SELECT codigo FROM @FiltroCodigos)
        GROUP BY MP.c_codigo, MDP.n_cantidad
    ) AS sub;
    """

    try:
        with pyodbc.connect(conn_str) as conn:
            df = pd.read_sql(query, conn)
        
        if df.empty:
            return pd.DataFrame([{
                "Tiendas": sede, "Stock Actual": 0, "Recepciones": 0, 
                "Salidas (Ventas)": 0, "Sugerido a Reponer": 0, "ESTADO": "SIN DATOS"
            }])
        
        df["ESTADO"] = "OK"
        return df

    except Exception as e:
        print(f"Error en sede {sede}: {str(e)}")
        return pd.DataFrame([{
            "Tiendas": sede, "Stock Actual": 0, "Recepciones": 0, 
            "Salidas (Ventas)": 0, "Sugerido a Reponer": 0, "ESTADO": "OFFLINE"
        }])