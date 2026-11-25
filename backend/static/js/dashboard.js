const LISTA_SEDES = [
    'ANACO', 'APURE', 'BABILON', 'BARALT', 'BOLIVAR', 'CABIMAS', 'CABUDARE', 
    'CAGUA', 'CARORA', 'CATIA', 'CRUZ VERDE', 'CUMANA', 'GUACARA', 'GUANARE', 
    'KAPITANA', 'MARACAIBO', 'MARACAY', 'MATURIN', 'PROPATRIA', 'TIGRE', 
    'UPATA', 'VALENCIA', 'VALERA', 'VIGIA', 'CASCADA', 'CEMENTERIO', 
    'CANDELARIA', 'E-COMERCE', 'VALLES'
];

let moduloActual = '';
let sedeActual = '';
let monedaActual = 'USD';
let productosCargados = [];

// Cargar preferencia del tema al iniciar (Añadir dentro del DOMContentLoaded existente)
document.addEventListener('DOMContentLoaded', () => {
    // ... tu lógica existente de usuario y permisos ...
    const dept = localStorage.getItem('departamento');
    const user = localStorage.getItem('usuario');
    const userInfo = document.getElementById('user-info');
    if (userInfo) userInfo.innerText = `👤 Usuario: ${user} | 🏢 Depto: ${dept}`;

    // Permisos
    const permisos = {
        'yaguara': ['tecnologia', 'inventario', 'costo', 'reposicion'],
        'tiendas': ['tecnologia', 'inventario', 'costo', 'reposicion'],
        'ventaspos': ['tecnologia', 'ventas', 'gerencia'],
        'detalladas': ['tecnologia', 'ventas', 'gerencia', 'costo'],
        'inventario': ['tecnologia', 'inventario', 'costo', 'reposicion'],
        'reposicion': ['tecnologia', 'inventario', 'reposicion'],
        'cashea': ['tecnologia', 'ventas'],
        'costos': ['tecnologia', 'costo'],
        'descarga-prod': ['tecnologia', 'costo', 'ventas'],
        'reposicion_compras': ['tecnologia'],
        'cierres': ['tecnologia', 'tributos']
    };

    Object.keys(permisos).forEach(id => {
        const btn = document.getElementById(`btn-${id}`);
        if (btn) {
            btn.style.display = permisos[id].includes(dept) ? 'flex' : 'none';
        }
    });
    
    // --- AÑADIR ESTO AQUÍ ---
    const savedTheme = localStorage.getItem('theme') || 'light';
    const body = document.body;
    const themeIcon = document.getElementById('theme-icon');
    const themeText = document.getElementById('theme-text');

    if (savedTheme === 'dark') {
        body.classList.remove('light');
        body.classList.add('dark');
        themeIcon.classList.remove('fa-moon');
        themeIcon.classList.add('fa-sun');
        themeText.textContent = 'Modo Claro';
    }
    // ------------------------
});

// ------------------------------- NAVEGACIÓN ---------------------------

