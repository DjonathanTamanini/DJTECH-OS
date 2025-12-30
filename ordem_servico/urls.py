from django.urls import path
from . import views

urlpatterns = [
    path('', views.ordem_servico_lista, name='ordem_servico_lista'),
    path('nova/', views.ordem_servico_criar, name='ordem_servico_criar'),
    path('<int:pk>/', views.ordem_servico_detalhe, name='ordem_servico_detalhe'),
    path('<int:pk>/editar/', views.ordem_servico_editar, name='ordem_servico_editar'),
    path('<int:pk>/imprimir/', views.ordem_servico_imprimir, name='ordem_servico_imprimir'),
    
    # Rotas AJAX
    path('buscar-clientes/', views.buscar_clientes_ajax, name='buscar_clientes_ajax'),
    path('api/buscar-pecas-json/', views.api_buscar_pecas_json, name='api_buscar_pecas_json'),
]