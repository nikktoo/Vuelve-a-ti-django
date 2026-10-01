# 🏢 Vuelve a Ti — Sistema de Recuperación de Objetos
**Plataforma Fullstack en Django para Gestión de Objetos Perdidos y Encontrados**  
*Desarrollado para el Edificio Plaza Centro (Concepción) — Universidad Técnica Federico Santa María (UTFSM)*  
**Autora:** Thalya Araneda &bull; **Carrera:** Técnico Universitario en Informática &bull; **Paralelo:** 701

---

## 📌 1. Visión General
**"Vuelve a ti"** es un sistema web integral diseñado para sustituir al 100% las anotaciones en cuadernos y hojas sueltas en las conserjerías de edificios corporativos y residenciales. Centraliza el ciclo de vida de los objetos extraviados, efectúa cruces algorítmicos automatizados y garantiza la máxima confidencialidad de los datos personales de acuerdo con la **Ley N° 19.628 de Protección de la Vida Privada** en Chile.

---

## 🚀 2. Características y Requerimientos Implementados

| Requerimiento | Descripción | Implementación en el Proyecto |
| :--- | :--- | :--- |
| **RF-01** Autenticación y Roles | Registro e inicio de sesión seguro con roles diferenciados: Residente/Ciudadano, Conserje y Administrador. | Modelo `Usuario` personalizado con contraseñas encriptadas y vistas `login` / `registro`. |
| **RF-02** Registro de Objeto Perdido | Asistente en 2 pasos: Clasificación/Lugar + Descripción Pública y **Clave de Verificación Privada**. Soporta **Modo Invitado (Híbrido)** sin requerir registro. | Vista `reportar_perdido` con validaciones dinámicas y generación de token de retiro. |
| **RF-03** Registro de Objeto Encontrado | Ingreso de hallazgos para residentes, conserjes y visitantes (Modo Invitado). En conserjería asigna casillero/locker en recepción. | Vista `reportar_hallazgo` y soporte de inventario en bodega. |
| **RF-04** Búsqueda y Filtrado | Catálogo público con filtros por sector, categoría, fecha y palabras clave, sin exponer datos personales. | Vista `buscar_objetos` con diseño de tarjetas basado en los mockups. |
| **RF-05** Coincidencias Automáticas | Algoritmo inteligente que evalúa categoría, términos clave, color, marca, sector y cercanía de fechas. | Módulo `recuperacion.matching` con umbral ponderado y scoring porcentual. |
| **RF-06** Verificación de Propiedad | Cotejo visual de la seña secreta contra el objeto físico y validación del token de 6 dígitos. | Módulo `validar_entrega` para el personal de mesón. |
| **RF-07** Notificaciones Integradas | Alertas en tiempo real en la plataforma cuando se detectan coincidencias superiores al 60%. | Modelo `Notificacion` integrado en el header y contador global. |
| **RF-08** Gestión de Recintos | Administración de sectores, pisos, casetas y asignación de encargados de conserjería. | Vista `gestion_recintos` para administradores. |
| **RF-09** Ciclo de Vida y Estados | Estados: `Registrado` $\rightarrow$ `En verificación` $\rightarrow$ `Entregado` $\rightarrow$ `Dado de baja`. | Máquina de estados controlada en `Objeto` y trazabilidad de entrega. |
| **RF-10** Reportes Estadísticos | Analítica gerencial: tasa de recuperación, top categorías y zonas con mayor incidencia. | Módulo `metricas` con gráficos e indicadores de gestión. |
| **RF-11** Historial Avanzado | Auditoría general de movimientos con filtros por fecha, tipo, lugar y estado. | Vista `historial_avanzado`. |
| **RF-12** Reporte de Incidencias | Reporte de irregularidades, anomalías o información falsa para revisión administrativa. | Modelo y formulario `Incidencia`. |
| **Canal Seguro** | Chat privado encriptado en plataforma entre propietario, conserje y hallador sin exponer teléfonos. | Modelo `MensajeChat` con vista `detalle_coincidencia`. |
| **Modo Invitado & Seguimiento** | Registro express para visitantes sin cuenta con ficha de confirmación y consulta de estado por código/token. | Vistas `reporte_exitoso_invitado` y `consultar_seguimiento`. |

---

