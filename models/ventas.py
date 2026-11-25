
query_ventas = """
SET NOCOUNT ON;
USE VAD10;
SELECT 
    MA_DEPARTAMENTOS.c_Descripcio AS Departamento,
    tb.cod_principal AS Producto,
    tb.c_Descri AS Descripcion,
    SUM(tb.cantidad) AS Cantidad,
    MAX(tb.precio) AS Precio,
    SUM(tb.impuesto) AS Impuesto,
    SUM(tb.total) AS Total
FROM (
    SELECT tr_inventario.c_CodArticulo as cod_principal, SUM(tr_inventario.n_Total) AS total, 
            MAX(tr_inventario.n_Precio) AS precio, SUM(tr_inventario.n_Impuesto) as impuesto, 
            SUM(tr_inventario.n_Cantidad) AS cantidad, ma_productos.c_Descri, ma_productos.c_Departamento
    FROM (
        SELECT c_CodArticulo, n_Cantidad, f_Fecha, c_Concepto, c_CodLocalidad, c_Compuesto,
            (n_Impuesto * (CASE WHEN CodMonOrig = CodMonDest THEN 1 ELSE FactorTransaccion / FactorHistoricoDestino END)) AS n_Impuesto,
            (n_Total * (CASE WHEN CodMonOrig = CodMonDest THEN 1 ELSE FactorTransaccion / FactorHistoricoDestino END)) AS n_Total,
            (n_Precio * (CASE WHEN CodMonOrig = CodMonDest THEN 1 ELSE FactorTransaccion / FactorHistoricoDestino END)) AS n_Precio
        FROM (
            SELECT TI.*, MA.d_Fecha AS TmpFechaHoraDoc, MA.c_CodMoneda AS CodMonOrig, 
            ISNULL((SELECT TOP 1 n_FactorPeriodo FROM MA_HISTORICO_MONEDAS 
                    WHERE c_CodMoneda = MON_DEST.c_CodMoneda AND d_FechaCambioActual <= MA.d_Fecha 
                    ORDER BY d_FechaCambioActual DESC, ID DESC), MON_DEST.n_Factor) AS FactorHistoricoDestino, 
            TI.n_FactorCambio AS FactorTransaccion, MON_DEST.c_CodMoneda AS CodMonDest
            FROM TR_INVENTARIO TI 
            INNER JOIN MA_VENTAS MA ON TI.c_Documento = MA.c_Documento AND TI.c_Concepto = MA.c_Concepto AND TI.c_CodLocalidad = MA.c_CodLocalidad
            CROSS JOIN (SELECT * FROM MA_MONEDAS WHERE c_CodMoneda = ?) MON_DEST
            WHERE TI.c_Concepto IN ('VEN', 'DEV') AND TI.f_Fecha BETWEEN ? AND DATEADD(SECOND, 86399, ?)
        ) AS TR_CONVERTIDO
    ) AS tr_inventario 
    LEFT JOIN ma_productos ON ma_productos.c_Codigo = tr_inventario.c_CodArticulo 
    WHERE tr_inventario.c_Concepto = 'VEN' AND tr_inventario.c_compuesto = ''
    GROUP BY tr_inventario.c_CodArticulo, ma_productos.c_Descri, ma_productos.c_Departamento
    UNION ALL
    SELECT tr_inventario.c_CodArticulo as cod_principal, SUM(tr_inventario.n_Total * -1) AS total, 
            MAX(tr_inventario.n_Precio) AS precio, SUM(tr_inventario.n_Impuesto * -1) as impuesto, 
            SUM(tr_inventario.n_Cantidad * -1) AS cantidad, ma_productos.c_Descri, ma_productos.c_Departamento
    FROM (
        SELECT c_CodArticulo, n_Cantidad, f_Fecha, c_Concepto, c_CodLocalidad, c_Compuesto,
            (n_Impuesto * (CASE WHEN CodMonOrig = CodMonDest THEN 1 ELSE FactorTransaccion / FactorHistoricoDestino END)) AS n_Impuesto,
            (n_Total * (CASE WHEN CodMonOrig = CodMonDest THEN 1 ELSE FactorTransaccion / FactorHistoricoDestino END)) AS n_Total,
            (n_Precio * (CASE WHEN CodMonOrig = CodMonDest THEN 1 ELSE FactorTransaccion / FactorHistoricoDestino END)) AS n_Precio
        FROM (
            SELECT TI.*, MA.d_Fecha AS TmpFechaHoraDoc, MA.c_CodMoneda AS CodMonOrig, 
            ISNULL((SELECT TOP 1 n_FactorPeriodo FROM MA_HISTORICO_MONEDAS 
                    WHERE c_CodMoneda = MON_DEST.c_CodMoneda AND d_FechaCambioActual <= MA.d_Fecha 
                    ORDER BY d_FechaCambioActual DESC, ID DESC), MON_DEST.n_Factor) AS FactorHistoricoDestino, 
            TI.n_FactorCambio AS FactorTransaccion, MON_DEST.c_CodMoneda AS CodMonDest
            FROM TR_INVENTARIO TI 
            INNER JOIN MA_VENTAS MA ON TI.c_Documento = MA.c_Documento AND TI.c_Concepto = MA.c_Concepto AND TI.c_CodLocalidad = MA.c_CodLocalidad
            CROSS JOIN (SELECT * FROM MA_MONEDAS WHERE c_CodMoneda = ?) MON_DEST
            WHERE TI.c_Concepto IN ('VEN', 'DEV') AND TI.f_Fecha BETWEEN ? AND DATEADD(SECOND, 86399, ?)
        ) AS TR_CONVERTIDO_DEV
    ) AS tr_inventario 
    LEFT JOIN ma_productos ON ma_productos.c_Codigo = tr_inventario.c_CodArticulo 
    WHERE tr_inventario.c_Concepto = 'DEV' AND tr_inventario.c_compuesto = ''
    GROUP BY tr_inventario.c_CodArticulo, ma_productos.c_Descri, ma_productos.c_Departamento
) tb
INNER JOIN MA_DEPARTAMENTOS ON MA_DEPARTAMENTOS.c_Codigo = tb.c_Departamento
GROUP BY MA_DEPARTAMENTOS.c_Descripcio, tb.cod_principal, tb.c_Descri
ORDER BY Departamento, Producto;
"""