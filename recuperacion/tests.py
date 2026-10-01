from datetime import date, timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from recuperacion.models import (
    Recinto, CategoriaObjeto, Objeto, Coincidencia, Notificacion, MensajeChat
)
from recuperacion.matching import calcular_afinidad, ejecutar_motor_coincidencias

Usuario = get_user_model()


class VuelveATiTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Usuarios de prueba
        self.residente1 = Usuario.objects.create_user(
            username='thalya',
            email='thalya@test.cl',
            password='password123',
            rol='residente',
            departamento_torre='Torre A - 502'
        )
        self.residente2 = Usuario.objects.create_user(
            username='juan',
            email='juan@test.cl',
            password='password123',
            rol='residente',
            departamento_torre='Torre B - 304'
        )
        self.conserje = Usuario.objects.create_user(
            username='carlos_conserje',
            email='carlos@test.cl',
            password='password123',
            rol='conserje',
            is_staff=True
        )
        self.admin = Usuario.objects.create_user(
            username='admin_edificio',
            email='admin@test.cl',
            password='password123',
            rol='admin',
            is_staff=True,
            is_superuser=True
        )

        # Ubicación y Categoría
        self.recinto = Recinto.objects.create(
            nombre='Estacionamiento Subterráneo -1',
            tipo='area_comun',
            encargado=self.conserje
        )
        self.categoria = CategoriaObjeto.objects.create(
            nombre='Llaves y Accesos',
            icono='fa-key'
        )

    def test_roles_usuario(self):
        """Verifica roles y métodos de permisos de usuario."""
        self.assertFalse(self.residente1.es_conserje_o_admin())
        self.assertFalse(self.residente1.es_admin())
        self.assertTrue(self.conserje.es_conserje_o_admin())
        self.assertFalse(self.conserje.es_admin())
        self.assertTrue(self.admin.es_conserje_o_admin())
        self.assertTrue(self.admin.es_admin())

    def test_generacion_codigos_automaticos(self):
        """Verifica código de seguimiento (VT-...) y token de 6 dígitos."""
        obj = Objeto.objects.create(
            tipo_registro='perdido',
            usuario_reporta=self.residente1,
            categoria=self.categoria,
            subcategoria='Control Portón',
            color_principal='Negro',
            ubicacion=self.recinto,
            descripcion_publica='Control de dos botones',
            clave_verificacion_privada='Cinta roja en la tapa de pilas',
            fecha_suceso=date.today(),
        )
        self.assertTrue(obj.codigo_seguimiento.startswith("VT-"))
        self.assertEqual(len(obj.token_retiro), 6)
        self.assertEqual(obj.estado, 'registrado')

    def test_motor_coincidencias_afinidad(self):
        """Verifica cálculo de afinidad algorítmica y notificación."""
        hoy = date.today()
        perdido = Objeto.objects.create(
            tipo_registro='perdido',
            usuario_reporta=self.residente1,
            categoria=self.categoria,
            subcategoria='Control Remoto Portón BFT',
            color_principal='Negro',
            marca='BFT',
            ubicacion=self.recinto,
            descripcion_publica='Control negro de portón con argolla',
            clave_verificacion_privada='Cinta roja trasera',
            fecha_suceso=hoy,
        )
        encontrado = Objeto.objects.create(
            tipo_registro='encontrado',
            usuario_reporta=self.conserje,
            categoria=self.categoria,
            subcategoria='Control Remoto Portón',
            color_principal='Negro',
            marca='BFT',
            ubicacion=self.recinto,
            ubicacion_bodega='Casillero 2',
            descripcion_publica='Control de portón hallado en rampa',
            clave_verificacion_privada='Detalle cinta roja',
            fecha_suceso=hoy,
        )

        score, razones = calcular_afinidad(perdido, encontrado)
        self.assertGreaterEqual(score, 75.0)

        matches = ejecutar_motor_coincidencias(perdido)
        self.assertEqual(len(matches), 1)
        self.assertEqual(Coincidencia.objects.count(), 1)
        self.assertEqual(Notificacion.objects.filter(usuario=self.residente1).count(), 1)

    def test_privacidad_ficha_objeto(self):
        """
        Garantiza Ley N° 19.628:
        Un residente ajeno NO puede ver la clave secreta ni el token de retiro del dueño.
        """
        obj = Objeto.objects.create(
            tipo_registro='perdido',
            usuario_reporta=self.residente1,
            categoria=self.categoria,
            subcategoria='Llavero Familiar',
            color_principal='Plateado',
            ubicacion=self.recinto,
            descripcion_publica='Llavero con 3 llaves',
            clave_verificacion_privada='LLAVE_SECRETA_CONFIDENCIAL',
            fecha_suceso=date.today(),
        )

        # 1. Residente ajeno (Juan)
        self.client.login(username='juan', password='password123')
        resp_juan = self.client.get(reverse('detalle_objeto', kwargs={'pk': obj.pk}))
        self.assertEqual(resp_juan.status_code, 200)
        self.assertNotContains(resp_juan, 'LLAVE_SECRETA_CONFIDENCIAL')
        self.assertNotContains(resp_juan, obj.token_retiro)
        self.assertContains(resp_juan, 'Privacidad Resguardada (Ley N° 19.628)')

        # 2. Propietaria (Thalya)
        self.client.login(username='thalya', password='password123')
        resp_thalya = self.client.get(reverse('detalle_objeto', kwargs={'pk': obj.pk}))
        self.assertEqual(resp_thalya.status_code, 200)
        self.assertContains(resp_thalya, 'LLAVE_SECRETA_CONFIDENCIAL')
        self.assertContains(resp_thalya, obj.token_retiro)

        # 3. Conserje (Carlos)
        self.client.login(username='carlos_conserje', password='password123')
        resp_conserje = self.client.get(reverse('detalle_objeto', kwargs={'pk': obj.pk}))
        self.assertEqual(resp_conserje.status_code, 200)
        self.assertContains(resp_conserje, 'LLAVE_SECRETA_CONFIDENCIAL')

    def test_conserjeria_acceso_restringido(self):
        """Un residente común no debe poder entrar al panel de conserjería."""
        self.client.login(username='juan', password='password123')
        resp = self.client.get(reverse('conserjeria_panel'))
        self.assertRedirects(resp, reverse('dashboard'))

        # Conserje sí tiene acceso
        self.client.login(username='carlos_conserje', password='password123')
        resp_ok = self.client.get(reverse('conserjeria_panel'))
        self.assertEqual(resp_ok.status_code, 200)

    def test_flujo_validacion_y_entrega_con_token(self):
        """
        Valida que ingresar el token correcto cambie el estado a ENTREGADO
        y registre funcionario responsable y fecha.
        """
        perdido = Objeto.objects.create(
            tipo_registro='perdido',
            usuario_reporta=self.residente1,
            categoria=self.categoria,
            subcategoria='Control Portón',
            color_principal='Negro',
            ubicacion=self.recinto,
            descripcion_publica='Control negro',
            clave_verificacion_privada='Cinta roja',
            fecha_suceso=date.today(),
        )
        encontrado = Objeto.objects.create(
            tipo_registro='encontrado',
            usuario_reporta=self.conserje,
            categoria=self.categoria,
            subcategoria='Control Portón',
            color_principal='Negro',
            ubicacion=self.recinto,
            ubicacion_bodega='Locker 1',
            descripcion_publica='Control hallado',
            clave_verificacion_privada='Cinta roja',
            fecha_suceso=date.today(),
        )
        coincidencia = Coincidencia.objects.create(
            objeto_perdido=perdido,
            objeto_encontrado=encontrado,
            porcentaje_similitud=90.0,
            criterios_match='Misma categoría y color'
        )

        self.client.login(username='carlos_conserje', password='password123')
        url_validar = reverse('validar_entrega', kwargs={'pk': encontrado.pk})

        # Token erróneo
        resp_err = self.client.post(url_validar, {'token_retiro': '999999', 'observaciones': ''})
        encontrado.refresh_from_db()
        self.assertEqual(encontrado.estado, 'registrado')

        # Token correcto del dueño
        resp_ok = self.client.post(url_validar, {
            'token_retiro': perdido.token_retiro,
            'observaciones': 'Entregado en recepción con verificación de carnet'
        })
        self.assertRedirects(resp_ok, reverse('conserjeria_panel'))

        encontrado.refresh_from_db()
        perdido.refresh_from_db()
        self.assertEqual(encontrado.estado, 'entregado')
        self.assertEqual(perdido.estado, 'entregado')
        self.assertEqual(encontrado.entregado_a, self.residente1)
        self.assertEqual(encontrado.entregado_por, self.conserje)
        self.assertIsNotNone(encontrado.fecha_entrega)
