from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, Recinto, CategoriaObjeto, Objeto, Coincidencia, MensajeChat, Notificacion, Incidencia


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Información "Vuelve a Ti"', {'fields': ('rol', 'telefono', 'departamento_torre')}),
    )
    list_display = ('username', 'email', 'get_full_name', 'rol', 'departamento_torre', 'is_staff')
    list_filter = ('rol', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'departamento_torre')


@admin.register(Recinto)
class RecintoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo', 'encargado', 'activo')
    list_filter = ('tipo', 'activo')
    search_fields = ('nombre', 'descripcion')


@admin.register(CategoriaObjeto)
class CategoriaObjetoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'icono', 'descripcion')
    search_fields = ('nombre',)


@admin.register(Objeto)
class ObjetoAdmin(admin.ModelAdmin):
    list_display = (
        'codigo_seguimiento',
        'subcategoria',
        'tipo_registro',
        'categoria',
        'color_principal',
        'ubicacion',
        'ubicacion_bodega',
        'estado',
        'fecha_suceso',
        'fecha_registro',
    )
    list_filter = ('tipo_registro', 'estado', 'categoria', 'ubicacion')
    search_fields = ('codigo_seguimiento', 'subcategoria', 'marca', 'color_principal', 'descripcion_publica')
    readonly_fields = ('codigo_seguimiento', 'token_retiro', 'fecha_registro')


@admin.register(Coincidencia)
class CoincidenciaAdmin(admin.ModelAdmin):
    list_display = (
        '__str__',
        'porcentaje_similitud',
        'estado',
        'fecha_coincidencia'
    )
    list_filter = ('estado',)
    readonly_fields = ('fecha_coincidencia',)


@admin.register(MensajeChat)
class MensajeChatAdmin(admin.ModelAdmin):
    list_display = ('coincidencia', 'emisor', 'fecha_envio', 'leido')
    list_filter = ('leido',)


@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'titulo', 'leida', 'fecha_creacion')
    list_filter = ('leida',)


@admin.register(Incidencia)
class IncidenciaAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'tipo', 'objeto', 'resuelta', 'fecha_reporte')
    list_filter = ('tipo', 'resuelta')
