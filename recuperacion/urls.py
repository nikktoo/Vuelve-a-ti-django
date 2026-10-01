from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('registro/', views.registro_view, name='registro'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('reportar-perdido/', views.reportar_perdido, name='reportar_perdido'),
    path('reportar-hallazgo/', views.reportar_hallazgo, name='reportar_hallazgo'),
    path('buscar/', views.buscar_objetos, name='buscar_objetos'),
    path('objeto/<int:pk>/', views.detalle_objeto, name='detalle_objeto'),
    path('conserjeria/', views.conserjeria_panel, name='conserjeria_panel'),
    path('conserjeria/validar/<int:pk>/', views.validar_entrega, name='validar_entrega'),
    path('coincidencias/', views.coincidencias_lista, name='coincidencias_lista'),
    path('coincidencias/<int:pk>/', views.detalle_coincidencia, name='detalle_coincidencia'),
    path('metricas/', views.metricas_view, name='metricas'),
    path('historial/', views.historial_avanzado, name='historial_avanzado'),
    path('incidencia/', views.reportar_incidencia, name='reportar_incidencia'),
    path('incidencia/<int:objeto_id>/', views.reportar_incidencia, name='reportar_incidencia_objeto'),
    path('gestion-recintos/', views.gestion_recintos, name='gestion_recintos'),
    path('notificaciones/marcar-leidas/', views.marcar_notificaciones_leidas, name='marcar_notificaciones_leidas'),
]
