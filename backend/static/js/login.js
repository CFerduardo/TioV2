async function handleLogin(event) {
    event.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    // Mostrar un loader mientras valida
    Swal.fire({
        title: 'Validando credenciales...',
        allowOutsideClick: false,
        didOpen: () => {
            Swal.showLoading();
        }
    });

    try {
        const response = await fetch('/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();

        if (data.success) {
            localStorage.setItem('cedula', data.cedula);
            localStorage.setItem('usuario', data.usuario);
            localStorage.setItem('departamento', data.departamento);

            Swal.fire({
                icon: 'success',
                title: '¡Bienvenido!',
                text: `Hola, ${data.usuario}`,
                heightAuto: false, // Esta es la línea clave
                timer: 1500,
                showConfirmButton: false
            }).then(() => {
                window.location.href = '/dashboard';
            });
            
        } else {
            Swal.fire({
                icon: 'error',
                title: 'Acceso Denegado',
                heightAuto: false, // Esta es la línea clave
                text: data.message || 'Credenciales inválidas'
            });
        }
    } catch (error) {
        console.error('Error:', error);
        Swal.fire({
            icon: 'error',
            title: 'Error de Conexión',
            text: 'No se pudo establecer contacto con el servidor SQL.',
            heightAuto: false // Esta es la línea clave
        });
    }
}