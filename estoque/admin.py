from django.contrib import admin
from django.utils.html import format_html
from .models import CategoriaPeca, Peca, MovimentacaoEstoque


@admin.register(CategoriaPeca)
class CategoriaPecaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'descricao']
    search_fields = ['nome']


@admin.register(Peca)
class PecaAdmin(admin.ModelAdmin):
    list_display = [
        'codigo_interno', 
        'descricao', 
        'categoria', 
        'quantidade_estoque', 
        'status_estoque',
        'preco_venda', 
        'fornecedor_principal',
        'ativo'
    ]
    list_filter = ['categoria', 'ativo', 'fornecedor_principal']
    search_fields = ['codigo_interno', 'descricao']
    list_per_page = 25
    
    fieldsets = (
        ('Identificação', {
            'fields': ('codigo_interno', 'descricao', 'categoria')
        }),
        ('Estoque', {
            'fields': ('quantidade_estoque', 'estoque_minimo', 'localizacao')
        }),
        ('Valores', {
            'fields': ('preco_custo', 'preco_venda')
        }),
        ('Fornecedor', {
            'fields': ('fornecedor_principal',)
        }),
        ('Observações', {
            'fields': ('observacoes', 'ativo'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['data_cadastro']
    
    def status_estoque(self, obj):
        if obj.estoque_baixo:
            return format_html(
                '<span style="color: red; font-weight: bold;">⚠️ BAIXO</span>'
            )
        return format_html(
            '<span style="color: green;">✓ OK</span>'
        )
    status_estoque.short_description = 'Status'


@admin.register(MovimentacaoEstoque)
class MovimentacaoEstoqueAdmin(admin.ModelAdmin):
    list_display = [
        'peca', 
        'tipo', 
        'quantidade', 
        'data_movimentacao', 
        'usuario',
        'ordem_servico'
    ]
    list_filter = ['tipo', 'data_movimentacao']
    search_fields = ['peca__descricao', 'peca__codigo_interno']
    date_hierarchy = 'data_movimentacao'
    list_per_page = 30
    
    fieldsets = (
        ('Movimentação', {
            'fields': ('peca', 'tipo', 'quantidade', 'valor_unitario')
        }),
        ('Relacionamentos', {
            'fields': ('ordem_servico', 'fornecedor', 'usuario')
        }),
        ('Observações', {
            'fields': ('observacoes',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['data_movimentacao', 'usuario']
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.usuario = request.user
        super().save_model(request, obj, form, change)