import re
from datetime import timedelta
from django.utils import timezone
from .models import Objeto, Coincidencia, Notificacion


def tokenizar(texto):
    """Limpia y divide un texto en palabras significativas en minúsculas."""
    if not texto:
        return set()
    palabras = re.findall(r'\b[a-záéíóúñ0-9]{3,}\b', texto.lower())
    stop_words = {'para', 'como', 'este', 'esta', 'estos', 'estas', 'pero', 'tiene', 'unos', 'unas', 'color', 'marca'}
    return set(p for p in palabras if p not in stop_words)


def calcular_afinidad(perdido, encontrado):
    """
    Calcula el porcentaje de similitud (0.0 a 100.0) y razones de coincidencia entre
    un objeto perdido y un objeto encontrado.
    """
    puntos = 0.0
    criterios = []

    # 1. Categoría (30 puntos si es exacta)
    if perdido.categoria_id == encontrado.categoria_id:
        puntos += 30.0
        criterios.append(f"Misma categoría: {perdido.categoria.nombre}")

    # 2. Subcategoría y palabras clave del objeto (hasta 25 puntos)
    tokens_sub_p = tokenizar(perdido.subcategoria)
    tokens_sub_e = tokenizar(encontrado.subcategoria)
    comunes_sub = tokens_sub_p.intersection(tokens_sub_e)
    if comunes_sub:
        puntos += 25.0
        criterios.append(f"Términos coincidentes: {', '.join(comunes_sub)}")
    else:
        # Si subcategoría coincide parcialmente como substring
        if perdido.subcategoria.lower() in encontrado.subcategoria.lower() or encontrado.subcategoria.lower() in perdido.subcategoria.lower():
            puntos += 15.0
            criterios.append("Subcategoría similar")

    # 3. Color principal (15 puntos)
    color_p = perdido.color_principal.strip().lower()
    color_e = encontrado.color_principal.strip().lower()
    if color_p and color_e:
        if color_p == color_e or color_p in color_e or color_e in color_p:
            puntos += 15.0
            criterios.append(f"Color coincidente: {perdido.color_principal}")
        elif color_p in encontrado.descripcion_publica.lower() or color_e in perdido.descripcion_publica.lower():
            puntos += 8.0
            criterios.append("Mención de color en descripción")

    # 4. Marca (10 puntos)
    if perdido.marca and encontrado.marca:
        if perdido.marca.strip().lower() == encontrado.marca.strip().lower():
            puntos += 10.0
            criterios.append(f"Misma marca: {perdido.marca}")
    elif perdido.marca and perdido.marca.lower() in encontrado.descripcion_publica.lower():
        puntos += 6.0
        criterios.append(f"Marca mencionada: {perdido.marca}")

    # 5. Ubicación física en el edificio (10 puntos)
    if perdido.ubicacion_id == encontrado.ubicacion_id:
        puntos += 10.0
        criterios.append(f"Misma área física: {perdido.ubicacion.nombre}")

    # 6. Proximidad temporal de fechas (hasta 10 puntos)
    dias_diferencia = abs((encontrado.fecha_suceso - perdido.fecha_suceso).days)
    if dias_diferencia <= 2:
        puntos += 10.0
        criterios.append(f"Fechas casi simultáneas (diferencia de {dias_diferencia} día(s))")
    elif dias_diferencia <= 7:
        puntos += 6.0
        criterios.append(f"Rango de fecha cercano ({dias_diferencia} días)")
    elif dias_diferencia <= 15:
        puntos += 3.0

    # Normalizar puntaje máximo a 100%
    porcentaje = round(min(puntos, 100.0), 1)
    texto_criterios = " | ".join(criterios) if criterios else "Similitud general"
    return porcentaje, texto_criterios


def ejecutar_motor_coincidencias(objeto):
    """
    Ejecuta el cruce algorítmico cuando se registra o actualiza un objeto.
    Compara contra objetos activos del tipo opuesto.
    """
    if objeto.estado in ['entregado', 'dado_de_baja']:
        return []

    coincidencias_generadas = []

    if objeto.tipo_registro == 'perdido':
        candidatos = Objeto.objects.filter(
            tipo_registro='encontrado',
            estado__in=['registrado', 'en_verificacion']
        )
        for cand in candidatos:
            score, criterios = calcular_afinidad(objeto, cand)
            if score >= 45.0:
                coincidencia, creada = Coincidencia.objects.update_or_create(
                    objeto_perdido=objeto,
                    objeto_encontrado=cand,
                    defaults={
                        'porcentaje_similitud': score,
                        'criterios_match': criterios,
                    }
                )
                coincidencias_generadas.append(coincidencia)

                # Generar notificación si la coincidencia es relevante y fue creada o alta
                if creada and score >= 60.0 and objeto.usuario_reporta:
                    Notificacion.objects.create(
                        usuario=objeto.usuario_reporta,
                        titulo="¡Posible coincidencia encontrada!",
                        mensaje=(
                            f"Se detectó un objeto encontrado ({cand.subcategoria}) en '{cand.ubicacion.nombre}' "
                            f"con {score}% de afinidad con tu reporte '{objeto.subcategoria}'."
                        ),
                        url_destino=f"/coincidencias/{coincidencia.id}/"
                    )

    elif objeto.tipo_registro == 'encontrado':
        candidatos = Objeto.objects.filter(
            tipo_registro='perdido',
            estado__in=['registrado', 'en_verificacion']
        )
        for cand in candidatos:
            score, criterios = calcular_afinidad(cand, objeto)
            if score >= 45.0:
                coincidencia, creada = Coincidencia.objects.update_or_create(
                    objeto_perdido=cand,
                    objeto_encontrado=objeto,
                    defaults={
                        'porcentaje_similitud': score,
                        'criterios_match': criterios,
                    }
                )
                coincidencias_generadas.append(coincidencia)

                if creada and score >= 60.0 and cand.usuario_reporta:
                    Notificacion.objects.create(
                        usuario=cand.usuario_reporta,
                        titulo="¡Nuevo hallazgo que coincide con tu reporte!",
                        mensaje=(
                            f"Acaban de registrar un hallazgo de '{objeto.subcategoria}' en '{objeto.ubicacion.nombre}' "
                            f"con {score}% de afinidad con lo que perdiste."
                        ),
                        url_destino=f"/coincidencias/{coincidencia.id}/"
                    )

    return coincidencias_generadas
