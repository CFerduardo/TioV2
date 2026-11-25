import pandas as pd
import pyodbc

def consultar_sede_pos(sede, config, fecha_inicio, fecha_fin, moneda):
    conn_str = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={config['SERVER']};"
        f"DATABASE={config['DATABASE']};"
        f"UID={config['USER']};"
        f"PWD={config['PASS']};"
        f"Connect Timeout=5;"
        f"TrustServerCertificate=yes;"
    )
    
    try:
        with pyodbc.connect(conn_str) as conn:
            query = "EXEC efectividad_pos_usd_ves ?, ?, ?"
            df = pd.read_sql(query, conn, params=(fecha_inicio, fecha_fin, moneda))

        if df.empty:
            return pd.DataFrame([{
                "TIENDA": sede, "ESTADO": "SIN DATOS",
                "Nro_Facturas": 0, "Total_Productos":0, "SubTotal": 0, "Impuestos": 0, "Total": 0, "Promedio_Factura": 0
            }])

        if 'TIENDA' in df.columns:
            df['TIENDA'] = sede
        else:
            df.insert(0, "TIENDA", sede)

        if 'ESTADO' not in df.columns:
            df.insert(1, "ESTADO", "OK")
        else:
            df['ESTADO'] = "OK"
        
        return df

    except Exception as e:
        print(f"Error en sede {sede}: {str(e)}") # Esto te dirá el error real en la consola
        return pd.DataFrame([{
            "TIENDA": sede, "ESTADO": "OFFLINE",
            "Nro_Facturas": 0, "Total_Productos":0, "SubTotal": 0, "Impuestos": 0, "Total": 0, "Promedio_Factura": 0
        }])