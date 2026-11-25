import pyodbc
import pandas as pd
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
from database import DatabaseManager, get_db_connection
from sedes import SERVIDORES_TIENDAS, SQL_SERVER_IMG, TIENDAS_MAP
from models.logic import process_txt_file, analyze_updates
from models.compras import cantidad, stock_imp
from models.tributos import sql_query
from io import BytesIO
import concurrent.futures
import base64
import os

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
    
db = DatabaseManager()

# HISTORICO
# ===================================================================================================
def registrar_log(cedula, nombre, departamento, modulo, accion):
    try:
        if not cedula or not nombre:
            print("⚠️ Intento de log sin datos de usuario")
            return

        conn = get_db_connection()
        cur = conn.cursor()
        query = """
            INSERT INTO historico_actividad (cedula, nombre_usuario, departamento, modulo, accion)
            VALUES (%s, %s, %s, %s, %s)
        """
        cur.execute(query, (cedula, nombre, departamento, modulo, accion))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"⚠️ Error al registrar log de auditoría: {e}")
#--------------------------------------------------------------------------------------------------------------------------------------
@app.route('/re')
def index2():
    return render_template('repos.html')
#--------------------------------------------------------------------------------------------------------------------------------------
@app.route('/tio')
def tio():
    return render_template('stock.html')
#---------------------------------------------------------------------------------------------------------------------------------
@app.route('/compras')
def compras():
    cantidad_codigos = cantidad()
    cantidad_provee = '25'
    stock_codigos = stock_imp()

    return render_template('compras.html', 
                            cantidad_codigos=cantidad_codigos,
                            stock_codigos=stock_codigos,
                            cantidad_provee=cantidad_provee)
#---------------------------------------------------------------------------------------------------------------------------------
@app.route('/')
def index():
    return render_template('login.html')
#--------------------------------------------------------------------------------------------------------------------------------------
@app.route('/dashboard')
def dashboard_view():
    return render_template('dashboard.html')

# ===================================================================================================
# RUTAS DE AUTENTICACIÓN
# ===================================================================================================
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    usuario = data.get('username')
    password = data.get('password')

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT cedula, usuario, departamento FROM usuarios WHERE usuario = %s AND password = %s", (usuario, password))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user:
            return jsonify({
                "success": True, 
                "cedula": user[0], 
                "usuario": user[1], 
                "departamento": user[2]
            })
        else:
            return jsonify({"success": False, "message": "Credenciales inválidas"}), 401
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# ===================================================================================================
# INVENTARIOS
# ===================================================================================================
@app.route('/exportar_yaguara', methods=['GET'])
def exportar_yaguara():
    fecha_inicio = request.args.get('inicio')
    fecha_fin = request.args.get('fin')
    c_user = request.args.get('c_user')
    n_user = request.args.get('n_user')
    d_user = request.args.get('d_user')

    try:
        conn = get_db_connection()
        query = "SELECT * FROM recepciones_yaguara WHERE fecha BETWEEN %s AND %s ORDER BY fecha ASC"
        df = pd.read_sql_query(query, conn, params=(fecha_inicio, fecha_fin))
        conn.close()

        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Recepciones')
        output.seek(0)

        registrar_log(c_user, n_user, d_user, "yaguara", f"Exportó Recepciones Yaguara: {fecha_inicio} a {fecha_fin}")

        return send_file(output, as_attachment=True, download_name=f"Yaguara_{fecha_inicio}.xlsx")
    except Exception as e:
        return jsonify({"error": str(e)}), 500
#--------------------------------------------------------------------------------------------------------------------------------------
@app.route('/exportar_tiendas', methods=['GET'])
def exportar_tiendas():
    fecha_inicio = request.args.get('inicio')
    fecha_fin = request.args.get('fin')
    c_user = request.args.get('c_user')
    n_user = request.args.get('n_user')
    d_user = request.args.get('d_user')

    try:
        conn = get_db_connection()
        query = "SELECT * FROM recepcion_tienda WHERE fecha BETWEEN %s AND %s ORDER BY fecha ASC"
        df = pd.read_sql_query(query, conn, params=(fecha_inicio, fecha_fin))
        conn.close()

        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Recepcion_Tiendas')
        output.seek(0)

        registrar_log(c_user, n_user, d_user, "recepcion_tiendas", f"Exportó Recepción Tiendas: {fecha_inicio} a {fecha_fin}")

        return send_file(output, as_attachment=True, download_name=f"Tiendas_{fecha_inicio}.xlsx")
    except Exception as e:
        return jsonify({"error": str(e)}), 500
