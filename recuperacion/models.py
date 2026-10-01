import random
import string
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


def generar_codigo_seguimiento():
    """Genera un código único corto, ej: VT-2026-AB12."""
    letras_y_num = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    año = timezone.now().year
    return f"VT-{año}-{letras_y_num}"


def generar_token_retiro():
    """Genera un token de 6 dígitos numéricos para retiro en conserjería."""
    return ''.join(random.choices(string.digits, k=6))


class Usuario(AbstractUser):
    """
    Usuario del sistema con roles definidos:
    - RESIDENTE: Ciudadano / Habitante / Visitante del edificio
    - CONSERJE: Encargado de recepción, conserjería o custodia física
    - ADMIN: Supervisor general de la plataforma y administración del edificio
    """
    ROL_CHOICES = [
        ('residente', 'Residente / Ciudadano'),
        ('conserje', 'Encargado de Recinto / Conserje'),
        ('admin', 'Administrador del Edificio'),
    ]

    rol = models.CharField(max_length=20, choices=ROL_CHOICES, default='residente')
    telefono = models.CharField(max_length=25, blank=True, null=True)
    departamento_torre = models.CharField(
        max_length=80,
        blank=True,
        null=True,
        help_text="Ejemplo: Torre A - Depto 502 / Oficina 301"
    )

    def es_conserje_o_admin(self):
        return self.rol in ['conserje', 'admin'] or self.is_superuser

    def es_admin(self):
        return self.rol == 'admin' or self.is_superuser

    def __str__(self):
        nombre = self.get_full_name() or self.username
        return f"{nombre} ({self.get_rol_display()})"


class Recinto(models.Model):
    """
    Sectores, dependencias o áreas comunes del Edificio Plaza Centro.
    """
    TIPO_CHOICES = [
        ('area_comun', 'Área Común / Tránsito'),
        ('punto_custodia', 'Punto de Custodia / Bodega / Conserjería'),
    ]

    nombre = models.CharField(max_length=120)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='area_comun')
    descripcion = models.TextField(blank=True)
    encargado = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recintos_a_cargo'
    )
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Recinto o Ubicación"
        verbose_name_plural = "Recintos y Ubicaciones"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class CategoriaObjeto(models.Model):
    """
    Categorías para clasificación rápida de objetos.
    """
    nombre = models.CharField(max_length=80, unique=True)
    icono = models.CharField(
        max_length=40,
        default='fa-box',
        help_text="Clase FontAwesome o emoji de representación (ej: 🔑, 📱, 🧥)"
    )
    descripcion = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name = "Categoría de Objeto"
        verbose_name_plural = "Categorías de Objetos"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Objeto(models.Model):
    """
    Registro centralizado de objetos perdidos y encontrados.
    Garantiza privacidad: La clave_verificacion_privada nunca se muestra públicamente.
    """
    TIPO_CHOICES = [
        ('perdido', 'Objeto Perdido (Reportado por Dueño)'),
        ('encontrado', 'Objeto Encontrado (En Custodia o Reportado por Vecino)'),
    ]

    ESTADO_CHOICES = [
        ('registrado', 'Registrado (En Búsqueda / En Custodia)'),
        ('en_verificacion', 'En Verificación (Proceso de Cotejo)'),
        ('entregado', 'Entregado al Propietario'),
        ('dado_de_baja', 'Dado de Baja / Descartado'),
    ]

    codigo_seguimiento = models.CharField(
        max_length=20,
        unique=True,
        default=generar_codigo_seguimiento
    )
    tipo_registro = models.CharField(max_length=20, choices=TIPO_CHOICES)
    usuario_reporta = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='objetos_reportados',
        help_text="Usuario registrado que reporta (null si es reporte de invitado/visitante)"
    )
    es_invitado = models.BooleanField(
        default=False,
        help_text="Indica si el reporte fue registrado por un visitante o usuario no autenticado"
    )
    contacto_nombre = models.CharField(
        max_length=120,
        blank=True,
        default='',
        help_text="Nombre completo de contacto para reportes de invitados"
    )
    contacto_email = models.EmailField(
        blank=True,
        default='',
        help_text="Correo electrónico de contacto para avisos"
    )
    contacto_telefono = models.CharField(
        max_length=30,
        blank=True,
        default='',
        help_text="Teléfono o WhatsApp de contacto"
    )
    categoria = models.ForeignKey(CategoriaObjeto, on_delete=models.PROTECT)
    subcategoria = models.CharField(
        max_length=100,
        help_text="Ejemplo: Control Remoto Portón, Audífonos Sony, Tarjeta bip"
    )
    color_principal = models.CharField(
        max_length=50,
        help_text="Ejemplo: Negro, Azul marino, Plateado, Rojo"
    )
    marca = models.CharField(max_length=80, blank=True, default='')
    
    # Ubicación física y custodia
    ubicacion = models.ForeignKey(
        Recinto,
        on_delete=models.PROTECT,
        related_name='objetos_registrados',
        help_text="Área o sector del edificio donde ocurrió el hallazgo o extravío"
    )
    ubicacion_bodega = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text="Casillero, locker o estante físico en recepción (solo para objetos encontrados)"
    )

    # Privacidad y seguridad (Ley 19.628)
    descripcion_publica = models.TextField(
        help_text="Detalles generales visibles para la búsqueda sin exponer información crítica"
    )
    clave_verificacion_privada = models.TextField(
        help_text="Detalle exclusivo e invisible públicamente para validar pertenencia (ej: stickers, roturas internas, número serial)"
    )

    fecha_suceso = models.DateField(
        help_text="Fecha aproximada en que se perdió o se encontró el objeto"
    )
    fecha_registro = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=25, choices=ESTADO_CHOICES, default='registrado')

    # Validación y entrega segura
    token_retiro = models.CharField(
        max_length=6,
        default=generar_token_retiro,
        help_text="Código numérico de 6 dígitos para retiro seguro en mesón"
    )
    entregado_a = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='objetos_recibidos'
    )
    entregado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='objetos_entregados_por'
    )
    fecha_entrega = models.DateTimeField(null=True, blank=True)
    observaciones_entrega = models.TextField(blank=True, default='')

    class Meta:
        verbose_name = "Objeto"
        verbose_name_plural = "Objetos"
        ordering = ['-fecha_registro']

    def __str__(self):
        return f"[{self.codigo_seguimiento}] {self.subcategoria} ({self.get_tipo_registro_display()})"

    def get_reportante_display(self):
        if self.es_invitado or not self.usuario_reporta:
            return f"{self.contacto_nombre or 'Visitante'} (Modo Invitado)"
        return self.usuario_reporta.get_full_name() or self.usuario_reporta.username

    def get_contacto_display(self):
        if self.es_invitado or not self.usuario_reporta:
            contactos = []
            if self.contacto_nombre:
                contactos.append(self.contacto_nombre)
            if self.contacto_telefono:
                contactos.append(f"Tel: {self.contacto_telefono}")
            if self.contacto_email:
                contactos.append(f"Email: {self.contacto_email}")
            return " | ".join(contactos) if contactos else "Invitado sin datos"
        user = self.usuario_reporta
        return f"{user.get_full_name() or user.username} ({user.departamento_torre or 'Sin depto'}) - {user.telefono or user.email}"


