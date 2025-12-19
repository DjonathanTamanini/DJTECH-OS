from django.urls import path
from . import views

urlpatterns = [
    path('', views.cliente_lista, name='cliente_lista'),
    path('novo/', views.cliente_criar, name='cliente_criar'),
    path('<int:pk>/', views.cliente_detalhe, name='cliente_detalhe'),
    path('<int:pk>/editar/', views.cliente_editar, name='cliente_editar'),
    path('<int:pk>/deletar/', views.cliente_deletar, name='cliente_deletar'),
]