#--------------------------------------------------------------------------------------------------------------------------------------
@app.route('/exportar_inventario', methods=['GET'])
def exportar_inventario():
    from models.inv import query_inv

    tienda_id = request.args.get('tienda')
    inicio = request.args.get('inicio').replace('-', '')
    fin = request.args.get('fin').replace('-', '')
    c_user = request.args.get('c_user')
    n_user = request.args.get('n_user')
    d_user = request.args.get('d_user')

    config = SERVIDORES_TIENDAS.get(tienda_id)
    if not config: return jsonify({"error": "Tienda no configurada"}), 400

    try:
        conn_str = (f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={config['SERVER']};"
            f"DATABASE={config['DATABASE']};"
            f"UID={config['USER']};"
            f"PWD={config['PASS']};"
            f"Connect Timeout=10;"
            f"TrustServerCertificate=yes;")
        
        with pyodbc.connect(conn_str) as conn:
            df = pd.read_sql(query_inv, conn, params=(inicio, fin))

        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Inventario')
        output.seek(0)

        registrar_log(c_user, n_user, d_user, "inventario_tienda", f"Exportó Inventario {tienda_id}")

        return send_file(output, as_attachment=True, download_name=f"Inventario_{tienda_id}.xlsx")

    except pyodbc.OperationalError:
        return jsonify({"error": f"La sede {tienda_id} está fuera de línea o el servidor no responde."}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500
#--------------------------------------------------------------------------------------------------------------------------------------
@app.route('/exportar_reposicion', methods=['GET'])
def exportar_reposicion():
    tienda_id = request.args.get('tienda')
    inicio = request.args.get('inicio')
    fin = request.args.get('fin')
    c_user = request.args.get('c_user')
    n_user = request.args.get('n_user')
    d_user = request.args.get('d_user')

    config = SERVIDORES_TIENDAS.get(tienda_id)
    if not config: return jsonify({"error": "Configuración de sede no encontrada"}), 400

    if tienda_id == 'IMPORTADORA':
        db_name = 'VAD10_IMP'
    else:
        db_name = 'VAD10'

    query = f"""
        SET NOCOUNT ON;

        DECLARE @FechaInicio DATETIME = '{inicio.replace("-", "")}'; 
        DECLARE @FechaFin DATETIME = '{fin.replace("-", "")}';    

        IF OBJECT_ID('tempdb..#Resultados') IS NOT NULL DROP TABLE #Resultados;
        CREATE TABLE #Resultados (
            codigo VARCHAR(50),
            descripcion VARCHAR(255),
            tienda VARCHAR(255),
            departamento VARCHAR(50),
            stockActual DECIMAL(18, 2),
            entradas DECIMAL(18, 2),
            salidas DECIMAL(18, 2),
            sugerirReposicion VARCHAR(50),
            montoSugerido DECIMAL(18, 2),
            dias INT
        );

        -- 2. Insertamos directamente usando la base de datos que ya identificamos en Python
        INSERT INTO #Resultados
        SELECT codigo, descripcion, tienda, departamento, stockActual, entradas, salidas, sugerirReposicion, montoSugerido, dias
        FROM (
            SELECT 
                MDP.c_codarticulo AS [codigo],
                MP.C_DESCRI AS [descripcion],
                LTRIM(RTRIM(REPLACE(REPLACE(MD.c_descripcion, 'piso de venta', ''), 'PISO DE VENTA', ''))) AS [tienda],
                -- Usamos COALESCE para el departamento por si la columna no existe o es NULL
                ISNULL(MP.c_Departamento, 'GENERAL') AS [departamento],
                MDP.n_cantidad AS [stockActual],
                ISNULL(SUM(CASE WHEN TR.c_tipomov = 'CARGO' THEN TR.n_cantidad ELSE 0 END), 0) AS [entradas],
                ISNULL(SUM(CASE WHEN TR.c_tipomov = 'DESCARGO' THEN TR.n_cantidad ELSE 0 END), 0) AS [salidas],
                CASE 
                    WHEN MDP.n_cantidad <= 0 AND ISNULL(SUM(CASE WHEN TR.c_tipomov = 'DESCARGO' THEN TR.n_cantidad ELSE 0 END), 0) > 0 THEN 'Agotado'
                    WHEN MDP.n_cantidad < ISNULL(SUM(CASE WHEN TR.c_tipomov = 'DESCARGO' THEN TR.n_cantidad ELSE 0 END), 0) THEN 'Stock Bajo'
                    WHEN MDP.n_cantidad < (ISNULL(SUM(CASE WHEN TR.c_tipomov = 'DESCARGO' THEN TR.n_cantidad ELSE 0 END), 0) * 1.3) THEN 'Sugerir Reposición Preventiva'
                    ELSE 'No Sugerir Reposición'
                END AS [sugerirReposicion],
                CASE 
                    WHEN MDP.n_cantidad < ISNULL(SUM(CASE WHEN TR.c_tipomov = 'DESCARGO' THEN TR.n_cantidad ELSE 0 END), 0) THEN 
                        (ISNULL(SUM(CASE WHEN TR.c_tipomov = 'DESCARGO' THEN TR.n_cantidad ELSE 0 END), 0) - (CASE WHEN MDP.n_cantidad < 0 THEN 0 ELSE MDP.n_cantidad END)) * 1.2
                    WHEN MDP.n_cantidad <= 0 AND ISNULL(SUM(CASE WHEN TR.c_tipomov = 'DESCARGO' THEN TR.n_cantidad ELSE 0 END), 0) > 0 THEN 
                        ISNULL(SUM(CASE WHEN TR.c_tipomov = 'DESCARGO' THEN TR.n_cantidad ELSE 0 END), 0) * 1.2
                    ELSE 0
                END AS [montoSugerido],
                DATEDIFF(DAY, @FechaInicio, @FechaFin) + 1 AS [dias]
            -- Usamos la variable {db_name} de Python directamente
            FROM [{db_name}].[dbo].[MA_DEPOPROD] MDP
            LEFT JOIN [{db_name}].[dbo].[TR_INVENTARIO] TR ON MDP.c_codarticulo = TR.c_codarticulo 
                AND TR.f_fecha BETWEEN @FechaInicio AND @FechaFin
            INNER JOIN [{db_name}].[dbo].[MA_PRODUCTOS] MP ON MDP.c_codarticulo = MP.c_codigo
            INNER JOIN [{db_name}].[dbo].[MA_DEPOSITO] MD ON MDP.c_coddeposito = MD.c_coddeposito
            GROUP BY MDP.c_codarticulo, MP.C_DESCRI, MP.c_Departamento, MD.c_descripcion, MDP.n_cantidad
        ) AS SubConsulta
        WHERE sugerirReposicion IN ('Agotado', 'Stock Bajo', 'Sugerir Reposición Preventiva');

        -- 3. Resultado final con limpieza de decimales
        SELECT 
            codigo, descripcion, tienda, departamento, 
            CAST(ROUND(stockActual, 0) AS INT) AS [stockActual], 
            CAST(ROUND(entradas, 0) AS INT) AS [entradas], 
            CAST(ROUND(salidas, 0) AS INT) AS [salidas], 
            sugerirReposicion, 
            CAST(ROUND(montoSugerido, 0) AS INT) AS [montoSugerido], 
            dias 
        FROM #Resultados 
        ORDER BY salidas DESC;

        DROP TABLE #Resultados;
        """

    try:
        conn_str = (f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={config['SERVER']};"
            f"DATABASE={config['DATABASE']};"
            f"UID={config['USER']};"
            f"PWD={config['PASS']};"
            f"Connect Timeout=10;"
            f"TrustServerCertificate=yes;")
        
        with pyodbc.connect(conn_str) as conn:
            df = pd.read_sql(query, conn)

        if df.empty:
            return jsonify({"error": "No hay datos de reposición"}), 404

        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Reposicion')
        output.seek(0)

        registrar_log(c_user, n_user, d_user, "reposicion", f"Exportó Sugerido Reposición {tienda_id}")

        return send_file(output, as_attachment=True, download_name=f"Reposicion_{tienda_id}.xlsx")

    except Exception as e:
        print(f"Error en {tienda_id} ({db_name}): {str(e)}") 
        return jsonify({"error": str(e)}), 500
    
# ===================================================================================================
# COMPRA
# ===================================================================================================
@app.route("/reposicion_compras", methods=["GET"])
def reposicion_compras():
    tienda_id = request.args.get("tienda")
    inicio = request.args.get("inicio").replace("-", "")
    fin = request.args.get("fin").replace("-", "")
    c_user = request.args.get("c_user")
    n_user = request.args.get("n_user")
    d_user = request.args.get("d_user")

    config = SERVIDORES_TIENDAS.get(tienda_id)
    if not config:
        return jsonify({"error": "Sede no encontrada"}), 400

    db_name = "VAD10_IMP" if tienda_id == "IMPORTADORA" else "VAD10"

    try:
        from models.compras import LCODIGOS_COMPRAS
        inserts_codigos = ",\n".join([f"('{c}')" for c in LCODIGOS_COMPRAS])
    except ImportError:
        return jsonify({"error": "No se pudo cargar la lista de códigos de compras"}), 500

    query = f"""
    SET NOCOUNT ON;
    DECLARE @FechaInicio DATETIME = '{inicio}';
    DECLARE @FechaFin DATETIME = '{fin}';
    DECLARE @FiltroCodigos TABLE (codigo VARCHAR(50));
    
    INSERT INTO @FiltroCodigos VALUES
    {inserts_codigos};

    IF OBJECT_ID('tempdb..#Resultados') IS NOT NULL DROP TABLE #Resultados;
    CREATE TABLE #Resultados (
        codigo VARCHAR(50),
        descripcion VARCHAR(255),
        departamento VARCHAR(100),
        stockActual DECIMAL(18, 2),
        entradas DECIMAL(18, 2),
        salidas DECIMAL(18, 2),
        sugerirReposicion VARCHAR(50),
        montoSugerido DECIMAL(18, 2),
        dias INT
    );

    INSERT INTO #Resultados
    SELECT codigo, descripcion, departamento, stockActual, entradas, salidas, sugerirReposicion, montoSugerido, dias
    FROM (
        SELECT
            MP.c_codigo AS [codigo],
            MP.c_descri AS [descripcion],
            ISNULL(D.C_DESCRIPCIO, 'GENERAL') AS [departamento],
            ISNULL(MDP.n_cantidad, 0) AS [stockActual],
            ISNULL(SUM(CASE WHEN TR.c_tipomov = 'CARGO' THEN TR.n_cantidad ELSE 0 END), 0) AS [entradas],
            ISNULL(SUM(CASE WHEN TR.c_tipomov = 'DESCARGO' THEN TR.n_cantidad ELSE 0 END), 0) AS [salidas],
            CASE
                WHEN ISNULL(MDP.n_cantidad, 0) <= 0 AND ISNULL(SUM(CASE WHEN TR.c_tipomov = 'DESCARGO' THEN TR.n_cantidad ELSE 0 END), 0) > 0 THEN 'Agotado'
                WHEN ISNULL(MDP.n_cantidad, 0) < ISNULL(SUM(CASE WHEN TR.c_tipomov = 'DESCARGO' THEN TR.n_cantidad ELSE 0 END), 0) THEN 'Stock Bajo'
                WHEN ISNULL(MDP.n_cantidad, 0) < (ISNULL(SUM(CASE WHEN TR.c_tipomov = 'DESCARGO' THEN TR.n_cantidad ELSE 0 END), 0) * 1.3) THEN 'Sugerir Reposición Preventiva'
                ELSE 'No Sugerir Reposición'
            END AS [sugerirReposicion],
            CASE
                WHEN ISNULL(MDP.n_cantidad, 0) < ISNULL(SUM(CASE WHEN TR.c_tipomov = 'DESCARGO' THEN TR.n_cantidad ELSE 0 END), 0) THEN
                    (ISNULL(SUM(CASE WHEN TR.c_tipomov = 'DESCARGO' THEN TR.n_cantidad ELSE 0 END), 0) - (CASE WHEN ISNULL(MDP.n_cantidad, 0) < 0 THEN 0 ELSE ISNULL(MDP.n_cantidad, 0) END)) * 1.2
                WHEN ISNULL(MDP.n_cantidad, 0) <= 0 AND ISNULL(SUM(CASE WHEN TR.c_tipomov = 'DESCARGO' THEN TR.n_cantidad ELSE 0 END), 0) > 0 THEN
                    ISNULL(SUM(CASE WHEN TR.c_tipomov = 'DESCARGO' THEN TR.n_cantidad ELSE 0 END), 0) * 1.2
                ELSE 0
            END AS [montoSugerido],
            DATEDIFF(DAY, @FechaInicio, @FechaFin) + 1 AS [dias]
        FROM [MA_PRODUCTOS] MP
        LEFT JOIN [MA_DEPOPROD] MDP ON MP.c_codigo = MDP.c_codarticulo
        LEFT JOIN [MA_DEPARTAMENTOS] D ON MP.c_Departamento = D.C_CODIGO
        LEFT JOIN [TR_INVENTARIO] TR ON MP.c_codigo = TR.c_codarticulo
            AND TR.f_fecha BETWEEN @FechaInicio AND @FechaFin
        WHERE MP.c_codigo IN (SELECT codigo FROM @FiltroCodigos)
        GROUP BY MP.c_codigo, MP.c_descri, D.C_DESCRIPCIO, MDP.n_cantidad
    ) AS SubConsulta;

    SELECT
        codigo, descripcion, departamento,
        CAST(ROUND(stockActual, 0) AS INT) AS stockActual,
        CAST(ROUND(entradas, 0) AS INT) AS entradas,
        CAST(ROUND(salidas, 0) AS INT) AS salidas,
        sugerirReposicion,
        CAST(ROUND(montoSugerido, 0) AS INT) AS montoSugerido,
        dias
    FROM #Resultados
    ORDER BY salidas DESC, stockActual ASC;
    
    DROP TABLE #Resultados;
    """

    try:
        conn_str = (
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={config['SERVER']};"
            f"DATABASE={db_name};"
            f"UID={config['USER']};"
            f"PWD={config['PASS']};"
            f"Connect Timeout=10;"
            f"TrustServerCertificate=yes;"
        )

        with pyodbc.connect(conn_str) as conn:
            df = pd.read_sql(query, conn)

        if df.empty:
            return jsonify({"error": "No se encontraron datos para los códigos en esta sede"}), 404

        df.insert(0, "TIENDA", tienda_id)

        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Reposicion_Compras")
        output.seek(0)

        registrar_log(c_user, n_user, d_user, "reposicion_compras", f"Exportó Reposición Compras {tienda_id}")

        return send_file(
            output, 
            as_attachment=True, 
            download_name=f"Reposicion_Compras_{tienda_id}_{inicio}.xlsx"
        )

    except Exception as e:
        print(f"Error en Reposición Compras ({tienda_id}): {str(e)}")
        return jsonify({"error": f"Error de conexión con {tienda_id}: {str(e)}"}), 500
   
# ===================================================================================================
# COMPRAS CONSOLIDADO
# ===================================================================================================
@app.route("/compras_consolidada", methods=["GET"])
def reposicion_compras_consolidada():
    # 1. Obtener parámetros
    inicio = request.args.get("inicio", "").replace("-", "")
    fin = request.args.get("fin", "").replace("-", "")
    c_user = request.args.get("c_user")
    n_user = request.args.get("n_user")
    d_user = request.args.get("d_user")

    # 2. Cargar códigos de productos
    try:
        from models.compras import LCODIGOS_COMPRAS, consultar_sede_reposicion
        inserts_codigos = ",\n".join([f"('{c}')" for c in LCODIGOS_COMPRAS])
    except ImportError:
        return jsonify({"error": "No se pudo cargar la lista de códigos"}), 500

    # 3. Filtrar sedes (puedes ajustar cuáles ignorar)
    sedes_ignoradas = ["IMPORTADORA", "E-COMERCE", "CEMENTERIO", "CASCADA", "CANDELARIA"] 
    sedes_objetivo = {s: c for s, c in SERVIDORES_TIENDAS.items() if s not in sedes_ignoradas}

    # 4. Ejecución en paralelo
    all_dfs = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = {
            executor.submit(consultar_sede_reposicion, sede, config, inicio, fin, inserts_codigos): sede 
            for sede, config in sedes_objetivo.items()
        }
        
        for future in concurrent.futures.as_completed(futures):
            all_dfs.append(future.result())

    if not all_dfs:
        return jsonify({"error": "No se obtuvo respuesta de ninguna sede"}), 500

    # 5. Consolidar resultados
    combined_df = pd.concat(all_dfs, ignore_index=True)
    
    # Ordenar por nombre de tienda para que se vea organizado
    combined_df = combined_df.sort_values(by="Tiendas")

    # Añadir fila de Totales al final (opcional, igual que en tu imagen)
    totales = pd.DataFrame([{
        "Tiendas": "Totales Tiendas",
        "Stock Actual": combined_df["Stock Actual"].sum(),
        "Recepciones": combined_df["Recepciones"].sum(),
        "Salidas (Ventas)": combined_df["Salidas (Ventas)"].sum(),
        "Sugerido a Reponer": combined_df["Sugerido a Reponer"].sum(),
        "ESTADO": ""
    }])
    combined_df = pd.concat([combined_df, totales], ignore_index=True)

    # 6. Generar Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        combined_df.to_excel(writer, index=False, sheet_name="Consolidado_Reposicion")
    output.seek(0)

    # 7. Registrar Log
    try:
        registrar_log(c_user, n_user, d_user, "reposicion_consolidada", f"Exportó Consolidado Reposición {inicio}-{fin}")
    except:
        pass

    return send_file(
        output,
        as_attachment=True,
        download_name=f"Consolidado_Reposicion_{inicio}.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# ===================================================================================================
# POS
# ===================================================================================================
@app.route("/exportar_pos", methods=["GET"])
def exportar_pos():
    from models.pos import consultar_sede_pos

    fecha_inicio = request.args.get("inicio", "").replace("-", "")
    fecha_fin = request.args.get("fin", "").replace("-", "")
    moneda = request.args.get("moneda", "usd").lower()
    
    c_user = request.args.get("c_user")
    n_user = request.args.get("n_user")
    d_user = request.args.get("d_user")

    sedes_ignoradas = ["CENTRAL", "IMPORTADORA"]
    sedes_objetivo = {s: c for s, c in SERVIDORES_TIENDAS.items() if s not in sedes_ignoradas}

    all_dfs = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = {
            executor.submit(consultar_sede_pos, sede, config, fecha_inicio, fecha_fin, moneda): sede 
            for sede, config in sedes_objetivo.items()
        }
        
        for future in concurrent.futures.as_completed(futures):
            all_dfs.append(future.result())

    if not all_dfs:
        return jsonify({"error": "No se obtuvo respuesta de ninguna sede"}), 500

    combined_df = pd.concat(all_dfs, ignore_index=True)
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        combined_df.to_excel(writer, index=False, sheet_name="VentasPOS_Global")
    output.seek(0)

    try:
        from app import registrar_log 
        registrar_log(c_user, n_user, d_user, "ventas_pos", f"Exportación Global POS ({moneda})")
    except:
        pass

    return send_file(
        output,
        as_attachment=True,
        download_name=f"VentasPOS_Global_{fecha_inicio}_{fecha_fin}.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


# ===================================================================================================
# VENTAS
# ===================================================================================================
@app.route('/exportar_detalladas')
def exportar_detalladas():
    from models.ventas import query_ventas

    inicio = request.args.get('inicio').replace('-', '')
    fin = request.args.get('fin').replace('-', '')
    tienda_id = request.args.get('tienda')
    moneda = request.args.get('moneda', 'USD').upper()
    c_user = request.args.get('c_user')
    n_user = request.args.get('n_user')
    d_user = request.args.get('d_user')

    config = SERVIDORES_TIENDAS.get(tienda_id)
    if not config: return f"Sede {tienda_id} no configurada", 404

    try:
        conn_str = (f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={config['SERVER']};"
            f"DATABASE={config['DATABASE']};"
            f"UID={config['USER']};"
            f"PWD={config['PASS']};"
            f"Connect Timeout=10;"
            f"TrustServerCertificate=yes;")
        conn = pyodbc.connect(conn_str)
        df = pd.read_sql(query_ventas, conn, params=[moneda, inicio, fin, moneda, inicio, fin])
        conn.close()

        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Ventas Detalladas')
        output.seek(0)

        registrar_log(c_user, n_user, d_user, "ventas_detalladas", f"Exportó Ventas Detalladas {tienda_id}")

        return send_file(output, as_attachment=True, download_name=f"Detalladas_{tienda_id}.xlsx")
    except Exception as e:
        return f"Error: {str(e)}", 500


# ===================================================================================================
# CASHEA
# ===================================================================================================
@app.route('/consultar_cashea', methods=['GET'])
def consultar_cashea():
    tienda_id = request.args.get('tienda')
    inicio = request.args.get('inicio').replace('-', '')
    fin = request.args.get('fin').replace('-', '')

    config = SERVIDORES_TIENDAS.get(tienda_id)
    if not config: return jsonify({"error": "Tienda no encontrada"}), 400

    query = f"""
    DECLARE @FechaInicio NVARCHAR(8) = '{inicio}';
    DECLARE @FechaFin    NVARCHAR(8) = '{fin}';

    SELECT 
        @FechaInicio AS FECHA_INICIO,   
        @FechaFin AS FECHA_FIN,         
        COUNT(MA_PAGOS.c_concepto) AS CONCEPTO,
        SUM(MA_PAGOS.N_Subtotal) AS SUB_TOTAL,
        SUM(MA_PAGOS.n_Impuesto + MA_PAGOS.n_Imp_IGTF) AS IMPUESTOS, 
        SUM(MA_PAGOS.n_Total + MA_PAGOS.n_Imp_IGTF) AS TOTAL, 
        SUM(CASE 
            WHEN ABS(MA_PAGOS.n_Cancelado) >= ABS(MA_PAGOS.n_Total) AND c_Concepto = 'DEV' 
            THEN (ABS(MA_PAGOS.n_Cancelado) + ABS(MA_PAGOS.n_Imp_IGTF)) * -1 
            ELSE (CASE WHEN c_Concepto = 'DEV' THEN -1 ELSE 1 END * MA_PAGOS.n_Cancelado) 
        END) AS CANCELADO,
        SUM(MA_PAGOS.N_Vuelto) AS VUELTO
    FROM MA_PAGOS 
    LEFT JOIN VAD10.DBO.MA_SUCURSALES SUC ON MA_PAGOS.c_Sucursal = SUC.c_Codigo 
    WHERE 
        MA_PAGOS.f_Fecha BETWEEN CAST(@FechaInicio AS DATETIME) 
                         AND DATEADD(SECOND, -1, DATEADD(DAY, 1, CAST(@FechaFin AS DATETIME)))
        AND (MA_PAGOS.c_Concepto + MA_PAGOS.c_Numero IN (
            SELECT 'VEN' + p.c_Factura 
            FROM MA_DETALLEPAGO p 
            WHERE p.c_CodDenominacion = 'CSH' 
            AND p.d_Fecha BETWEEN CAST(@FechaInicio AS DATETIME) 
                          AND DATEADD(SECOND, -1, DATEADD(DAY, 1, CAST(@FechaFin AS DATETIME)))
        ))  
    GROUP BY 
        ISNULL(SUC.c_Descripcion, 'N/A');
    """

    try:
        conn_str = (f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={config['SERVER']};"
            f"DATABASE={config['DATABASE']};"
            f"UID={config['USER']};"
            f"PWD={config['PASS']};"
            f"Connect Timeout=10;"
            f"TrustServerCertificate=yes;")
        
        with pyodbc.connect(conn_str) as conn:
            df = pd.read_sql(query, conn)
            
        return jsonify(df.to_dict(orient='records'))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    
# ===================================================================================================
# DESCARGA DE PRODUCTOS CON IMAGENES
# ===================================================================================================
@app.route("/obtener_productos_txt", methods=["POST"])
def obtener_productos_txt():
    from models.img import procesar_imagen_para_js

    try:
        data = request.get_json(silent=True)
        if not data or "codigos" not in data:
            return jsonify({"error": "No se recibieron códigos"}), 400
        
        codigos_solicitados = list(set([str(c).strip() for c in data.get("codigos", []) if str(c).strip()]))
        
        if not codigos_solicitados:
            return jsonify([])

        conf = SQL_SERVER_IMG["CENTRAL"]
        
        conn_str = (f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={conf['SERVER']};"
            f"DATABASE={conf['DATABASE']};"
            f"UID={conf['USER']};"
            f"PWD={conf['PASS']};"
            f"Connect Timeout=10;"
            f"TrustServerCertificate=yes;")
        
        placeholders = ",".join(["?"] * len(codigos_solicitados))
        query = f"""
            SELECT 
                c_Codigo AS codigo,
                c_Descri AS descripcion,
                c_Marca,
                c_Modelo,
                n_CostoAct AS costo,
                n_Precio1 AS precio,
                n_Impuesto1 AS impuesto,
                (n_Precio1 + (n_Precio1 * (n_Impuesto1 / 100))) AS precio_total,
                c_FileImagen AS imagen_binaria
            FROM vad10.dbo.MA_PRODUCTOS 
            WHERE c_Codigo IN ({placeholders})
        """

        with pyodbc.connect(conn_str) as conn:
            df_db = pd.read_sql(query, conn, params=codigos_solicitados)

        productos_finales = []
        codigos_encontrados = set(df_db['codigo'].unique())

        for cod in codigos_solicitados:
            if cod in codigos_encontrados:
                row = df_db[df_db['codigo'] == cod].iloc[0]
                
                # APLICAMOS LA REPARACIÓN AQUÍ
                img_base64 = procesar_imagen_para_js(row["imagen_binaria"])

                productos_finales.append({
                    "Imagen": img_base64, # Ya va reparado y en base64
                    "Código": row["codigo"],
                    "Descripción": row["descripcion"],
                    "Marca": row["c_Marca"] if row["c_Marca"] else "NO TIENE",
                    "Modelo": row["c_Modelo"] if row["c_Modelo"] else "NO TIENE",
                    "Costo USD": round(float(row["costo"]), 2),
                    "Precio USD": round(float(row["precio"]), 2),
                    "Impuesto %": round(float(row["impuesto"]), 2),
                    "Precio Total": round(float(row["precio_total"]), 2)
                })
            else:
                productos_finales.append({
                    "Imagen": "NO EXISTE EN STELLAR",
                    "Código": cod,
                    "Descripción": "PRODUCTO NO ENCONTRADO",
                    "Marca": "-",
                    "Modelo": "-",
                    "Costo USD": 0,
                    "Precio USD": 0,
                    "Impuesto %": 0,
                    "Precio Total": 0
                })

        return jsonify(productos_finales)

    except Exception as e:
        print(f"❌ Error en /obtener_productos_txt: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
# ===================================================================================================
# TRIBUTOS CONSOLIDADO (TODAS LAS TIENDAS)
# ===================================================================================================
@app.route('/exportar_tributos_consolidado', methods=['GET'])
def exportar_tributos_consolidado():
    fecha_inicio = request.args.get('inicio') # Formato esperado: YYYY-MM-DD
    fecha_fin = request.args.get('fin')
    c_user = request.args.get('c_user')
    n_user = request.args.get('n_user')
    d_user = request.args.get('d_user')

    if not fecha_inicio or not fecha_fin:
        return jsonify({"error": "Faltan fechas"}), 400

    # Función interna para procesar cada tienda individualmente
    def consultar_tienda(tienda_id, config):
        try:
            conn_str = (f"DRIVER={{ODBC Driver 18 for SQL Server}};"
                        f"SERVER={config['SERVER']};"
                        f"DATABASE={config['DATABASE']};"
                        f"UID={config['USER']};"
                        f"PWD={config['PASS']};"
                        f"Connect Timeout=5;"
                        f"TrustServerCertificate=yes;")
            
            nombre_sucursal = TIENDAS_MAP.get(tienda_id)
            codigo_interno = config.get('SUCURSAL', tienda_id)
            
            with pyodbc.connect(conn_str) as conn:
                cursor = conn.cursor()
                # Ejecutamos la consulta directamente con pyodbc para evitar el UserWarning
                cursor.execute(sql_query, (nombre_sucursal, fecha_inicio, fecha_fin, codigo_interno))
                
                # Obtenemos los nombres de las columnas y los datos manualmente
                columns = [column[0] for column in cursor.description]
                data = cursor.fetchall()
                
                return pd.DataFrame.from_records(data, columns=columns)
                
        except Exception as e:
            print(f"⚠️ Error consultando {tienda_id}: {e}")
            return pd.DataFrame()

    # Ejecución concurrente
    all_dataframes = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        # CAMBIO: Iteramos sobre TIENDAS_MAP para filtrar solo las que quieres
        futuros = {}
        for tienda_id, nombre_sucursal in TIENDAS_MAP.items():
            # Buscamos la configuración en SERVIDORES_TIENDAS usando el nombre
            conf = SERVIDORES_TIENDAS.get(nombre_sucursal)
            
            if conf:
                futuros[executor.submit(consultar_tienda, tienda_id, conf)] = tienda_id
            else:
                print(f"⚠️ No hay configuración de servidor para: {nombre_sucursal}")
        
        for future in concurrent.futures.as_completed(futuros):
            df_resultado = future.result()
            if not df_resultado.empty:
                all_dataframes.append(df_resultado)

    if not all_dataframes:
        return jsonify({"error": "No se obtuvieron datos de ninguna sede"}), 404

    try:
        # Concatenar todos los resultados en un solo DataFrame
        df_final = pd.concat(all_dataframes, ignore_index=True)

        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_final.to_excel(writer, index=False, sheet_name='Consolidado_Tributos')
        output.seek(0)

        registrar_log(c_user, n_user, d_user, "tributos_consolidado", f"Exportó reporte consolidado: {fecha_inicio} a {fecha_fin}")

        return send_file(
            output, 
            as_attachment=True, 
            download_name=f"Tributos_Consolidado_{fecha_inicio}_al_{fecha_fin}.xlsx",
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        return jsonify({"error": f"Error al generar Excel: {str(e)}"}), 500

# ===================================================================================================
# LOGICA DE COSTOS PARA SUBIR TXT DE PROMOCIONES Y CAMBIOS DE PRECIOS
# ===================================================================================================
@app.route('/analyze', methods=['POST'])
def analyze():
    """Procesa el TXT y devuelve el análisis de validaciones."""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No se cargó ningún archivo'}), 400
            
        file = request.files['file']
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        df = process_txt_file(file_path)
        results = analyze_updates(df, db)
        return jsonify(results)

    except Exception as e:
        print(f"ERROR EN ANALYZE: {str(e)}") 
        return jsonify({'error': str(e)}), 500
#-------------------------------------------------------------------------
@app.route('/execute', methods=['POST'])
def execute():
    """
    Recibe la lista final de productos a actualizar.
    Ejecuta los UPDATE en Central e Importadora e INSERT en Pendientes.
    """
    try:
        data = request.get_json()
        productos_a_actualizar = data.get('productos', [])
        
        if not productos_a_actualizar:
            return jsonify({'error': 'No hay productos para actualizar'}), 400

        update_list = []
        for p in productos_a_actualizar:
            update_list.append({
                'codigo': str(p['codigo']).strip(),
                'costo': float(p.get('costo', 0)),
                'precio': float(p.get('precio', 0)),
                'impuesto': float(p.get('impuesto', 0)),
                'es_padre': not str(p['codigo']).isdigit() 
            })


        res_sync = db.execute_update_sync(update_list)
        
        if res_sync['errors']:
            print("\n--- ERRORES DE SINCRONIZACIÓN DETECTADOS ---")
            for err in res_sync['errors']:
                print(f"DETALLE: {err}")
            print("-------------------------------------------\n")

        mensaje = f"CENTRAL: {res_sync['central']} regs. | IMPORTADORA: {res_sync['importadora']} regs."
        
        if res_sync['errors']:
            return jsonify({
                'status': 'partial_error',
                'message': f"Sincronización incompleta. {mensaje}",
                'details': res_sync['errors']
            }), 207

        return jsonify({
            'status': 'success',
            'message': f"Sincronización exitosa. {mensaje}"
        })

    except Exception as e:
        print(f"ERROR CRÍTICO EN EXECUTE: {str(e)}")
        return jsonify({'error': f'Error en ejecución: {str(e)}'}), 500

#--------------------------------------------------------------------------------------------------------------------------------------
@app.route('/stock', methods=['POST'])
def route_tienda_stock(): 
    from models.compras import get_stock
    try:
        data = request.json
        numero_sucursal = data.get('nsucursal') 
        tienda = data.get('ntienda') 

        if not numero_sucursal:
            return jsonify({"Error": "No se proporcionó la sucursal"}), 400

        stock = get_stock(numero_sucursal, tienda)

        if stock is None:
            return jsonify({"Error": f"No se pudo obtener stock de {numero_sucursal}"}), 404

        return jsonify(stock), 200
    except Exception as e:
        return jsonify({"Error": str(e)}), 500
#--------------------------------------------------------------------------------------------------------------------------------------
@app.route('/get_dar', methods=['GET'])
def route_departamento(): 
    from models.stock import get_departamentos
    try:

        departamentos = get_departamentos()

        if departamentos is None:
            return jsonify({"Info": f"No se pudo obtener las Categorias"}), 404

        return jsonify(departamentos), 200
    except Exception as e:
        return jsonify({"Error": str(e)}), 500
#--------------------------------------------------------------------------------------------------------------------------------------
@app.route('/stock/all', methods=['POST'])
def route_tienda_stock_all(): 
    from models.stock import get_stock_all
    try:
        data = request.json
        numero_sucursal = data.get('nsucursal') 
        tienda = data.get('ntienda') 
        depar = data.get('depar') 

        if not numero_sucursal:
            return jsonify({"Error": "No se proporcionó la sucursal"}), 400

        stock = get_stock_all(numero_sucursal, tienda, depar)

        if stock is None:
            return jsonify({"Error": f"No se pudo obtener stock de {numero_sucursal}"}), 404

        return jsonify(stock), 200
    except Exception as e:
        return jsonify({"Error": str(e)}), 500
    
#--------------------------------------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5080, debug=True)