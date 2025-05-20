document.getElementById('sync-btn').addEventListener('click', async function() {
    const btn = this;
    const statusEl = document.getElementById('sync-status');
    const fechaSeleccionada = document.getElementById('fecha-sync').value;
    
    // Configuración inicial
    btn.disabled = true;
    const originalText = btn.innerHTML;
    btn.innerHTML = 'Sincronizando...';
    statusEl.textContent = 'Conectando con el servidor...';
    statusEl.className = 'text-warning';

    try {
        // 1. Enviar petición
        const response = await fetch(`/marcaje/sync-marcaje/?fecha=${fechaSeleccionada}`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Accept': 'application/json'
            }
        });

        // 2. Manejar respuesta
        const data = await response.json();
        
        if (!response.ok || data.status !== 'success') {
            throw new Error(data.message || 'Error en la sincronización');
        }

        // 3. Mostrar resultados
        statusEl.innerHTML = `
            
            ${data.message} | 
            Nuevos: ${data.creados} | 
            Actualizados: ${data.actualizados}
        `;
        statusEl.className = 'text-success';
        
        // 4. Opcional: Procesar los marcajes
        console.log('Datos recibidos:', JSON.parse(data.marcajes));
        
    } catch (error) {
        console.error('Error en sincronización:', error);
        statusEl.innerHTML = `${error.message}`;
        statusEl.className = 'text-danger';
    } finally {
        // Restaurar estado
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
});

// Función auxiliar para CSRF
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

let table = $('#tabla-marcaje').DataTable({
    pageLength: 10,
    lengthMenu: [10, 25, 50, 100],
    scrollY: 400
  });