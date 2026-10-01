from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from .models import Objeto, Recinto, CategoriaObjeto, Incidencia

Usuario = get_user_model()


class RegistroUsuarioForm(forms.ModelForm):
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '••••••••', 'autocomplete': 'new-password'}),
        min_length=6
    )
    password_confirm = forms.CharField(
        label="Confirmar Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '••••••••', 'autocomplete': 'new-password'})
    )

    class Meta:
        model = Usuario
        fields = ['username', 'email', 'first_name', 'last_name', 'telefono', 'departamento_torre', 'rol', 'password']
        labels = {
            'username': 'Nombre de Usuario',
            'email': 'Correo Electrónico',
            'first_name': 'Nombres',
            'last_name': 'Apellidos',
            'telefono': 'Teléfono de Contacto',
            'departamento_torre': 'Torre y Departamento / Oficina',
            'rol': 'Tipo de Usuario',
        }
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ej: juan.perez'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'ejemplo@correo.com'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Juan'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Pérez'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+56 9 1234 5678'}),
            'departamento_torre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Torre A - Depto 502'}),
            'rol': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        pwd = cleaned_data.get('password')
        pwd_c = cleaned_data.get('password_confirm')
        if pwd and pwd_c and pwd != pwd_c:
            self.add_error('password_confirm', "Las contraseñas no coinciden.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class LoginFormPersonalizado(AuthenticationForm):
    username = forms.CharField(
        label="Usuario o Correo",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingresa tu usuario'})
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '••••••••'})
    )


