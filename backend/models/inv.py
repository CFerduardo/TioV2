query_inv = """
    SET NOCOUNT ON;
    USE VAD10;
    DECLARE @FechaInicio DATE = ?;
    DECLARE @FechaFin DATE = ?;

    SELECT 
        MDP.c_codarticulo AS codigo,
        MP.C_DESCRI AS descripcion,
        MP.c_marca AS marca,
        MP.c_modelo AS modelo,
        ISNULL(PROV.c_Descripcio, 'SIN PROVEEDOR') AS proveedor,
        ISNULL(PROV.c_CodProveed, 'N/A') AS codproveedor,
        MP.n_CostoAct AS costo,
        MP.n_Precio1 AS precio,
        MP.n_Impuesto1 AS impuesto,
        LTRIM(RTRIM(REPLACE(MD.c_descripcion, 'Piso de venta', ''))) AS tienda,
        MDP.n_cantidad AS stockactual,
        ISNULL(SUM(CASE WHEN TR.c_tipomov = 'CARGO' THEN TR.n_cantidad ELSE 0 END), 0) AS entradas,
        ISNULL(SUM(CASE WHEN TR.c_tipomov = 'DESCARGO' THEN TR.n_cantidad ELSE 0 END), 0) AS salidas,
        DATEDIFF(DAY, @FechaInicio, @FechaFin) + 1 AS dias
    FROM dbo.MA_DEPOPROD MDP
    INNER JOIN dbo.MA_PRODUCTOS MP ON MDP.c_codarticulo = MP.c_codigo 
    INNER JOIN dbo.MA_DEPOSITO MD ON MDP.c_coddeposito = MD.c_coddeposito
    LEFT JOIN  dbo.MA_PRODXPROV PXP ON MP.c_codigo = PXP.c_codigo
    LEFT JOIN  dbo.MA_PROVEEDORES PROV ON PXP.c_codprovee = PROV.c_CodProveed
    LEFT JOIN  dbo.TR_INVENTARIO TR ON MDP.c_codarticulo = TR.c_codarticulo 
        AND TR.f_fecha BETWEEN @FechaInicio AND @FechaFin
    GROUP BY 
        MDP.c_codarticulo, MP.C_DESCRI, MP.c_marca, MP.c_modelo,
        PROV.c_Descripcio, PROV.c_CodProveed, MP.n_CostoAct,
        MP.n_Precio1, MP.n_Impuesto1, MD.c_descripcion, MDP.n_cantidad
    ORDER BY tienda, codigo;
"""