## 🎨 3. Diseño y Estética Visual
El diseño frontend utiliza la paleta en tonos cálidos tierra y beige (`#F7F3ED`, `#D9C4B2`, `#8F623F`, `#3B281C`) especificada en los mockups oficiales, implementando:
1. **Vista Residente / Móvil:** Formularios ágiles guiados, tarjetas tipo app móvil y token de retiro de 6 dígitos visible solo para el dueño.
2. **Panel de Conserjería / Recepción:** Barra de búsqueda en tiempo real por casillero/código, tabla de inventario en bodega y botón exprés de entrega.

---

## 🔑 4. Cuentas de Prueba Preconfiguradas

Para facilitar la evaluación y demostración inmediata, se incluyen las siguientes credenciales:

| Rol | Usuario | Contraseña | Perfil / Descripción |
| :--- | :--- | :--- | :--- |
| **Administrador** | `admin` | `admin123` | Control maestro, métricas globales, recintos y Django Admin. |
| **Conserje** | `conserje1` | `conserje123` | Carlos Soto - Encargado de recepción, bodega, lockers y entregas. |
| **Residente 1** | `thalya` | `thalya123` | Thalya Araneda - Torre A Depto 502 (reportó control remoto perdido). |
| **Residente 2** | `juan` | `juan123` | Juan Pérez - Torre B Depto 304 (reportó audífonos perdidos). |

---

## 🛠️ 5. Ejecución del Proyecto

### 5.1. Configuración del Entorno Virtual e Instalación de Dependencias

1. **Crear el entorno virtual:**
   ```powershell
   py -m venv .venv
   ```

2. **Activar el entorno virtual:**
   - En **PowerShell**:
     ```powershell
     .\.venv\Scripts\Activate.ps1
     ```
     *(Si PowerShell restringe la ejecución de scripts, puedes habilitarlo en tu sesión actual con `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`).*
   - En **CMD (Símbolo del sistema)**:
     ```cmd
     .venv\Scripts\activate.bat
     ```
   - En **Git Bash / WSL / Linux / macOS**:
     ```bash
     source .venv/Scripts/activate # o source .venv/bin/activate en Linux/macOS
     ```

3. **Instalar dependencias:**
   ```powershell
   pip install -r requirements.txt
   ```

### 5.2. Iniciar el Servidor de Desarrollo
```powershell
python manage.py runserver
```
Accede en tu navegador a: **http://127.0.0.1:8000/**

### 5.3. Ejecutar la Suite de Pruebas Automatizadas
```powershell
python manage.py test recuperacion
```
Verifica modelos, matching algorítmico, reglas de privacidad (Ley 19.628) y validación de entrega con token.

### 5.4. Repoblar Datos de Prueba (Opcional)
```powershell
python manage.py poblar_datos
```

---

## 📁 6. Estructura del Código
```
Vuelve a ti/
├── manage.py                          # Gestor de comandos Django
├── requirements.txt                   # Dependencias del proyecto (Django)
├── db.sqlite3                         # Base de datos preconfigurada con datos de Plaza Centro
├── vuelve_a_ti_project/               # Configuración del proyecto Django
│   ├── settings.py                    # Ajustes (Auth custom, i18n español, templates, static)
│   ├── urls.py                        # Ruteo principal
│   └── wsgi.py
├── recuperacion/                      # Aplicación central de recuperación de objetos
│   ├── models.py                      # Modelos: Usuario, Recinto, Categoria, Objeto, Coincidencia, etc.
│   ├── views.py                       # Lógica de vistas y controladores (12 requerimientos funcionales)
│   ├── forms.py                       # Formularios en 2 pasos y validaciones
│   ├── matching.py                    # Motor de emparejamiento inteligente ponderado
│   ├── admin.py                       # Panel administrativo Django personalizado
│   ├── urls.py                        # URLs de la aplicación
│   ├── tests.py                       # Suite de pruebas unitarias y de integración
│   └── management/commands/
│       └── poblar_datos.py            # Comando de seed de datos realistas
├── templates/                         # Plantillas HTML5 con Django Templates
│   ├── base.html                      # Layout base con navbar y notificaciones
│   └── recuperacion/                  # Vistas específicas (dashboard, conserjería, métricas, etc.)
└── static/                            # Archivos estáticos
    ├── css/styles.css                 # Estilos basados en la paleta de los mockups
    └── js/main.js                     # Asistente en 2 pasos, copiado de token y filtro en vivo
```
