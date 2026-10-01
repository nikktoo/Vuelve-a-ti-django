// Funcionalidades interactivas de 'Vuelve a ti'

document.addEventListener('DOMContentLoaded', () => {
  // 1. Asistente en 2 Pasos para Reportar Objeto
  const paso1 = document.getElementById('wizard-paso-1');
  const paso2 = document.getElementById('wizard-paso-2');
  const btnIrPaso2 = document.getElementById('btn-ir-paso-2');
  const btnVolverPaso1 = document.getElementById('btn-volver-paso-1');

  if (paso1 && paso2 && btnIrPaso2 && btnVolverPaso1) {
    btnIrPaso2.addEventListener('click', () => {
      // Validar campos mínimos del paso 1
      const contactoNombre = document.getElementById('id_contacto_nombre');
      if (contactoNombre && contactoNombre.required && !contactoNombre.value.trim()) {
        alert('Por favor indica tu nombre completo de contacto antes de continuar.');
        contactoNombre.focus();
        return;
      }

      const subcategoria = document.getElementById('id_subcategoria');
      const categoria = document.getElementById('id_categoria');
      if (subcategoria && !subcategoria.value.trim()) {
        alert('Por favor indica qué objeto es antes de continuar.');
        subcategoria.focus();
        return;
      }
      paso1.style.display = 'none';
      paso2.style.display = 'block';
      const step2Indicator = document.getElementById('indicator-step-2');
      if (step2Indicator) step2Indicator.classList.add('active');
    });

    btnVolverPaso1.addEventListener('click', () => {
      paso2.style.display = 'none';
      paso1.style.display = 'block';
    });
  }

  // 2. Copiar Token de Retiro al Portapapeles
  const btnCopiarToken = document.querySelectorAll('.btn-copiar-token');
  btnCopiarToken.forEach(btn => {
    btn.addEventListener('click', () => {
      const token = btn.getAttribute('data-token');
      if (token) {
        navigator.clipboard.writeText(token).then(() => {
          const originalText = btn.innerText;
          btn.innerText = '¡Copiado!';
          setTimeout(() => { btn.innerText = originalText; }, 2000);
        });
      }
    });
  });

  // 3. Filtro en Vivo para la Tabla de Conserjería
  const inputFiltroInventario = document.getElementById('filtro-inventario-rapido');
  if (inputFiltroInventario) {
    inputFiltroInventario.addEventListener('keyup', (e) => {
      const term = e.target.value.toLowerCase();
      const filas = document.querySelectorAll('#tabla-inventario tbody tr');
      filas.forEach(fila => {
        const texto = fila.innerText.toLowerCase();
        fila.style.display = texto.includes(term) ? '' : 'none';
      });
    });
  }

  // 4. Marcar notificaciones como leídas
  const btnLimpiarNotificaciones = document.getElementById('btn-marcar-notificaciones');
  if (btnLimpiarNotificaciones) {
    btnLimpiarNotificaciones.addEventListener('click', (e) => {
      e.preventDefault();
      fetch('/notificaciones/marcar-leidas/', {
        method: 'POST',
        headers: {
          'X-CSRFToken': getCookie('csrftoken'),
          'Content-Type': 'application/json'
        }
      }).then(res => res.json()).then(data => {
        if (data.status === 'ok') {
          const badge = document.getElementById('badge-notificaciones-count');
          if (badge) badge.style.display = 'none';
          const list = document.getElementById('lista-notificaciones');
          if (list) list.innerHTML = '<li class="p-2 text-muted text-center">No tienes notificaciones pendientes.</li>';
        }
      });
    });
  }
});

// Helper para leer cookies (CSRF token)
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
