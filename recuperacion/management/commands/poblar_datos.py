from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from recuperacion.models import (
    Usuario, Recinto, CategoriaObjeto, Objeto, Coincidencia, MensajeChat, Notificacion
)
from recuperacion.matching import ejecutar_motor_coincidencias


class Command(BaseCommand):
    help = "Puebla la base de datos con datos realistas para el Edificio Plaza Centro ('Vuelve a ti')"

    def handle(self, *args, **options):
        self.stdout.write("Creando usuarios del sistema...")
        # 1. Usuarios
        admin, _ = Usuario.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@vuelveati.cl',
                'first_name': 'Administrador',
                'last_name': 'Plaza Centro',
                'rol': 'admin',
                'is_staff': True,
                'is_superuser': True,
                'telefono': '+56 9 8888 1111',
                'departamento_torre': 'Administración General - Piso 2'
            }
        )
        admin.set_password('admin123')
        admin.save()

        conserje, _ = Usuario.objects.get_or_create(
            username='conserje1',
            defaults={
                'email': 'conserjeria@plazacentro.cl',
                'first_name': 'Carlos',
                'last_name': 'Soto (Conserje Turno Día)',
                'rol': 'conserje',
                'is_staff': True,
                'telefono': '+56 9 7777 2222',
                'departamento_torre': 'Recepción y Seguridad Central'
            }
        )
        conserje.set_password('conserje123')
        conserje.save()

        residente1, _ = Usuario.objects.get_or_create(
            username='thalya',
            defaults={
                'email': 'thalya.araneda@usm.cl',
                'first_name': 'Thalya',
                'last_name': 'Araneda',
                'rol': 'residente',
                'telefono': '+56 9 6666 3333',
                'departamento_torre': 'Torre A - Depto 502'
            }
        )
        residente1.set_password('thalya123')
        residente1.save()

        residente2, _ = Usuario.objects.get_or_create(
            username='juan',
            defaults={
                'email': 'juan.perez@correo.cl',
                'first_name': 'Juan',
                'last_name': 'Pérez',
                'rol': 'residente',
                'telefono': '+56 9 5555 4444',
                'departamento_torre': 'Torre B - Depto 304'
            }
        )
        residente2.set_password('juan123')
        residente2.save()

        self.stdout.write("Creando recintos y áreas comunes...")
        # 2. Recintos
        recintos_data = [
            ("Conserjería y Bodega Principal", "punto_custodia", "Mesón de recepción y casillero de objetos en custodia"),
            ("Estacionamiento Subterráneo -1", "area_comun", "Aparcamiento vehicular y portón principal"),
            ("Estacionamiento Subterráneo -2", "area_comun", "Zona de bodegas subterráneas"),
            ("Lobby y Ascensores Torre A", "area_comun", "Acceso a torres residenciales A"),
            ("Lobby y Ascensores Torre B", "area_comun", "Acceso a oficinas y torre B"),
            ("Gimnasio y Terraza Comunitaria", "area_comun", "Piso 4 - Espacio recreativo compartido"),
            ("Pasillos Comerciales Piso 1", "area_comun", "Locales de atención al público y cafetería"),
        ]

        recintos_dict = {}
        for nombre, tipo, desc in recintos_data:
            rec, _ = Recinto.objects.get_or_create(
                nombre=nombre,
                defaults={'tipo': tipo, 'descripcion': desc, 'encargado': conserje}
            )
            recintos_dict[nombre] = rec

        self.stdout.write("Creando categorías...")
        # 3. Categorías
        categorias_data = [
            ("Llaves y Accesos", "🔑", "Llaveros, controles remotos de portón, tarjetas magneticas y chips."),
            ("Telefonía y Electrónica", "📱", "Smartphones, cargadores, audífonos bluetooth, tablets."),
            ("Documentos y Billeteras", "🪪", "Cédulas, pases escolares, billeteras, tarjetas bancarias."),
            ("Ropa y Abrigos", "🧥", "Chaquetas, bufandas, polerones, sombreros y gorros."),
            ("Bolsos y Mochilas", "🎒", "Mochilas universitarias, carteras, bananos y maletines."),
            ("Accesorios Personales", "🕶️", "Lentes ópticos y de sol, relojes, joyas, paraguas."),
            ("Otros Artículos", "📦", "Botellas térmicas, termos, termos, cuadernos, estuches."),
        ]

        cat_dict = {}
        for nombre, icono, desc in categorias_data:
            cat, _ = CategoriaObjeto.objects.get_or_create(
                nombre=nombre,
                defaults={'icono': icono, 'descripcion': desc}
            )
            cat_dict[nombre] = cat

        self.stdout.write("Creando objetos de muestra (perdidos y encontrados)...")
        hoy = date.today()

        # Objeto 1: Control remoto portón reportado como PERDIDO por Thalya
        obj_perdido_1, _ = Objeto.objects.get_or_create(
            codigo_seguimiento='VT-2026-CTRL1',
            defaults={
                'tipo_registro': 'perdido',
                'usuario_reporta': residente1,
                'categoria': cat_dict["Llaves y Accesos"],
                'subcategoria': 'Control Remoto Portón Automático',
                'color_principal': 'Negro',
                'marca': 'BFT',
                'ubicacion': recintos_dict["Estacionamiento Subterráneo -1"],
                'descripcion_publica': 'Control de portón negro de dos botones redondos con argolla plateada desgastada.',
                'clave_verificacion_privada': 'Tiene un trozo de cinta adhesiva roja cubriendo la tapa trasera de las pilas.',
                'fecha_suceso': hoy - timedelta(days=2),
                'estado': 'registrado',
            }
        )

        # Objeto 2: Control remoto portón ENCONTRADO por Conserje en Estacionamiento -1
        obj_encontrado_1, _ = Objeto.objects.get_or_create(
            codigo_seguimiento='VT-2026-HALL1',
            defaults={
                'tipo_registro': 'encontrado',
                'usuario_reporta': conserje,
                'categoria': cat_dict["Llaves y Accesos"],
                'subcategoria': 'Control Remoto Portón',
                'color_principal': 'Negro',
                'marca': 'BFT',
                'ubicacion': recintos_dict["Estacionamiento Subterráneo -1"],
                'ubicacion_bodega': 'Estante A - Casillero 3',
                'descripcion_publica': 'Control de portón negro hallado en el sector de rampas del subterráneo -1.',
                'clave_verificacion_privada': 'Lleva cinta aisladora roja en la parte posterior.',
                'fecha_suceso': hoy - timedelta(days=1),
                'estado': 'registrado',
            }
        )

        # Objeto 3: Audífonos Bluetooth perdidos por Juan
        obj_perdido_2, _ = Objeto.objects.get_or_create(
            codigo_seguimiento='VT-2026-AUDI2',
            defaults={
                'tipo_registro': 'perdido',
                'usuario_reporta': residente2,
                'categoria': cat_dict["Telefonía y Electrónica"],
                'subcategoria': 'Audífonos Inalámbricos Bluetooth',
                'color_principal': 'Blanco',
                'marca': 'Sony',
                'ubicacion': recintos_dict["Gimnasio y Terraza Comunitaria"],
                'descripcion_publica': 'Caja de carga blanca de audífonos compactos, perdida en sector máquinas.',
                'clave_verificacion_privada': 'El estuche tiene una pequeña marca hecha con plumón negro en la base.',
                'fecha_suceso': hoy - timedelta(days=3),
                'estado': 'registrado',
            }
        )

        # Objeto 4: Audífonos encontrados en Gimnasio entregados a conserjería
        obj_encontrado_2, _ = Objeto.objects.get_or_create(
            codigo_seguimiento='VT-2026-HALL2',
            defaults={
                'tipo_registro': 'encontrado',
                'usuario_reporta': conserje,
                'categoria': cat_dict["Telefonía y Electrónica"],
                'subcategoria': 'Audífonos Inalámbricos',
                'color_principal': 'Blanco',
                'marca': 'Sony',
                'ubicacion': recintos_dict["Gimnasio y Terraza Comunitaria"],
                'ubicacion_bodega': 'Locker Seguridad 1 - Nivel Medio',
                'descripcion_publica': 'Estuche cargador blanco hallado en banca de vestidor.',
                'clave_verificacion_privada': 'Mancha o inicial diminuta en la base inferior.',
                'fecha_suceso': hoy - timedelta(days=3),
                'estado': 'registrado',
            }
        )

        # Ejecutar algoritmo de coincidencias automáticas
        self.stdout.write("Calculando coincidencias automáticas...")
        ejecutar_motor_coincidencias(obj_perdido_1)
        ejecutar_motor_coincidencias(obj_encontrado_1)
        ejecutar_motor_coincidencias(obj_perdido_2)
        ejecutar_motor_coincidencias(obj_encontrado_2)

        self.stdout.write(self.style.SUCCESS("¡Base de datos poblada exitosamente!"))
        self.stdout.write("Usuarios creados:")
        self.stdout.write(" - Admin: admin / admin123")
        self.stdout.write(" - Conserje: conserje1 / conserje123")
        self.stdout.write(" - Residente 1: thalya / thalya123")
        self.stdout.write(" - Residente 2: juan / juan123")
