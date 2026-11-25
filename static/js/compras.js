

(function() {
    // 1. ESTADO GLOBAL
    let productosActuales = []; // Aquí guardaremos la respuesta de la API
    const STORES = {
        '0203': 'BABILON', '0301': 'BARALT', '0202': 'CABIMAS', '0205': 'CABUDARE', '0501': 'CAGUA',
        '0207': 'CATIA', '0201': 'CRUZ VERDE', '0204': 'GUANARE', '0103': 'GUACARA', '0101': 'KAPITANA',
        '0302': 'MATURIN', '0401': 'PROPATRIA', '0402': 'UPATA', '0102': 'VALENCIA', '0206': 'VALERA',
        '0104': 'MARACAY', '0208': 'TIGRE', '0209': 'MARACAIBO', '0210': 'BOLIVAR', '0211': 'CARORA',
        '0212': 'ANACO', '0213': 'VIGIA', '0214': 'CUMANA', '0215': 'SAN FERNANDO', '0216': 'VALLES'
    };

    // Elementos del DOM
    const modal = document.getElementById('stockModal');
    const modalTiendaNombre = document.getElementById('modalTiendaNombre');
    const modalProductTableBody = document.getElementById('modalProductTableBody');
    const searchInputModal = document.getElementById('searchProductModalInput');

    // 2. FUNCIÓN PARA LLAMAR AL API
    async function obtenerStockTienda(codigo, nombre) {
        // Mostrar Modal de Carga con SweetAlert2
        Swal.fire({
            title: 'Consultando Inventario',
            html: `Obteniendo datos de <b>${nombre}</b>...`,
            allowOutsideClick: false,
            didOpen: () => {
                Swal.showLoading();
            }
        });

        try {
            const response = await fetch('/stock', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    nsucursal: codigo,
                    ntienda: nombre
                })
            });

            if (!response.ok) throw new Error('Error al obtener datos del servidor');

            const data = await response.json();
            
            // Guardamos en el estado global
            productosActuales = data;

            // Cerramos el cargador de SweetAlert
            Swal.close();

            // Abrimos el modal de la interfaz
            abrirModalInterfaz(codigo, nombre);

        } catch (error) {
            console.error(error);
            Swal.fire({
                icon: 'error',
                title: 'Error de conexión',
                text: 'No se pudo obtener el stock de esta sucursal.',
                confirmButtonColor: '#10b981'
            });
        }
    }

    // 3. RENDERIZADO DE LA TABLA (Maneja las claves de tu API)
    function renderModalProductTable(filterText = '') {
        const lowerFilter = filterText.toLowerCase().trim();
        
        const filteredProducts = productosActuales.filter(prod => 
            prod.Codigo.toLowerCase().includes(lowerFilter) || 
            prod.Descri.toLowerCase().includes(lowerFilter)
        );

        if (filteredProducts.length === 0) {
            modalProductTableBody.innerHTML = `
                <tr>
                    <td colspan="3" class="py-10 text-center text-slate-400">
                        <i class="fas fa-search-slash text-3xl mb-2 block opacity-50"></i>
                        No se encontraron coincidencias
                    </td>
                </tr>`;
            return;
        }

        modalProductTableBody.innerHTML = filteredProducts.map(prod => `
            <tr class="hover:bg-emerald-50/40 transition fade-row">
                <td class="px-5 py-3 font-mono text-xs font-semibold text-slate-700">${prod.Codigo}</td>
                <td class="px-5 py-3 text-slate-700 text-xs">${prod.Descri}</td>
                <td class="px-5 py-3 text-right font-bold ${prod.Stock > 0 ? 'text-emerald-700' : 'text-rose-500'}">
                    ${prod.Stock.toLocaleString('es-ES')} ud
                </td>
            </tr>
        `).join('');
    }

    // 4. CONTROL DEL MODAL DE UI
    function abrirModalInterfaz(codigo, nombre) {
        modalTiendaNombre.innerHTML = `${nombre} <span class="text-sm font-normal text-slate-400"> (${codigo})</span>`;
        searchInputModal.value = '';
        renderModalProductTable('');
        
        modal.classList.remove('hidden');
        const modalContent = modal.querySelector('.modal-content-init');
        setTimeout(() => {
            modalContent.classList.replace('scale-95', 'scale-100');
            modalContent.classList.replace('opacity-0', 'opacity-100');
        }, 10);
    }

    function cerrarModal() {
        const modalContent = modal.querySelector('.modal-content-init');
        modalContent.classList.replace('scale-100', 'scale-95');
        modalContent.classList.replace('opacity-100', 'opacity-0');
        setTimeout(() => modal.classList.add('hidden'), 200);
    }

    // 5. INICIALIZACIÓN
    function init() {
        // Renderizar Grilla de Tiendas
        const storeGrid = document.getElementById('storeGrid');
        storeGrid.innerHTML = Object.entries(STORES).map(([code, name]) => `
            <div class="store-card rounded-xl p-4 shadow-sm hover:shadow-lg transition-all duration-200 bg-white/80 border border-slate-200/60" 
                 onclick="window.consultarTienda('${code}', '${name}')">
                <div class="flex justify-between items-start">
                    <span class="text-xs font-mono bg-slate-100/80 px-2 py-1 rounded-lg text-slate-600 font-medium">${code}</span>
                    <div class="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center text-[#29336d]">
                        <i class="fas fa-store text-sm"></i>
                    </div>
                </div>
                <h3 class="font-bold text-slate-800 mt-3 text-lg truncate">${name}</h3>
            </div>
        `).join('');

        // Eventos de búsqueda
        searchInputModal.addEventListener('input', (e) => renderModalProductTable(e.target.value));

        // Eventos de cierre
        document.getElementById('closeModalBtn').onclick = cerrarModal;
        document.getElementById('closeModalFooterBtn').onclick = cerrarModal;
        
        // Exponer función globalmente para el onclick
        window.consultarTienda = obtenerStockTienda;

        // Cerrar al hacer clic fuera
        modal.onclick = (e) => { if (e.target === modal) cerrarModal(); };
    }

    init();
})();