function mostrarFiltrosSimple(tipo) {
    moduloActual = tipo;
    seleccionarSede('POSTGRES'); // Mantiene la selección por defecto
    ocultarTodo();
    document.getElementById('interfaz-filtros').style.display = 'block';
    
    // Lógica de títulos
    let titulo = "";
    if (tipo === 'yaguara') titulo = "📦 Recepción Yaguara";
    else if (tipo === 'tiendas') titulo = "🏪 Recepción Tiendas";
    else if (tipo === 'cierres') titulo = "🧾 Cierres POS Consolidado";
    else if (tipo === 'reposicion_compras') titulo = "🛒 Reposición para Compras";
    
    document.getElementById('txt-titulo-modulo').innerText = titulo;
}
//--------------------------------------------------------------------------------------
function irAMenuSedes(tipo) {
    moduloActual = tipo;

    if (tipo === 'ventaspos') {

        sedeActual = 'TODAS'; 
        ocultarTodo();
        
        const interfazFiltros = document.getElementById('interfaz-filtros');
        const txtSede = document.getElementById('txt-sede-activa');
        const btnDescargar = document.getElementById('btn-descargar');
        const boxMoneda = document.getElementById('box-moneda');
        const titulo = document.getElementById('txt-titulo-modulo');

        interfazFiltros.style.display = 'block';
        txtSede.innerText = 'REPORTE GLOBAL (TODAS LAS SEDES)';
        titulo.innerText = "📈 Efectividad Ventas POS - Consolidado";
        boxMoneda.style.display = 'block';
        btnDescargar.innerText = "GENERAR REPORTE GLOBAL";
        btnDescargar.onclick = procesarDescarga;
        
        return; 
    }

    ocultarTodo();
    document.getElementById('menu-sedes').style.display = 'block';
    const contenedorSedes = document.getElementById('container-sedes');
    contenedorSedes.innerHTML = ''; 
    let sedes = [...LISTA_SEDES];
    if (['inventario', 'reposicion'].includes(tipo)) sedes.push('IMPORTADORA');
    if (['inventario', 'reposicion', 'reposicion_compras'].includes(tipo)) sedes.push('IMPORTADORA');

    sedes.sort().forEach(sede => {
        const div = document.createElement('div');
        div.className = 'card-sede';
        div.innerText = sede;
        div.onclick = () => seleccionarSede(sede);
        contenedorSedes.appendChild(div);
    });
}
//--------------------------------------------------------------------------------------
function seleccionarSede(sede) {
    sedeActual = sede;
    ocultarTodo();
    document.getElementById('interfaz-filtros').style.display = 'block';
    document.getElementById('txt-sede-activa').innerText = `SEDE: ${sede}`;
    
    const btn = document.getElementById('btn-descargar');
    const boxMoneda = document.getElementById('box-moneda');
    const titulo = document.getElementById('txt-titulo-modulo');
    const btnConsolidado = document.getElementById('btn-descargar-consolidado');

    // Resetear visibilidad por defecto
    boxMoneda.style.display = (['ventaspos', 'detalladas'].includes(moduloActual)) ? 'block' : 'none';
    btnConsolidado.style.display = 'none';

    if (moduloActual === 'cashea') {
        titulo.innerText = "💳 Consulta Movimientos Cashea";
        btn.innerText = "VISUALIZAR CASHEA";
        btn.onclick = window.procesarConsultaCashea;

    } else if (moduloActual === 'reposicion_compras') {
        titulo.innerText = "🛒 Reposición para Compras";
        btn.innerText = "DESCARGAR DETALLADO";
        btnConsolidado.innerText = "DESCARGAR CONSOLIDADO";
        btnConsolidado.style.display = 'block';
        btnConsolidado.onclick = window.procesarDescargaConsolidada;
        btn.onclick = procesarDescarga;

    } else {
        btn.innerText = "DESCARGAR EXCEL";
        btn.onclick = window.procesarDescarga;
        
        const titulos = {
            'ventaspos': "📈 Efectividad Ventas POS",
            'inventario': "📋 Inventario de Tienda",
            'reposicion': "🔄 Sugerido de Reposición",
            'detalladas': "📊 Ventas Detalladas"
        };
        titulo.innerText = titulos[moduloActual] || "Reporte";
    }
}
//--------------------------------------------------------------------------------------
// --- CASHEA (
async function procesarConsultaCashea() {
    const inicio = document.getElementById('fecha-inicio').value;
    const fin = document.getElementById('fecha-fin').value;

    if (!inicio || !fin) {
        return Swal.fire({
            icon: 'warning',
            title: 'Fechas incompletas',
            text: 'Por favor, seleccione el rango de fechas para el reporte.'
        });
    }

    toggleLoader(true);
    try {
        const response = await fetch(`/consultar_cashea?tienda=${sedeActual}&inicio=${inicio}&fin=${fin}`);
        const datos = await response.json();
        
        if (datos.error) throw new Error(datos.error);

        const tbody = document.getElementById('tbody-cashea');
        const thead = document.getElementById('thead-cashea');
        
        thead.innerHTML = `
            <tr>
                <th>Desde</th>
                <th>Hasta</th>
                <th>Concepto</th>
                <th>Subtotal</th>
                <th>Impuestos</th>
                <th>Total</th>
                <th>Cancelado</th>
                <th>Vuelto</th>
            </tr>`;

        tbody.innerHTML = datos.map(d => `
            <tr>
                <td style="color: #aaa;">${d.FECHA_INICIO}</td>
                <td style="color: #aaa;">${d.FECHA_FIN}</td>
                <td>${d.CONCEPTO}</td>
                <td>${d.SUB_TOTAL.toFixed(2)}</td>
                <td>${d.IMPUESTOS.toFixed(2)}</td>
                <td style="font-weight:bold;">${d.TOTAL.toFixed(2)}</td>
                <td style="color:#00ff88; font-weight:bold;">${d.CANCELADO.toFixed(2)}</td>
                <td style="color: #e74c3c;">${d.VUELTO.toFixed(2)}</td>
            </tr>
        `).join('');
        
        document.getElementById('contenedor-tabla-cashea').style.display = 'block';
    } catch (e) {
        console.error("Error en Cashea:", e);
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: 'Error al consultar Cashea...'
        });
    } finally {
        toggleLoader(false);
    }
}
//--------------------------------------------------------------------------------------
async function procesarArchivoTxt(input) {
    const file = input.files[0];
    if (!file) return;
    document.getElementById('loader-overlay').style.display = 'flex';
    document.getElementById('loader-text').innerText = "Leyendo códigos...";

    const reader = new FileReader();
    reader.onload = async (e) => {
        const contenido = e.target.result;
        const codigos = contenido.split(/\r?\n/).map(c => c.trim()).filter(c => c !== "");

        if (codigos.length === 0) {
            toggleLoader(false); // Asegúrate de apagar el loader
            return Swal.fire({
                icon: 'info',
                title: 'Información',
                text: 'El archivo está vacío...'
            });
        }

       try {
            const response = await fetch('/obtener_productos_txt', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ codigos: codigos })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || "Error en el servidor");
            }

            const data = await response.json();
            
            if (Array.isArray(data) && data.length > 0) {
                renderizarPrevia(data); 

                window.datosUltimaBusqueda = data; 
                document.getElementById('btn-excel-imagenes').style.display = 'inline-block';

                const btnExcel = document.getElementById('btn-excel-imagenes');
                if (btnExcel) {
                    btnExcel.style.display = 'inline-block';
                }
            } else {
                Swal.fire({
                    icon: 'error',
                    title: 'Error Inesperado',
                    text: 'No se encontraron productos en la base de datos...'
                });
            }
        } catch (error) {
            console.error(error);
            Swal.fire({
                icon: 'error',
                title: 'Error Inesperado',
                text: 'Hubo un error al generar el archivo Excel..'
            });
        } finally {
                    document.getElementById('loader-overlay').style.display = 'none';
                }
            };
    reader.readAsText(file);
}
//--------------------------------------------------------------------------------------
function renderizarPrevia(productos) {
    const tbody = document.getElementById('tbody-productos');
    const thead = document.getElementById('thead-productos');
    
    thead.innerHTML = `
            <tr>
                <th>Imagen</th>
                <th>Código</th>
                <th>Descripción</th>
                <th>Precio Total</th>
            </tr>
        `;

    tbody.innerHTML = productos.map(p => `
            <tr>
                <td>
                    ${p.Imagen && p.Imagen !== "NO EXISTE EN STELLAR" 
                        ? `<img src="data:image/jpeg;base64,${p.Imagen}" style="width:50px;">` 
                        : '❌'}
                </td>
                <td>${p.Código}</td>
                <td>${p.Descripción}</td>
                <td>${p["Precio Total"]}</td>
            </tr>
        `).join('');
}
//--------------------------------------------------------------------------------------
//-------------------         COMPRAS NACIONALES           -----------------------------
async function procesarDescargaConsolidada() {
    const inicio = document.getElementById('fecha-inicio').value;
    const fin = document.getElementById('fecha-fin').value;
    
    if (!inicio || !fin) {
        return Swal.fire({ icon: 'warning', title: 'Fechas incompletas' });
    }

    const cedula = localStorage.getItem('cedula') || '0';
    const usuario = localStorage.getItem('usuario') || 'S/N';
    const depto = localStorage.getItem('departamento') || 'S/D';
    const userParams = `&c_user=${cedula}&n_user=${usuario}&d_user=${depto}`;

    toggleLoader(true);
    document.getElementById('loader-text').innerText = "Generando Consolidado Global...";
    
    const endpoint = `/compras_consolidada?inicio=${inicio}&fin=${fin}${userParams}`;

    try {
        const response = await fetch(endpoint);
        if (response.ok) {
            window.location.href = endpoint;
            setTimeout(() => toggleLoader(false), 3000);
        } else {
            const errorData = await response.json();
            toggleLoader(false);
            Swal.fire({ icon: 'error', title: 'Error', text: errorData.error });
        }
    } catch (error) {
        toggleLoader(false);
        Swal.fire({ icon: 'error', title: 'Error de Conexión' });
    }
}
//--------------------------------------------------------------------------------------
async function downloadExcel() {
    const productos = window.datosUltimaBusqueda;
    if (!productos || productos.length === 0) {
        alert("No hay datos para exportar.");
        return;
    }

    try {
        const workbook = new ExcelJS.Workbook();
        const worksheet = workbook.addWorksheet('Lista de Productos');

        worksheet.columns = [
            { header: 'Imagen', key: 'Imagen', width: 15 }, 
            { header: 'Código', key: 'Código', width: 20 },
            { header: 'Descripción', key: 'Descripción', width: 45 },
            { header: 'Marca', key: 'Marca', width: 20 },
            { header: 'Modelo', key: 'Modelo', width: 15 },
            { header: 'Costo USD', key: 'Costo USD', width: 12 },
            { header: 'Precio USD', key: 'Precio USD', width: 12 },
            { header: 'Impuesto %', key: 'Impuesto %', width: 12 },
            { header: 'Precio Total', key: 'Precio Total', width: 15 }
        ];

        for (let i = 0; i < productos.length; i++) {
            const p = productos[i];
            const rowIndex = i + 2; 

            worksheet.addRow({
                'Imagen': '', 
                'Código': p['Código'],
                'Descripción': p['Descripción'],
                'Marca': p['Marca'] || '',
                'Modelo': p['Modelo'] || '',
                'Costo USD': p['Costo USD'] || 0,
                'Precio USD': p['Precio USD'] || 0,
                'Impuesto %': p['Impuesto %'] || 0,
                'Precio Total': p['Precio Total'] || 0
            });

            // Ajustamos altura de la fila (80-90 es ideal para fotos cuadradas)
            worksheet.getRow(rowIndex).height = 80;
            worksheet.getRow(rowIndex).alignment = { vertical: 'middle', horizontal: 'left' };

            // INSERTAR IMAGEN (Solo si existe y no es el mensaje de error)
            if (p.Imagen && p.Imagen !== "NO EXISTE EN STELLAR") {
                try {
                    const imageId = workbook.addImage({
                        base64: p.Imagen, // Ya viene reparado por decode_sql_image en Python[cite: 2]
                        extension: 'jpeg',
                    });

                    worksheet.addImage(imageId, {
                        tl: { col: 0.1, row: rowIndex - 0.9 }, // Pequeño margen dentro de la celda
                        ext: { width: 95, height: 95 },
                        editAs: 'oneCell' 
                    });
                } catch (e) {
                    console.error("Error al insertar imagen en Excel para: " + p.Código, e);
                }
            }
        } // <--- ESTA ES LA LLAVE QUE FALTABA PARA CERRAR EL BUCLE FOR

        // Generar y descargar el archivo
        const buffer = await workbook.xlsx.writeBuffer();
        const blob = new Blob([buffer], { type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" });
        saveAs(blob, `Descarga_Productos_${new Date().getTime()}.xlsx`);

    } catch (error) {
        console.error("Error generando Excel:", error);
        alert("Hubo un error al generar el archivo Excel.");
    }
}

// --- HELPERS ---
function toggleLoader(show) { document.getElementById('loader-overlay').style.display = show ? 'flex' : 'none'; }
//---------------------------------------------------------------------------------------------------------------------------------
function mostrarInterfazDescarga() { ocultarTodo(); document.getElementById('interfaz-descarga-productos').style.display = 'block'; }
function volverAlPrincipal() { ocultarTodo(); document.getElementById('menu-principal').style.display = 'block'; }
function regresarAlMenu() { volverAlPrincipal(); }

//---------------------------------------------------------------------------------------------------------------------------------
function ocultarTodo() {
    ['menu-principal', 'menu-sedes', 'interfaz-filtros', 'interfaz-descarga-productos'].forEach(id => {
        const el = document.getElementById(id);
        if(el) el.style.display = 'none';
    });
    
    // ✅ OCULTAR TABLA DE CASHEA
    const contenedorCashea = document.getElementById('contenedor-tabla-cashea');
    if (contenedorCashea) contenedorCashea.style.display = 'none';
}
//---------------------------------------------------------------------------------------------------------------------------------
function atrasDesdeFiltros() {
    // En lugar de lógica compleja de IDs que ya no usamos, 
    // simplemente regresamos a la vista principal (Dashboard)
    ocultarTodo();
    
    // Limpiamos los títulos y badges por si acaso
    const txtSede = document.getElementById('txt-sede-activa');
    if(txtSede) txtSede.innerText = '';
    
    // Mostramos el contenedor de tarjetas
    const menu = document.getElementById('menu-principal');
    if(menu) {
        menu.style.display = 'block';
    } else {
        // Si por alguna razón el DOM se perdió, recargamos (Plan B)
        window.location.reload();
    }
}

// Opcional: Si quieres que el botón "atras" siempre limpie todo y sea seguro
function regresarAlMenu() {
    window.location.reload(); 
}
//---------------------------------------------------------------------------------------------------------------------------------
async function procesarDescarga() {
    const inicio = document.getElementById('fecha-inicio').value;
    const fin = document.getElementById('fecha-fin').value;
    
    if (!inicio || !fin) {
        return Swal.fire({
            icon: 'warning',
            title: 'Fechas incompletas',
            text: 'Por favor, seleccione el rango de fechas para el reporte.'
        });
    }

    const cedula = localStorage.getItem('cedula') || '0';
    const usuario = localStorage.getItem('usuario') || 'S/N';
    const depto = localStorage.getItem('departamento') || 'S/D';
    const userParams = `&c_user=${cedula}&n_user=${usuario}&d_user=${depto}`;

    const elMoneda = document.getElementById('select-moneda');
    const moneda = elMoneda ? elMoneda.value : 'USD';

    toggleLoader(true);
    document.getElementById('loader-text').innerText = "Consultando todas las sedes...";
    document.getElementById('loader-subtext').innerText = "Este proceso puede tardar unos segundos dependiendo de la conexión de las tiendas.";

    let endpoint = "";
    
    if (moduloActual === 'ventaspos') {
        endpoint = `/exportar_pos?inicio=${inicio}&fin=${fin}&moneda=${moneda}${userParams}`;
    } 
    else {
        const baseEndpoints = {
            'inventario': '/exportar_inventario',
            'reposicion': '/exportar_reposicion',
            'reposicion_compras': '/reposicion_compras',
            'detalladas': '/exportar_detalladas',
            'yaguara': '/exportar_yaguara',
            'tiendas': '/exportar_tiendas',
            'cierres': '/exportar_tributos_consolidado'
        };
        endpoint = `${baseEndpoints[moduloActual]}?tienda=${sedeActual}&inicio=${inicio}&fin=${fin}${userParams}`;
        if (moduloActual === 'detalladas') endpoint += `&moneda=${moneda}`;
    }

    try {
        const response = await fetch(endpoint);
        if (response.ok) {
            window.location.href = endpoint;
            setTimeout(() => toggleLoader(false), 3000);
        } else {
            const errorData = await response.json();
            toggleLoader(false);
            Swal.fire({
                icon: 'error',
                title: 'Error en Reporte',
                text: errorData.error || 'No se pudieron obtener datos de las sedes.'
            });
        }
    } catch (error) {
        toggleLoader(false);
        Swal.fire({
            icon: 'error',
            title: 'Error de Conexión',
            text: 'No se pudo conectar con el servidor central.'
        });
    }
}

function mostrarInterfazCostos() {
    ocultarTodo();
    document.getElementById('interfaz-costos').style.display = 'block';
}

function logout() { localStorage.clear(); window.location.href = '/'; }

// Función para alternar entre tema claro y oscuro -----------------------------------------------------
function toggleTheme() {
    const body = document.body;
    const themeIcon = document.getElementById('theme-icon');
    const themeText = document.getElementById('theme-text');
    
    // Guardar preferencia en localStorage
    if (body.classList.contains('light')) {
        // Cambiar a Oscuro
        body.classList.remove('light');
        body.classList.add('dark');
        themeIcon.classList.remove('fa-moon');
        themeIcon.classList.add('fa-sun');
        themeText.textContent = 'Modo Claro';
        localStorage.setItem('theme', 'dark');
    } else {
        // Cambiar a Claro
        body.classList.remove('dark');
        body.classList.add('light');
        themeIcon.classList.remove('fa-sun');
        themeIcon.classList.add('fa-moon');
        themeText.textContent = 'Modo Oscuro';
        localStorage.setItem('theme', 'light');
    }
}

