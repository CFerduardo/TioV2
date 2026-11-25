import pandas as pd
import numpy as np

def process_txt_file(file_path):
    """
    Lee el archivo TXT con la estructura: Codigo, Descripcion, Costo, Precio, Impuesto.
    """
    try:
        column_names = ['codigo', 'descripcion', 'costo', 'precio', 'impuesto']
        
        # Leemos el archivo con separador de coma explícito
        df = pd.read_csv(
            file_path, 
            names=column_names, 
            header=None, 
            sep=',', 
            encoding='latin1',
            dtype={'codigo': str}
        )
        
        df['codigo'] = df['codigo'].str.strip()
        
        df['costo'] = pd.to_numeric(df['costo'], errors='coerce').fillna(0)
        df['precio'] = pd.to_numeric(df['precio'], errors='coerce').fillna(0)
        df['impuesto'] = pd.to_numeric(df['impuesto'], errors='coerce').fillna(0)
        
        return df
    except Exception as e:
        raise Exception(f"Error al leer el archivo TXT: {str(e)}")

def analyze_updates(df_txt, db_manager):

    codes_in_txt = df_txt['codigo'].unique().tolist()
    
    # Separamos Alfanuméricos (Padres) de Numéricos (Hijos)
    parent_codes_detected = [c for c in codes_in_txt if not c.isdigit()]
    
    db_products = db_manager.fetch_products_data(codes_in_txt)
    db_map = {p['c_Codigo']: p for p in db_products}
    
    all_related_codes = codes_in_txt.copy()
    children_data = []
    if parent_codes_detected:
        children_data = db_manager.get_children_of_parents(parent_codes_detected)
        for child in children_data:
            if child['c_Codigo'] not in all_related_codes:
                all_related_codes.append(child['c_Codigo'])

    # Validar Promociones 'DPE' para todos los involucrados
    promos_active = db_manager.check_promotions(all_related_codes)
    
    analysis = {
        'ready': [],
        'alerts_promo': [],
        'alerts_loss': [],
        'not_found': [],
        'full_data': [] 
    }

    for _, row in df_txt.iterrows():
        codigo = row['codigo']
        
        # VALIDACIÓN 1: Existencia
        if codigo not in db_map:
            analysis['not_found'].append(codigo)
            continue
            
        prod_db = db_map[codigo]
        
        precio_nuevo = float(row['precio'])
        impuesto_porcentaje = float(row['impuesto'])
        costo_actual = float(prod_db['n_CostoAct'])
        descripcion_db = prod_db['c_Descri']

        # VALIDACIÓN 2: Promociones
        has_promo = False
        nombre_promo = ""
        
        if codigo in promos_active:
            has_promo = True
            nombre_promo = promos_active[codigo]
        else:
            hijos_en_promo = [c['c_Codigo'] for c in children_data 
                             if c['c_Codigo_Base'] == codigo and c['c_Codigo'] in promos_active]
            if hijos_en_promo:
                has_promo = True
                nombre_promo = f"Hijos en promo: {promos_active[hijos_en_promo[0]]}"

        if has_promo:
            analysis['alerts_promo'].append({
                'codigo': codigo,
                'descripcion': descripcion_db,
                'promo': nombre_promo
            })

        # VALIDACIÓN 3: Venta a Pérdida
        precio_neto = precio_nuevo / (1 + (impuesto_porcentaje / 100))
        
        if precio_neto < costo_actual:
            analysis['alerts_loss'].append({
                'codigo': codigo,
                'descripcion': descripcion_db,
                'costo': round(costo_actual, 2),
                'precio_neto': round(precio_neto, 2)
            })
            
        analysis['ready'].append({
            'codigo': codigo,
            'descripcion': descripcion_db,
            'precio': precio_nuevo
        })

        analysis['full_data'].append({
            'codigo': codigo,
            'costo': float(row['costo']),
            'precio': precio_nuevo,
            'impuesto': impuesto_porcentaje
        })

    return analysis