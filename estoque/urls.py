from django.urls import path
from . import views

urlpatterns = [
    # Peças
    path('', views.peca_lista, name='peca_lista'),
    path('peca/nova/', views.peca_criar, name='peca_criar'),
    path('peca/<int:pk>/', views.peca_detalhe, name='peca_detalhe'),
    path('peca/<int:pk>/editar/', views.peca_editar, name='peca_editar'),
    path('peca/<int:pk>/deletar/', views.peca_deletar, name='peca_deletar'),
    
    # Movimentações
    path('movimentacao/nova/', views.movimentacao_criar, name='movimentacao_criar'),
    
    # Categorias
    path('categorias/', views.categoria_lista, name='categoria_lista'),
    path('categoria/nova/', views.categoria_criar, name='categoria_criar'),
    path('categoria/<int:pk>/editar/', views.categoria_editar, name='categoria_editar'),
]