from psycopg2.extras import RealDictCursor
import psycopg2
import pyodbc
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    conn = psycopg2.connect(
        host=os.getenv('ip_carlos'),
        database=os.getenv('db_carlos'),
        user="postgres",
        password=os.getenv('psw_carlos')
    )
    return conn

#----------------------------------------------------------------------------------------------------------
class DatabaseManager:
    def __init__(self):
        # Cambia {SQL Server} por {ODBC Driver 18 for SQL Server} o {ODBC Driver 17 for SQL Server}
        self.conn_str_central = (
            f"DRIVER={{ODBC Driver 18 for SQL Server}};" 
            f"SERVER={os.getenv('DB_CENTRAL_HOST')};"
            f"DATABASE={os.getenv('DB_CENTRAL_NAME')};"
            f"UID={os.getenv('DB_CENTRAL_USER')};"
            f"PWD={os.getenv('DB_CENTRAL_PASS')};"
            f"TrustServerCertificate=yes;" # Agrega esto si tienes problemas de SSL
        )
                
        # Conexión Servidor IMPORTADORA
        self.conn_str_import = (
            f"DRIVER={{ODBC Driver 18 for SQL Server}};" # Asegúrate que este nombre sea el del paso 1
            f"SERVER={os.getenv('DB_IMPORT_HOST')};"
            f"DATABASE={os.getenv('DB_IMPORT_NAME')};"
            f"UID={os.getenv('DB_IMPORT_USER')};"
            f"PWD={os.getenv('DB_IMPORT_PASS')};"
            f"TrustServerCertificate=yes;" # <--- MUY IMPORTANTE en la versión 18
        )

    def get_connection(self, server_type='central'):
        conn_str = self.conn_str_central if server_type == 'central' else self.conn_str_import
        try:
            return pyodbc.connect(conn_str, timeout=5)
        except pyodbc.Error as e:
            print(f"Error de conexión a {server_type}: {e}")
            raise e

    def fetch_products_data(self, codes_list):
        if not codes_list: return []
        placeholders = ','.join(['?'] * len(codes_list))
        query = f"""
            SELECT c_Codigo, c_Codigo_Base, c_Descri, n_CostoAct, n_Impuesto1, n_Precio1 
            FROM MA_PRODUCTOS 
            WHERE c_Codigo IN ({placeholders})
        """
        with self.get_connection('central') as conn:
            cursor = conn.cursor()
            cursor.execute(query, codes_list)
            columns = [column[0] for column in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def check_promotions(self, codes_list):
        if not codes_list: return []
        placeholders = ','.join(['?'] * len(codes_list))
        query = f"""
            SELECT c_Codigo, Descripcion 
            FROM MA_PROMOCION 
            WHERE c_Codigo IN ({placeholders}) 
            AND f_Final >= GETDATE()
        """
        try:
            with self.get_connection('central') as conn:
                cursor = conn.cursor()
                cursor.execute(query, codes_list)
                return {row[0]: row[1] for row in cursor.fetchall()}
        except:
            return {}

    def get_children_of_parents(self, parent_codes):
        if not parent_codes: return []
        placeholders = ','.join(['?'] * len(parent_codes))
        query = f"SELECT c_Codigo, c_Codigo_Base, c_Descri FROM MA_PRODUCTOS WHERE c_Codigo_Base IN ({placeholders})"
        with self.get_connection('central') as conn:
            cursor = conn.cursor()
            cursor.execute(query, parent_codes)
            columns = [column[0] for column in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def execute_update_sync(self, update_list):
        results = {"central": 0, "importadora": 0, "errors": []}
        
        # 1. Query de Actualización
        sql_update = """
            UPDATE MA_PRODUCTOS
            SET 
                n_CostoAct = ?, n_CostoAnt = ?, n_CostoPro = ?, n_CostoRep = ?,
                n_Precio1 = ?, n_Precio2 = ?, n_Precio3 = ?, n_Impuesto1 = ?
            WHERE c_Codigo = ?
        """

        # 2. Query de Pendientes 
        sql_pendiente = """
            INSERT INTO TR_PENDIENTE_PROD (
                c_Codigo, c_Descri, c_Departamento, c_Grupo, c_Subgrupo, c_Marca, c_Modelo, 
                c_Procede, n_CostoAct, n_CostoAnt, n_CostoPro, n_CostoRep, n_Precio1, 
                n_Precio2, n_Precio3, c_Seriales, c_Compuesto, c_Presenta, n_Peso, 
                n_Volumen, n_CantiBul, n_PesoBul, n_VolBul, c_FileImagen, n_Impuesto1, 
                n_Impuesto2, n_Impuesto3, c_Cod_Arancel, c_Des_Arancel, n_Por_Arancel, 
                n_Costo_Original, c_Observacio, n_Activo, n_TipoPeso, n_PrecioO, 
                f_Inicial, f_Final, h_Inicial, h_Final, Add_Date, Update_Date, 
                c_CodFabricante, Hablador, c_CodMoneda, Cant_Decimales, Moneda_Ant, 
                Moneda_Act, Moneda_Pro, c_Codigo_Base, c_Descri_Base, Text1, Text2, 
                Text3, Text4, Text5, Text6, Text7, Text8, Date1, Nume1, n_Cantidad_Tmp, 
                c_Cod_Plantilla, c_UsuarioAdd, c_UsuarioUpd, n_Prod_Ext, n_Pro_Ext, 
                nu_Tipo_Producto, nu_InsumoInterno, nu_PrecioRegulado, nu_PocentajeMerma, 
                nu_NivelClave, cu_Descripcion_Corta, bs_PermiteTeclado, bs_PermiteCantidad, 
                nu_StockMin, nu_StockMax
            )
            SELECT 
                c_Codigo, c_Descri, c_Departamento, c_Grupo, c_Subgrupo, c_Marca, c_Modelo, 
                c_Procede, n_CostoAct, n_CostoAnt, n_CostoPro, n_CostoRep, n_Precio1, 
                n_Precio2, n_Precio3, c_Seriales, c_Compuesto, c_Presenta, n_Peso, 
                n_Volumen, n_CantiBul, n_PesoBul, n_VolBul, c_FileImagen, n_Impuesto1, 
                n_Impuesto2, n_Impuesto3, c_Cod_Arancel, c_Des_Arancel, n_Por_Arancel, 
                n_Costo_Original, c_Observacio, n_Activo, n_TipoPeso, n_PrecioO, 
                f_Inicial, f_Final, h_Inicial, h_Final, Add_Date, Update_Date, 
                c_CodFabricante, Hablador, c_CodMoneda, Cant_Decimales, Moneda_Ant, 
                Moneda_Act, Moneda_Pro, c_Codigo_Base, c_Descri_Base, Text1, Text2, 
                Text3, Text4, Text5, Text6, Text7, Text8, Date1, Nume1, n_Cantidad_Tmp, 
                c_Cod_Plantilla, c_UsuarioAdd, c_UsuarioUpd, n_Prod_Ext, n_Pro_Ext, 
                nu_Tipo_Producto, nu_InsumoInterno, nu_PrecioRegulado, nu_PocentajeMerma, 
                nu_NivelClave, cu_Descripcion_Corta, bs_PermiteTeclado, bs_PermiteCantidad, 
                nu_StockMin, nu_StockMax
            FROM MA_PRODUCTOS
            WHERE c_Codigo = ?;
        """

        # --- PROCESO CENTRAL ---
        try:
            with self.get_connection('central') as conn_c:
                cursor_c = conn_c.cursor()
                for item in update_list:
                    params = (
                        item['costo'], item['costo'], item['costo'], item['costo'],
                        item['precio'], item['precio'], item['precio'],
                        item['impuesto'], item['codigo']
                    )
                    cursor_c.execute(sql_update, params)
                    
                    if item['es_padre']:
                        sql_hijos = sql_update.replace("WHERE c_Codigo = ?", "WHERE c_Codigo_Base = ?")
                        cursor_c.execute(sql_hijos, params)

                    cursor_c.execute(sql_pendiente, (item['codigo'],))
                    results["central"] += 1
                conn_c.commit()
        except Exception as e:
            results["errors"].append(f"Error Central: {str(e)}")

        # --- PROCESO IMPORTADORA ---
        try:
            with self.get_connection('import') as conn_i:
                cursor_i = conn_i.cursor()
                for item in update_list:
                    params = (
                        item['costo'], item['costo'], item['costo'], item['costo'],
                        item['precio'], item['precio'], item['precio'],
                        item['impuesto'], item['codigo']
                    )
                    cursor_i.execute(sql_update, params)
                    
                    if item['es_padre']:
                        sql_hijos = sql_update.replace("WHERE c_Codigo = ?", "WHERE c_Codigo_Base = ?")
                        cursor_i.execute(sql_hijos, params)
                        
                    results["importadora"] += 1
                conn_i.commit()
        except Exception as e:
            results["errors"].append(f"Error Importadora: {str(e)}")

        return results