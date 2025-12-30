from django.contrib import admin
from .models import OrdemServico, PecaUtilizadaOS, HistoricoStatusOS # CORREÇÃO

class PecaUtilizadaInline(admin.TabularInline):
    model = PecaUtilizadaOS # CORREÇÃO
    extra = 0
    fields = ['peca', 'quantidade', 'preco_unitario', 'valor_total']
    readonly_fields = ['valor_total']

class HistoricoStatusInline(admin.TabularInline):
    model = HistoricoStatusOS # CORREÇÃO
    extra = 0
    readonly_fields = ['status_anterior', 'novo_status', 'data_alteracao', 'usuario', 'observacao']
    can_delete = False

@admin.register(OrdemServico)
class OrdemServicoAdmin(admin.ModelAdmin):
    list_display = ['id', 'cliente', 'status', 'data_entrada']
    list_filter = ['status', 'prioridade']
    search_fields = ['id', 'cliente__nome']
    inlines = [PecaUtilizadaInline, HistoricoStatusInline]

@admin.register(PecaUtilizadaOS) # CORREÇÃO
class PecaUtilizadaAdmin(admin.ModelAdmin):
    list_display = ['os', 'peca', 'quantidade', 'valor_total']

@admin.register(HistoricoStatusOS) # CORREÇÃO
class HistoricoStatusAdmin(admin.ModelAdmin):
    list_display = ['os', 'novo_status', 'data_alteracao', 'usuario']