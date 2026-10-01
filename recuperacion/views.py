from datetime import date, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q, Avg, F
from django.http import JsonResponse, HttpResponseForbidden
from django.utils import timezone

from .models import (
    Usuario, Recinto, CategoriaObjeto, Objeto, Coincidencia,
    MensajeChat, Notificacion, Incidencia
)
from .forms import (
    RegistroUsuarioForm, LoginFormPersonalizado, ObjetoPerdidoForm,
    ObjetoEncontradoForm, ValidacionEntregaForm, IncidenciaForm, RecintoForm
)
from .matching import ejecutar_motor_coincidencias


def home(request):
    """Página de inicio y presentación de 'Vuelve a ti' en Edificio Plaza Centro."""
    total_recuperados = Objeto.objects.filter(estado='entregado').count()
    total_custodia = Objeto.objects.filter(tipo_registro='encontrado', estado__in=['registrado', 'en_verificacion']).count()
    total_recintos = Recinto.objects.filter(activo=True).count()
    categorias = CategoriaObjeto.objects.all()

    return render(request, 'recuperacion/home.html', {
        'total_recuperados': total_recuperados,
        'total_custodia': total_custodia,
        'total_recintos': total_recintos,
        'categorias': categorias,
    })


def registro_view(request):
    """Registro de nuevo usuario respetando roles y privacidad."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"¡Bienvenido(a) a Vuelve a ti, {user.first_name or user.username}!")
            return redirect('dashboard')
    else:
        form = RegistroUsuarioForm()

    return render(request, 'recuperacion/registro.html', {'form': form})


def login_view(request):
    """Inicio de sesión adaptado al diseño de los mockups."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = LoginFormPersonalizado(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Sesión iniciada con éxito.")
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            messages.error(request, "Credenciales incorrectas. Por favor verifica tu usuario y contraseña.")
    else:
        form = LoginFormPersonalizado()

    return render(request, 'recuperacion/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "Has cerrado tu sesión de forma segura.")
    return redirect('home')


@login_required
def dashboard(request):
    """
    Panel central inteligente:
    - Redirige o despliega vista según el rol (Residente, Conserje o Admin).
    """
    user = request.user
    
    # Objetos del usuario
    mis_perdidos = Objeto.objects.filter(usuario_reporta=user, tipo_registro='perdido')
    mis_encontrados = Objeto.objects.filter(usuario_reporta=user, tipo_registro='encontrado')
    
    # Coincidencias relevantes para el usuario
    coincidencias = Coincidencia.objects.filter(
        Q(objeto_perdido__usuario_reporta=user) | Q(objeto_encontrado__usuario_reporta=user)
    ).exclude(estado='descartada').select_related('objeto_perdido', 'objeto_encontrado')[:5]

    # Estadísticas rápidas para conserje o admin
    stats_conserje = {}
    if user.es_conserje_o_admin():
        stats_conserje = {
            'en_bodega': Objeto.objects.filter(tipo_registro='encontrado', estado='registrado').count(),
            'en_verificacion': Objeto.objects.filter(estado='en_verificacion').count(),
            'entregados_recientes': Objeto.objects.filter(estado='entregado').order_by('-fecha_entrega')[:5],
            'total_perdidos_activos': Objeto.objects.filter(tipo_registro='perdido', estado='registrado').count(),
        }

    return render(request, 'recuperacion/dashboard.html', {
        'mis_perdidos': mis_perdidos,
        'mis_encontrados': mis_encontrados,
        'coincidencias': coincidencias,
        'stats_conserje': stats_conserje,
    })


@login_required
def reportar_perdido(request):
    """
    RF-02: Registrar objeto perdido mediante asistente estructurado en 2 pasos:
    Paso 1: Clasificación y Ubicación
    Paso 2: Descripción textual y Clave de Verificación Privada
    """
    if request.method == 'POST':
        form = ObjetoPerdidoForm(request.POST)
        if form.is_valid():
            objeto = form.save(commit=False)
            objeto.tipo_registro = 'perdido'
            objeto.usuario_reporta = request.user
            objeto.estado = 'registrado'
            objeto.save()

            # Ejecutar motor de coincidencias automáticas (RF-05)
            coincidencias = ejecutar_motor_coincidencias(objeto)

            if coincidencias:
                messages.success(
                    request,
                    f"¡Reporte registrado exitosamente! Hemos detectado {len(coincidencias)} posible(s) coincidencia(s) en custodia."
                )
                return redirect('coincidencias_lista')
            else:
                messages.success(
                    request,
                    f"Tu objeto ha sido registrado con código {objeto.codigo_seguimiento}. Te notificaremos automáticamente ante cualquier hallazgo."
                )
                return redirect('detalle_objeto', pk=objeto.pk)
    else:
        form = ObjetoPerdidoForm()

    return render(request, 'recuperacion/reportar_perdido.html', {'form': form})


@login_required
def reportar_hallazgo(request):
    """
    RF-03: Registrar objeto encontrado (por vecino o conserje).
    Si es conserje, se solicita obligatoriamente el casillero o locker de bodega.
    """
    es_conserje = request.user.es_conserje_o_admin()

    if request.method == 'POST':
        form = ObjetoEncontradoForm(request.POST)
        if form.is_valid():
            objeto = form.save(commit=False)
            objeto.tipo_registro = 'encontrado'
            objeto.usuario_reporta = request.user
            objeto.estado = 'registrado'
            
            # Si un residente lo encontró sin asignar casillero, se define custodia en recepción
            if not objeto.ubicacion_bodega:
                objeto.ubicacion_bodega = "Entregado a Conserjería Central"

            objeto.save()

            # Motor de coincidencias
            coincidencias = ejecutar_motor_coincidencias(objeto)

            if coincidencias:
                messages.success(
                    request,
                    f"¡Objeto ingresado! El sistema detectó {len(coincidencias)} vecino(s) buscando un artículo similar."
                )
            else:
                messages.success(
                    request,
                    f"Objeto registrado en inventario con código {objeto.codigo_seguimiento}."
                )

            if es_conserje:
                return redirect('conserjeria_panel')
            return redirect('detalle_objeto', pk=objeto.pk)
    else:
        # Prellenar ubicación por defecto si es conserje
        initial_data = {}
        if es_conserje:
            initial_data['ubicacion_bodega'] = 'Bodega Central - Estante A'
        form = ObjetoEncontradoForm(initial=initial_data)

    return render(request, 'recuperacion/reportar_hallazgo.html', {
        'form': form,
        'es_conserje': es_conserje
    })


def buscar_objetos(request):
    """
    RF-04: Búsqueda y filtrado público de objetos garantizando privacidad.
    Muestra solo descripción pública y ubicación sin datos personales de los usuarios.
    """
    query = request.GET.get('q', '').strip()
    categoria_id = request.GET.get('categoria', '')
    ubicacion_id = request.GET.get('ubicacion', '')
    tipo_filtro = request.GET.get('tipo', 'encontrado')  # Por defecto busca objetos en custodia

    objetos = Objeto.objects.filter(estado__in=['registrado', 'en_verificacion'])

    if tipo_filtro in ['perdido', 'encontrado']:
        objetos = objetos.filter(tipo_registro=tipo_filtro)

    if categoria_id:
        objetos = objetos.filter(categoria_id=categoria_id)

    if ubicacion_id:
        objetos = objetos.filter(ubicacion_id=ubicacion_id)

    if query:
        objetos = objetos.filter(
            Q(subcategoria__icontains=query) |
            Q(descripcion_publica__icontains=query) |
            Q(color_principal__icontains=query) |
            Q(marca__icontains=query) |
            Q(codigo_seguimiento__icontains=query)
        )

    categorias = CategoriaObjeto.objects.all()
    recintos = Recinto.objects.filter(activo=True)

    return render(request, 'recuperacion/buscar.html', {
        'objetos': objetos,
        'categorias': categorias,
        'recintos': recintos,
        'query': query,
        'categoria_sel': categoria_id,
        'ubicacion_sel': ubicacion_id,
        'tipo_filtro': tipo_filtro,
        'total_resultados': objetos.count(),
    })


@login_required
def detalle_objeto(request, pk):
    """
    Ficha del objeto.
    Control estricto de privacidad: La clave_verificacion_privada y token_retiro
    solo son visibles por el dueño del reporte o por personal de conserjería/admin.
    """
    objeto = get_object_or_404(Objeto, pk=pk)
    es_dueño = (objeto.usuario_reporta == request.user)
    es_personal = request.user.es_conserje_o_admin()

    # Coincidencias relacionadas
    coincidencias = []
    if es_dueño or es_personal:
        if objeto.tipo_registro == 'perdido':
            coincidencias = objeto.coincidencias_como_perdido.all()
        else:
            coincidencias = objeto.coincidencias_como_encontrado.all()

    return render(request, 'recuperacion/detalle_objeto.html', {
        'objeto': objeto,
        'es_dueño': es_dueño,
        'es_personal': es_personal,
        'coincidencias': coincidencias,
    })


@login_required
def conserjeria_panel(request):
    """
    Panel Web para Encargados de Conserjería y Recepción:
    - Inventario permanente en bodega/lockers
    - Búsqueda en tiempo real por casillero, categoría o código
    - Ingreso exprés y acceso directo a verificación de entrega
    """
    if not request.user.es_conserje_o_admin():
        messages.error(request, "Acceso restringido al personal de conserjería y administración.")
        return redirect('dashboard')

    query = request.GET.get('q', '').strip()
    filtro_estado = request.GET.get('estado', '')

    inventario = Objeto.objects.filter(tipo_registro='encontrado').select_related(
        'categoria', 'ubicacion', 'usuario_reporta'
    )

    if filtro_estado:
        inventario = inventario.filter(estado=filtro_estado)

    if query:
        inventario = inventario.filter(
            Q(codigo_seguimiento__icontains=query) |
            Q(subcategoria__icontains=query) |
            Q(ubicacion_bodega__icontains=query) |
            Q(descripcion_publica__icontains=query)
        )

    # Conteos rápidos de mesón
    conteos = {
        'en_custodia': Objeto.objects.filter(tipo_registro='encontrado', estado='registrado').count(),
        'en_verificacion': Objeto.objects.filter(tipo_registro='encontrado', estado='en_verificacion').count(),
        'entregados': Objeto.objects.filter(tipo_registro='encontrado', estado='entregado').count(),
    }

    form_expres = ObjetoEncontradoForm()

    return render(request, 'recuperacion/conserjeria_panel.html', {
        'inventario': inventario,
        'conteos': conteos,
        'form_expres': form_expres,
        'query': query,
        'filtro_estado': filtro_estado,
    })


@login_required
def validar_entrega(request, pk):
    """
    RF-06 y RF-09: Módulo de Verificación y Entrega Física en Conserjería.
    El conserje contrasta la 'Clave de Verificación Privada' con el objeto físico
    y valida el token de retiro de 6 dígitos que presenta el residente.
    """
    if not request.user.es_conserje_o_admin():
        messages.error(request, "Acceso exclusivo para conserjería.")
        return redirect('dashboard')

    objeto = get_object_or_404(Objeto, pk=pk)

    # Si es un objeto perdido, buscamos si hay objeto encontrado emparejado
    objeto_custodiado = objeto
    objeto_reclamo = objeto

    if objeto.tipo_registro == 'perdido':
        coincidencia = Coincidencia.objects.filter(objeto_perdido=objeto).first()
        if coincidencia:
            objeto_custodiado = coincidencia.objeto_encontrado
    else:
        coincidencia = Coincidencia.objects.filter(objeto_encontrado=objeto).first()
        if coincidencia:
            objeto_reclamo = coincidencia.objeto_perdido

    if request.method == 'POST':
        form = ValidacionEntregaForm(request.POST)
        if form.is_valid():
            token_ingresado = form.cleaned_data['token_retiro'].strip()
            observaciones = form.cleaned_data['observaciones']

            # El token válido puede ser el del objeto perdido que presenta el residente
            token_esperado = objeto_reclamo.token_retiro

            if token_ingresado == token_esperado:
                # Actualizar estado a ENTREGADO
                objeto_custodiado.estado = 'entregado'
                objeto_custodiado.entregado_a = objeto_reclamo.usuario_reporta
                objeto_custodiado.entregado_por = request.user
                objeto_custodiado.fecha_entrega = timezone.now()
                objeto_custodiado.observaciones_entrega = observaciones
                objeto_custodiado.save()

                if objeto_reclamo != objeto_custodiado:
                    objeto_reclamo.estado = 'entregado'
                    objeto_reclamo.entregado_a = objeto_reclamo.usuario_reporta
                    objeto_reclamo.entregado_por = request.user
                    objeto_reclamo.fecha_entrega = timezone.now()
                    objeto_reclamo.observaciones_entrega = observaciones
                    objeto_reclamo.save()

                if coincidencia:
                    coincidencia.estado = 'resuelta'
                    coincidencia.save()

                # Notificar al dueño
                Notificacion.objects.create(
                    usuario=objeto_reclamo.usuario_reporta,
                    titulo="¡Objeto devuelto formalmente!",
                    mensaje=f"Tu objeto '{objeto_reclamo.subcategoria}' ha sido entregado en conserjería con éxito.",
                    url_destino=f"/objeto/{objeto_custodiado.id}/"
                )

                messages.success(request, f"¡Entrega confirmada con éxito! El objeto {objeto_custodiado.codigo_seguimiento} fue marcado como ENTREGADO.")
                return redirect('conserjeria_panel')
            else:
                messages.error(request, f"Token inválido. El código '{token_ingresado}' no coincide con el token de retiro del propietario.")
    else:
        form = ValidacionEntregaForm()

    return render(request, 'recuperacion/validar_entrega.html', {
        'objeto': objeto_custodiado,
        'objeto_reclamo': objeto_reclamo,
        'coincidencia': coincidencia if 'coincidencia' in locals() else None,
        'form': form,
    })


@login_required
def coincidencias_lista(request):
    """
    Lista de sugerencias automáticas de coincidencia para el usuario o para conserjes.
    """
    user = request.user
    if user.es_conserje_o_admin():
        coincidencias = Coincidencia.objects.all().select_related(
            'objeto_perdido', 'objeto_encontrado', 'objeto_perdido__categoria'
        )
    else:
        coincidencias = Coincidencia.objects.filter(
            Q(objeto_perdido__usuario_reporta=user) | Q(objeto_encontrado__usuario_reporta=user)
        ).select_related('objeto_perdido', 'objeto_encontrado', 'objeto_perdido__categoria')

    return render(request, 'recuperacion/coincidencias_lista.html', {
        'coincidencias': coincidencias,
    })


@login_required
def detalle_coincidencia(request, pk):
    """
    Detalle comparativo de la coincidencia y chat seguro para coordinar.
    """
    coincidencia = get_object_or_404(Coincidencia, pk=pk)
    user = request.user

    # Verificar permisos de acceso a la coincidencia
    es_involucrado = (
        coincidencia.objeto_perdido.usuario_reporta == user or
        coincidencia.objeto_encontrado.usuario_reporta == user or
        user.es_conserje_o_admin()
    )
    if not es_involucrado:
        return HttpResponseForbidden("No tienes autorización para ver esta coincidencia.")

    mensajes = coincidencia.mensajes.all().select_related('emisor')

    # Si es POST, procesar nuevo mensaje de chat
    if request.method == 'POST':
        texto = request.POST.get('mensaje', '').strip()
        if texto:
            MensajeChat.objects.create(
                coincidencia=coincidencia,
                emisor=user,
                mensaje=texto
            )
            # Notificar al receptor
            otro_usuario = (
                coincidencia.objeto_encontrado.usuario_reporta
                if coincidencia.objeto_perdido.usuario_reporta == user
                else coincidencia.objeto_perdido.usuario_reporta
            )
            Notificacion.objects.create(
                usuario=otro_usuario,
                titulo=f"Nuevo mensaje sobre tu objeto ({coincidencia.objeto_perdido.subcategoria})",
                mensaje=f"{user.first_name or user.username}: {texto[:60]}...",
                url_destino=f"/coincidencias/{coincidencia.id}/"
            )
            return redirect('detalle_coincidencia', pk=pk)

    return render(request, 'recuperacion/detalle_coincidencia.html', {
        'coincidencia': coincidencia,
        'mensajes': mensajes,
    })


@login_required
def metricas_view(request):
    """
    RF-10: Analítica y Reportes Estadísticos para la administración del Edificio Plaza Centro:
    - Tasa global de recuperación (% devuelto vs total)
    - Categorías con mayor frecuencia de extravío
    - Zonas y recintos críticos del edificio
    - Tiempos medios de retención
    """
    if not request.user.es_conserje_o_admin():
        messages.error(request, "Acceso exclusivo para administración.")
        return redirect('dashboard')

    total_perdidos = Objeto.objects.filter(tipo_registro='perdido').count()
    total_encontrados = Objeto.objects.filter(tipo_registro='encontrado').count()
    total_entregados = Objeto.objects.filter(estado='entregado').count()

    tasa_recuperacion = 0.0
    if total_encontrados > 0:
        tasa_recuperacion = round((total_entregados / total_encontrados) * 100, 1)

    # Top categorías con más objetos
    categorias_top = CategoriaObjeto.objects.annotate(
        total_items=Count('objeto')
    ).order_by('-total_items')[:5]

    # Zonas críticas (áreas comunes con más pérdidas/hallazgos)
    zonas_criticas = Recinto.objects.annotate(
        total_reportes=Count('objetos_registrados')
    ).order_by('-total_reportes')[:5]

    # Últimos objetos entregados
    entregados_recientes = Objeto.objects.filter(
        estado='entregado'
    ).select_related('categoria', 'entregado_a', 'entregado_por').order_by('-fecha_entrega')[:10]

    return render(request, 'recuperacion/metricas.html', {
        'total_perdidos': total_perdidos,
        'total_encontrados': total_encontrados,
        'total_entregados': total_entregados,
        'tasa_recuperacion': tasa_recuperacion,
        'categorias_top': categorias_top,
        'zonas_criticas': zonas_criticas,
        'entregados_recientes': entregados_recientes,
    })


@login_required
def historial_avanzado(request):
    """
    RF-11: Historial avanzado y auditoría de movimientos del recinto.
    """
    if not request.user.es_conserje_o_admin():
        messages.error(request, "Acceso exclusivo para administración.")
        return redirect('dashboard')

    objetos = Objeto.objects.all().select_related(
        'categoria', 'ubicacion', 'usuario_reporta', 'entregado_a'
    ).order_by('-fecha_registro')

    estado = request.GET.get('estado')
    tipo = request.GET.get('tipo')
    recinto = request.GET.get('recinto')

    if estado:
        objetos = objetos.filter(estado=estado)
    if tipo:
        objetos = objetos.filter(tipo_registro=tipo)
    if recinto:
        objetos = objetos.filter(ubicacion_id=recinto)

    recintos = Recinto.objects.all()

    return render(request, 'recuperacion/historial_avanzado.html', {
        'objetos': objetos,
        'recintos': recintos,
        'estado_sel': estado,
        'tipo_sel': tipo,
        'recinto_sel': recinto,
    })


@login_required
def reportar_incidencia(request, objeto_id=None):
    """
    RF-12: Reportar información incorrecta, falsos datos o anomalías.
    """
    objeto = None
    if objeto_id:
        objeto = get_object_or_404(Objeto, pk=objeto_id)

    if request.method == 'POST':
        form = IncidenciaForm(request.POST)
        if form.is_valid():
            incidencia = form.save(commit=False)
            incidencia.usuario = request.user
            incidencia.objeto = objeto
            incidencia.save()
            messages.success(request, "Tu reporte de incidencia fue enviado a la administración. Gracias por velar por la seguridad de la comunidad.")
            return redirect('dashboard')
    else:
        form = IncidenciaForm()

    return render(request, 'recuperacion/reportar_incidencia.html', {
        'form': form,
        'objeto': objeto,
    })


@login_required
def gestion_recintos(request):
    """
    RF-08: Gestión de recintos, sectores y casetas para el Administrador.
    """
    if not request.user.es_admin():
        messages.error(request, "Solo administradores pueden gestionar recintos.")
        return redirect('dashboard')

    recintos = Recinto.objects.all().select_related('encargado')

    if request.method == 'POST':
        form = RecintoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Nuevo recinto agregado exitosamente.")
            return redirect('gestion_recintos')
    else:
        form = RecintoForm()

    return render(request, 'recuperacion/gestion_recintos.html', {
        'recintos': recintos,
        'form': form,
    })


@login_required
def marcar_notificaciones_leidas(request):
    """Marca las notificaciones del usuario como leídas vía POST."""
    if request.method == 'POST':
        Notificacion.objects.filter(usuario=request.user, leida=False).update(leida=True)
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'invalid method'}, status=400)
