document.addEventListener('DOMContentLoaded', function() {
    const btnValidar = document.getElementById('btn-validar');
    
    btnValidar.addEventListener('click', function() {
        const sucursalId = document.getElementById('sucursal').value;
        const fecha = document.getElementById('fecha').value;
        
        if (!fecha) {
            alert('Por favor selecciona una fecha');
            return;
        }
        
        btnValidar.disabled = true;
        btnValidar.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Validando...';
        
        // Configurar CSRF token
      
        
        fetch('/marcaje/validar-asistencia/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `sucursal=${sucursalId}&fecha=${fecha}`
        })
        .then(response => {
            console.log('Status:', response.status); // ← Agrega esto
            console.log('Content-Type:', response.headers.get('content-type')); // ← Y esto
            if (!response.ok) {
                return response.text().then(text => { throw new Error(text) }); // ← Muestra el error real
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            
            const tbody = document.querySelector('#tabla-resultados tbody');
            tbody.innerHTML = '';
            
            data.data.forEach(empleado => {
                // let fecha = '--';
                // let hora = '--';
                
                // if (empleado.fecha_hora) {
                //     const marcaje = new Date(empleado.fecha_hora);
                //     fecha = marcaje.toLocaleDateString('en-EN'); // dd/mm/yyyy
                //     hora = marcaje.toLocaleTimeString('en-EN', { hour: '2-digit', minute: '2-digit' });
                // }

                const row = document.createElement('tr');   
                if (!empleado.asistio) {
                    row.classList.add('table-danger');
                }
                
                row.innerHTML = `
                    <td>${empleado.fecha}</td>
                    <td>${empleado.sucursal}</td>
                    <td>${empleado.codigo}</td>
                    <td>${empleado.nombre}</td>
                    <td>${empleado.departamento}</td>
                    <td>${empleado.entrada}</td>
                    <td>${empleado.salida}</td>
                    <td class="text-center ${empleado.asistio ? 'bg-success' : 'bg-danger'} text-white">
                        ${empleado.asistio ? 'I' : ''}
                    </td>
                `;
                
                tbody.appendChild(row);
            });
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error: ' + error.message);
        })
        .finally(() => {
            btnValidar.disabled = false;
            btnValidar.innerHTML = '<i class="fas fa-check-circle"></i> Validar';
        });
    });
});

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

