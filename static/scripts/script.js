document.getElementById('sync-btn').addEventListener('click', async function() {
    const btn = this;
    const statusEl = document.getElementById('sync-status');
   
    const tablaEmpleados = document.getElementById('tabla-empleados');
    btn.disabled = true;
    statusEl.textContent = "Sincronizando...";
    statusEl.className = "ms-2 text-warning";

    try {
        const response = await fetch('/marcaje/sync-empleados/', {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),  // ¡Nueva línea importante!
            },
            credentials: 'same-origin'  // Asegura que se envíen las cookies
        });
        
        console.log(response)

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        
        if (data.status === 'success') {
            statusEl.textContent = `✓ Listo: ${data.creados} nuevos, ${data.actualizados} actualizados`;
          
            statusEl.className = "ms-2 text-success";

             // Actualiza la tabla con los nuevos datos
             if (data.empleados) {
                const empleados = JSON.parse(data.empleados);
                actualizarTabla(empleados);
            }
        } else {
            throw new Error(data.message || "Error desconocido");
        }
    } catch (error) {
        console.error('Error en sincronización:', error);
        statusEl.textContent = `✗ Error: ${error.message}`;
        statusEl.className = "ms-2 text-danger";
    } finally {
        btn.disabled = false;
    }
});

// Función para obtener el token CSRF (añade esto al mismo archivo)
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

function actualizarTabla(empleados) {
    const tbody = document.querySelector('#tabla-empleados tbody');
    tbody.innerHTML = '';  // Limpia la tabla
    
    empleados.forEach(emp => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${emp.fields.sucursal}</td>  <!-- Ahora sí mostrará el nombre -->
            <td>${emp.fields.codigo}</td>
            <td>${emp.fields.nombre}</td>
            <td>${emp.fields.departamento}</td>
        `;
        tbody.appendChild(row);
    });
}

let table = $('#tabla-empleados').DataTable({

    pageLength: 10,
    lengthMenu: [10, 25, 50, 100],
  });