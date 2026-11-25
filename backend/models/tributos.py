sql_query = """
    SELECT
        ? AS Tiendas,
        TBDatos2.CampoMostrar AS [Caja],
        TBDatos2.Cantidad AS [Nro.Facturas],
        TBDatos2.Total AS [Subtotal],
        TBDatos2.Impuesto AS [%],
        TBDatos2.gTotal AS [Total],
        CASE WHEN TBDatos2.Cantidad <> 0 THEN TBDatos2.Total / TBDatos2.Cantidad ELSE 0 END AS [PromedioFactura]
    FROM
        (
            SELECT
                CampoMostrar,
                SUM(Cantidad) AS Cantidad,
                SUM(Total) AS Total,
                SUM(Impuesto) AS Impuesto,
                SUM(gTotal) AS gTotal
            FROM
                (
                    SELECT
                        (CASE WHEN MA_PAGOS.c_Concepto = 'VEN' THEN 1 ELSE 0 END) AS Cantidad,
                        c_Caja AS CampoMostrar,
                        -- Lógica de Conversión para n_Subtotal (ahora Total/Subtotal)
                        (MA_PAGOS.n_Subtotal * (1 / (
                            SELECT ISNULL((
                                SELECT TOP 1 ISNULL(HIS.n_FactorPeriodo, MON.n_Factor)
                                FROM VAD10..MA_MONEDAS MON
                                LEFT JOIN VAD10..MA_HISTORICO_MONEDAS HIS ON MON.c_CodMoneda = HIS.c_CodMoneda
                                    AND HIS.d_FechaCambioActual <= (DATEADD(SECOND, ISNULL(TRY_CAST(MA_PAGOS.f_Hora AS INT), 0), TRY_CAST(MA_PAGOS.f_Fecha AS DATETIME)))
                                WHERE MON.c_CodMoneda = 'VES'
                                ORDER BY HIS.d_FechaCambioActual DESC, HIS.ID DESC
                            ), (
                                SELECT TOP 1 MON.n_Factor FROM VAD10..MA_MONEDAS MON WHERE MON.c_CodMoneda = 'VES'
                            ))
                        ))) AS Total,
                        -- Lógica de Conversión para n_Impuesto
                        (MA_PAGOS.n_Impuesto * (1 / (
                            SELECT ISNULL((
                                SELECT TOP 1 ISNULL(HIS.n_FactorPeriodo, MON.n_Factor)
                                FROM VAD10..MA_MONEDAS MON
                                LEFT JOIN VAD10..MA_HISTORICO_MONEDAS HIS ON MON.c_CodMoneda = HIS.c_CodMoneda
                                    AND HIS.d_FechaCambioActual <= (DATEADD(SECOND, ISNULL(TRY_CAST(MA_PAGOS.f_Hora AS INT), 0), TRY_CAST(MA_PAGOS.f_Fecha AS DATETIME)))
                                WHERE MON.c_CodMoneda = 'VES'
                                ORDER BY HIS.d_FechaCambioActual DESC, HIS.ID DESC
                            ), (
                                SELECT TOP 1 MON.n_Factor FROM VAD10..MA_MONEDAS MON WHERE MON.c_CodMoneda = 'VES'
                            ))
                        ))) AS Impuesto,
                        -- Lógica de Conversión para n_Total
                        (MA_PAGOS.n_Total * (1 / (
                            SELECT ISNULL((
                                SELECT TOP 1 ISNULL(HIS.n_FactorPeriodo, MON.n_Factor)
                                FROM VAD10..MA_MONEDAS MON
                                LEFT JOIN VAD10..MA_HISTORICO_MONEDAS HIS ON MON.c_CodMoneda = HIS.c_CodMoneda
                                    AND HIS.d_FechaCambioActual <= (DATEADD(SECOND, ISNULL(TRY_CAST(MA_PAGOS.f_Hora AS INT), 0), TRY_CAST(MA_PAGOS.f_Fecha AS DATETIME)))
                                WHERE MON.c_CodMoneda = 'VES'
                                ORDER BY HIS.d_FechaCambioActual DESC, HIS.ID DESC
                            ), (
                                SELECT TOP 1 MON.n_Factor FROM VAD10..MA_MONEDAS MON WHERE MON.c_CodMoneda = 'VES'
                            ))
                        ))) AS gTotal
                    FROM
                        VAD20..MA_PAGOS
                    WHERE
                        MA_PAGOS.f_Fecha BETWEEN CONVERT(DATETIME, ?, 120) AND CONVERT(DATETIME, ?, 120)
                        AND CAST(CASE WHEN ISNUMERIC(c_Caja) = 1 THEN c_Caja ELSE 0 END AS NUMERIC) >= 1
                        AND CAST(CASE WHEN ISNUMERIC(c_Caja) = 1 THEN c_Caja ELSE 0 END AS NUMERIC) <= 40
                        AND MA_PAGOS.c_Sucursal IN (?)
                ) TBDatos
            GROUP BY CampoMostrar
        ) TBDatos2
    ORDER BY
        CAST(CASE WHEN ISNUMERIC(CampoMostrar) = 1 THEN CampoMostrar ELSE 0 END AS INT);
"""