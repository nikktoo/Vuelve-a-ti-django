from .models import Notificacion

def notificaciones_context(request):
    """Provee las notificaciones no leídas y conteo global para la barra superior."""
    if request.user.is_authenticated:
        no_leidas = Notificacion.objects.filter(usuario=request.user, leida=False).order_by('-fecha_creacion')
        return {
            'notificaciones_no_leidas': no_leidas[:5],
            'conteo_notificaciones': no_leidas.count(),
        }
    return {
        'notificaciones_no_leidas': [],
        'conteo_notificaciones': 0,
    }