class ObjetoPerdidoForm(forms.ModelForm):
    """
    Formulario estructurado en 2 pasos para reporte de objetos perdidos.
    Soporta Modo Registrado y Modo Invitado (Híbrido).
    """
    class Meta:
        model = Objeto
        fields = [
            'categoria',
            'subcategoria',
            'color_principal',
            'marca',
            'ubicacion',
            'fecha_suceso',
            'contacto_nombre',
            'contacto_email',
            'contacto_telefono',
            'descripcion_publica',
            'clave_verificacion_privada'
        ]
        labels = {
            'categoria': 'Categoría General',
            'subcategoria': '¿Qué objeto perdiste? (Nombre específico)',
            'color_principal': 'Color Principal',
            'marca': 'Marca o Fabricante (Opcional)',
            'ubicacion': 'Área común o sector donde lo extraviaste',
            'fecha_suceso': 'Fecha aproximada de extravío',
            'contacto_nombre': 'Tu Nombre Completo',
            'contacto_email': 'Correo Electrónico de Contacto',
            'contacto_telefono': 'Teléfono o WhatsApp',
            'descripcion_publica': 'Descripción Pública (Visible)',
            'clave_verificacion_privada': 'Clave de Verificación Privada (Confidencial)',
        }
        help_texts = {
            'descripcion_publica': 'Resumen visible para búsquedas sin revelar datos privados (ej: "Control remoto negro con dos botones redondos").',
            'clave_verificacion_privada': 'Detalle exclusivo que solo tú conoces para validar tu propiedad al retirarlo (ej: "Tiene cinta adhesiva roja en la tapa de pilas").',
            'fecha_suceso': 'Selecciona la fecha estimada.',
            'contacto_nombre': 'Indica cómo te llamas para identificarte en conserjería.',
            'contacto_email': 'Te avisaremos si el sistema detecta coincidencias.',
            'contacto_telefono': 'Número de contacto para que conserjería se comunique contigo.',
        }
        widgets = {
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'subcategoria': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ej: Control Portón, Tarjeta Bip, Billetera'}),
            'color_principal': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ej: Negro, Azul, Café'}),
            'marca': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ej: BFT, Sony, Samsung, Cuero'}),
            'ubicacion': forms.Select(attrs={'class': 'form-select'}),
            'fecha_suceso': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'contacto_nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ej: Camila Muñoz'}),
            'contacto_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'ej: camila@correo.cl'}),
            'contacto_telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ej: +56 9 8765 4321'}),
            'descripcion_publica': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe el objeto de forma general...'}),
            'clave_verificacion_privada': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Escribe una seña particular, detalle interno o marca secreta...'}),
        }

    def __init__(self, *args, es_invitado=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.es_invitado = es_invitado
        if self.es_invitado:
            self.fields['contacto_nombre'].required = True
        else:
            self.fields['contacto_nombre'].required = False
            self.fields['contacto_email'].required = False
            self.fields['contacto_telefono'].required = False

    def clean(self):
        cleaned_data = super().clean()
        if self.es_invitado:
            nombre = cleaned_data.get('contacto_nombre')
            email = cleaned_data.get('contacto_email')
            telefono = cleaned_data.get('contacto_telefono')

            if not nombre:
                self.add_error('contacto_nombre', "Debes indicar tu nombre completo en Modo Invitado.")
            if not email and not telefono:
                self.add_error('contacto_email', "Ingresa al menos un correo o teléfono para poder contactarte ante cualquier novedad.")
        return cleaned_data


class ObjetoEncontradoForm(forms.ModelForm):
    """
    Formulario para registrar objetos hallados.
    Permite registrar a usuarios autenticados, conserjes o visitantes invitados.
    """
    class Meta:
        model = Objeto
        fields = [
            'categoria',
            'subcategoria',
            'color_principal',
            'marca',
            'ubicacion',
            'ubicacion_bodega',
            'fecha_suceso',
            'contacto_nombre',
            'contacto_email',
            'contacto_telefono',
            'descripcion_publica',
            'clave_verificacion_privada'
        ]
        labels = {
            'categoria': 'Categoría General',
            'subcategoria': '¿Qué objeto encontraste?',
            'color_principal': 'Color Principal',
            'marca': 'Marca o Fabricante (Opcional)',
            'ubicacion': 'Área común donde fue hallado',
            'ubicacion_bodega': 'Ubicación física en custodia (Locker / Casillero)',
            'fecha_suceso': 'Fecha del hallazgo',
            'contacto_nombre': 'Tu Nombre Completo',
            'contacto_email': 'Correo Electrónico (Opcional)',
            'contacto_telefono': 'Teléfono o WhatsApp (Opcional)',
            'descripcion_publica': 'Descripción Pública del objeto',
            'clave_verificacion_privada': 'Detalle o seña particular para corroborar al dueño',
        }
        widgets = {
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'subcategoria': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ej: Mochila, Llavero, Celular'}),
            'color_principal': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ej: Gris, Negro, Rojo'}),
            'marca': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ej: Xiaomi, Jansport'}),
            'ubicacion': forms.Select(attrs={'class': 'form-select'}),
            'ubicacion_bodega': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ej: Casillero 3 - Bodega Conserjería'}),
            'fecha_suceso': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'contacto_nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ej: Andrés Soto'}),
            'contacto_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'ej: andres@correo.cl'}),
            'contacto_telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ej: +56 9 1234 5678'}),
            'descripcion_publica': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Detalles generales visibles para la comunidad...'}),
            'clave_verificacion_privada': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Detalle secreto que deberá confirmar quien lo reclame...'}),
        }

    def __init__(self, *args, es_invitado=False, es_conserje=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.es_invitado = es_invitado
        self.es_conserje = es_conserje

        if self.es_invitado:
            self.fields['contacto_nombre'].required = True
            # Los invitados no seleccionan casillero de bodega
            if 'ubicacion_bodega' in self.fields:
                self.fields['ubicacion_bodega'].required = False
                self.fields['ubicacion_bodega'].widget = forms.HiddenInput()
        else:
            self.fields['contacto_nombre'].required = False
            self.fields['contacto_email'].required = False
            self.fields['contacto_telefono'].required = False

    def clean(self):
        cleaned_data = super().clean()
        if self.es_invitado:
            nombre = cleaned_data.get('contacto_nombre')
            email = cleaned_data.get('contacto_email')
            telefono = cleaned_data.get('contacto_telefono')

            if not nombre:
                self.add_error('contacto_nombre', "Debes indicar tu nombre para dejar constancia de quién entregó el hallazgo.")
            if not email and not telefono:
                self.add_error('contacto_email', "Ingresa al menos un medio de contacto (correo o teléfono).")
        return cleaned_data


class ValidacionEntregaForm(forms.Form):
    token_retiro = forms.CharField(
        max_length=6,
        label="Token de Retiro (6 dígitos)",
        widget=forms.TextInput(attrs={'class': 'form-control text-center tracking-widest text-lg font-bold', 'placeholder': '123456', 'maxlength': 6})
    )
    observaciones = forms.CharField(
        required=False,
        label="Observaciones de Entrega",
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Notas sobre la entrega física o verificación de cédula...'})
    )


class IncidenciaForm(forms.ModelForm):
    class Meta:
        model = Incidencia
        fields = ['tipo', 'descripcion']
        labels = {
            'tipo': 'Motivo del Reporte',
            'descripcion': 'Explica lo sucedido en detalle',
        }
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe la irregularidad o dato incorrecto...'}),
        }


class RecintoForm(forms.ModelForm):
    class Meta:
        model = Recinto
        fields = ['nombre', 'tipo', 'descripcion', 'encargado', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del sector o caseta'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'encargado': forms.Select(attrs={'class': 'form-select'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
