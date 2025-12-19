from django.contrib import admin
from django.utils.html import format_html
from .models import CategoriaFinanceira, Transacao, ContaBancaria


@admin.register(CategoriaFinanceira)
class CategoriaFinanceiraAdmin(admin.ModelAdmin):
    list_display = ['nome', 'tipo', 'cor_display', 'ativo']
    list_filter = ['tipo', 'ativo']
    search_fields = ['nome']
    
    def cor_display(self, obj):
        return format_html(
            '<span style="background-color: {}; padding: 5px 15px; border-radius: 3px; color: white;">{}</span>',
            obj.cor,
            obj.cor
        )
    cor_display.short_description = 'Cor'


@admin.register(Transacao)
class TransacaoAdmin(admin.ModelAdmin):
    list_display = ['descricao', 'tipo', 'categoria', 'valor', 'data_vencimento', 'status', 'esta_vencida_display']
    list_filter = ['tipo', 'status', 'categoria', 'forma_pagamento', 'data_vencimento']
    search_fields = ['descricao']
    date_hierarchy = 'data_vencimento'
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('tipo', 'categoria', 'descricao', 'valor')
        }),
        ('Datas', {
            'fields': ('data_vencimento', 'data_pagamento')
        }),
        ('Status e Pagamento', {
            'fields': ('status', 'forma_pagamento')
        }),
        ('Relacionamentos', {
            'fields': ('ordem_servico', 'fornecedor'),
            'classes': ('collapse',)
        }),
        ('Observações', {
            'fields': ('observacoes', 'usuario'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['usuario', 'data_cadastro', 'data_atualizacao']
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.usuario = request.user
        super().save_model(request, obj, form, change)
    
    def esta_vencida_display(self, obj):
        if obj.esta_vencida:
            return format_html('<span style="color: red; font-weight: bold;">⚠️ Vencida</span>')
        return format_html('<span style="color: green;">✓ OK</span>')
    esta_vencida_display.short_description = 'Vencimento'


@admin.register(ContaBancaria)
class ContaBancariaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'banco', 'saldo_atual_display', 'ativo']
    list_filter = ['ativo']
    search_fields = ['nome', 'banco']
    
    def saldo_atual_display(self, obj):
        saldo = obj.calcular_saldo()
        cor = 'green' if saldo >= 0 else 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">R$ {:.2f}</span>',
            cor,
            saldo
        )
    saldo_atual_display.short_description = 'Saldo Atual'