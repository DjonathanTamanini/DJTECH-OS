from django.urls import path
from . import views

urlpatterns = [
    path('', views.fornecedor_lista, name='fornecedor_lista'),
    path('novo/', views.fornecedor_criar, name='fornecedor_criar'),
    path('<int:pk>/', views.fornecedor_detalhe, name='fornecedor_detalhe'),
    path('<int:pk>/editar/', views.fornecedor_editar, name='fornecedor_editar'),
    path('<int:pk>/deletar/', views.fornecedor_deletar, name='fornecedor_deletar'),
]