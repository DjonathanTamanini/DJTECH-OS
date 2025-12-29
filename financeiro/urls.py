from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.dashboard_financeiro, name='financeiro_dashboard'),
    
    # Transações
    path('transacoes/', views.transacao_lista, name='transacao_lista'),
    path('transacoes/nova/', views.transacao_criar, name='transacao_criar'),
    path('transacoes/<int:pk>/editar/', views.transacao_editar, name='transacao_editar'),
    path('transacoes/<int:pk>/deletar/', views.transacao_deletar, name='transacao_deletar'),
    path('transacoes/<int:pk>/pagar/', views.transacao_pagar, name='transacao_pagar'),
    
    # Relatórios
    path('relatorio/', views.relatorio_financeiro, name='relatorio_financeiro'),
    
    # Categorias
    path('categorias/', views.categoria_lista, name='categoria_financeira_lista'),
    path('categorias/nova/', views.categoria_criar, name='categoria_financeira_criar'),

    # Notas Fiscais
    path('notas/', views.nota_fiscal_lista, name='nota_fiscal_lista'),
    path('notas/nova/', views.nota_fiscal_criar, name='nota_fiscal_criar'),
    path('notas/<int:pk>/', views.nota_fiscal_detalhe, name='nota_fiscal_detalhe'),
    path('notas/<int:pk>/integrar-estoque/', views.nota_fiscal_integrar_estoque, name='nota_fiscal_integrar_estoque'),
    path('notas/<int:pk>/integrar-financeiro/', views.nota_fiscal_integrar_financeiro, name='nota_fiscal_integrar_financeiro'),
    path('notas/<int:pk>/integrar-completo/', views.nota_fiscal_integrar_completo, name='nota_fiscal_integrar_completo'),
]