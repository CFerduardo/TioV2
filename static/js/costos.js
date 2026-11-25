document.addEventListener("DOMContentLoaded", () => {
    const dropZone = document.getElementById("drop-zone-costos");
    const fileInput = document.getElementById("file-input-costos");
    const analysisSection = document.getElementById("analysis-section");
    const btnExecute = document.getElementById("btn-execute-costos");
    
    let currentAnalysis = null;

    if(!dropZone) return; // Evitar errores si no estamos en esa sección

    // Eventos de subida
    fileInput.addEventListener("change", () => {
        if (fileInput.files.length) handleUpload(fileInput.files[0]);
    });

    async function handleUpload(file) {
        toggleLoader(true);
        const formData = new FormData();
        formData.append("file", file);

        try {
            const response = await fetch("/analyze", {
                method: "POST",
                body: formData
            });
            const data = await response.json();
            
            if(data.error) throw new Error(data.error);
            
            showAnalysis(data);
        } catch (error) {
            Swal.fire("Error", "No se pudo analizar el archivo: " + error.message, "error");
        } finally {
            toggleLoader(false);
        }
    }

    function showAnalysis(data) {
        currentAnalysis = data;
        analysisSection.style.display = "block";
        dropZone.style.display = "none";

        document.getElementById("count-ready").innerText = data.ready.length;
        document.getElementById("count-promo").innerText = data.alerts_promo.length;
        document.getElementById("count-loss").innerText = data.alerts_loss.length;
        document.getElementById("count-notfound").innerText = data.not_found.length;

        const alertsContainer = document.getElementById("alerts-container-costos");
        alertsContainer.innerHTML = "";

        if (data.alerts_loss.length > 0) {
            alertsContainer.innerHTML += `
                <div class="alert-msg" style="background: rgba(231, 76, 60, 0.2); border-left: 5px solid #e74c3c; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                    <i class="fas fa-exclamation-triangle"></i> <b>Atención:</b> ${data.alerts_loss.length} productos tienen precio menor al costo.
                </div>`;
        }

        btnExecute.disabled = data.ready.length === 0;
    }

    btnExecute.addEventListener("click", async () => {
        if (!currentAnalysis || currentAnalysis.ready.length === 0) return;

        const result = await Swal.fire({
            title: '¿Confirmar actualización?',
            text: `Se actualizarán ${currentAnalysis.ready.length} productos en CENTRAL e IMPORTADORA.`,
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#10b981',
            cancelButtonColor: '#d33',
            confirmButtonText: 'Sí, actualizar todo',
            cancelButtonText: 'Revisar de nuevo'
        });

        if (result.isConfirmed) {
            toggleLoader(true);
            try {
                const payload = currentAnalysis.ready.map(p => {
                    const original = currentAnalysis.full_data.find(item => item.codigo === p.codigo);
                    return {
                        codigo: p.codigo,
                        precio: p.precio,
                        costo: original ? original.costo : 0,
                        impuesto: original ? original.impuesto : 16
                    };
                });

                const response = await fetch("/execute", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ productos: payload })
                });

                const data = await response.json();
                // Ocultamos el loader inmediatamente al recibir respuesta
                toggleLoader(false);

                if (data.status === 'success') {
                    await Swal.fire('¡Éxito!', data.message, 'success');
                    location.reload();
                } else if (data.status === 'partial_error') {
                    await Swal.fire('Sincronización Parcial', data.message, 'warning');
                } else {
                    throw new Error(data.error || data.message);
                }
            } catch (error) {
                Swal.fire("Error Server", error.message, "error");
            } finally {
                toggleLoader(false);
            }
        }
    });
});