class Coincidencia(models.Model):
    """
    Resultado del algoritmo de cruce inteligente entre objetos perdidos y encontrados.
    """
    ESTADO_CHOICES = [
        ('sugerida', 'Coincidencia Sugerida por Sistema'),
        ('en_verificacion', 'En Verificación con Conserjería'),
        ('confirmada', 'Confirmada por Propietario'),
        ('descartada', 'Descartada / Falso Positivo'),
        ('resuelta', 'Resuelta / Objeto Entregado'),
    ]

    objeto_perdido = models.ForeignKey(
        Objeto,
        on_delete=models.CASCADE,
        related_name='coincidencias_como_perdido'
    )
    objeto_encontrado = models.ForeignKey(
        Objeto,
        on_delete=models.CASCADE,
        related_name='coincidencias_como_encontrado'
    )
    porcentaje_similitud = models.FloatField(
        help_text="Puntaje de afinidad calculado entre 0% y 100%"
    )
    criterios_match = models.TextField(
        blank=True,
        help_text="Detalle estructurado de factores coincidentes (categoría, color, lugar, fechas)"
    )
    estado = models.CharField(max_length=25, choices=ESTADO_CHOICES, default='sugerida')
    fecha_coincidencia = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Coincidencia de Objetos"
        verbose_name_plural = "Coincidencias de Objetos"
        unique_together = ('objeto_perdido', 'objeto_encontrado')
        ordering = ['-porcentaje_similitud', '-fecha_coincidencia']

    def __str__(self):
        return f"Match ({self.porcentaje_similitud}%): {self.objeto_perdido.subcategoria} <-> {self.objeto_encontrado.subcategoria}"


class MensajeChat(models.Model):
    """
    Canal de comunicación seguro habilitado para coordinar detalles o entrega.
    """
    coincidencia = models.ForeignKey(
        Coincidencia,
        on_delete=models.CASCADE,
        related_name='mensajes'
    )
    emisor = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    mensaje = models.TextField()
    fecha_envio = models.DateTimeField(auto_now_add=True)
    leido = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Mensaje de Coordinación"
        verbose_name_plural = "Mensajes de Coordinación"
        ordering = ['fecha_envio']

    def __str__(self):
        return f"{self.emisor.username}: {self.mensaje[:30]}"


class Notificacion(models.Model):
    """
    Alertas automáticas en la plataforma para los usuarios (RF-07).
    """
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='notificaciones'
    )
    titulo = models.CharField(max_length=150)
    mensaje = models.TextField()
    url_destino = models.CharField(max_length=255, blank=True, default='')
    leida = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Notificación"
        verbose_name_plural = "Notificaciones"
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"Para {self.usuario.username}: {self.titulo}"


class Incidencia(models.Model):
    """
    Reporte de irregularidades, inconsistencias o datos falsos (RF-12).
    """
    TIPO_CHOICES = [
        ('datos_falsos', 'Datos incorrectos o falsos en publicación'),
        ('entrega_irregular', 'Inconveniente o sospecha en entrega física'),
        ('mal_uso', 'Mal uso de la plataforma'),
        ('otro', 'Otro asunto'),
    ]

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='incidencias_reportadas'
    )
    objeto = models.ForeignKey(
        Objeto,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='incidencias'
    )
    tipo = models.CharField(max_length=30, choices=TIPO_CHOICES)
    descripcion = models.TextField()
    resuelta = models.BooleanField(default=False)
    respuesta_admin = models.TextField(blank=True, default='')
    fecha_reporte = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Incidencia"
        verbose_name_plural = "Incidencias"
        ordering = ['-fecha_reporte']

    def __str__(self):
        return f"Incidencia de {self.usuario.username} ({self.get_tipo_display()})"
