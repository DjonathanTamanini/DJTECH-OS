from django.contrib import admin
from .models import Fornecedor


@admin.register(Fornecedor)
class FornecedorAdmin(admin.ModelAdmin):
    list_display = ['razao_social', 'nome_fantasia', 'cnpj', 'telefone', 'cidade', 'ativo']
    list_filter = ['ativo', 'cidade', 'estado']
    search_fields = ['razao_social', 'nome_fantasia', 'cnpj', 'telefone']
    list_per_page = 20
    
    fieldsets = (
        ('Dados da Empresa', {
            'fields': ('razao_social', 'nome_fantasia', 'cnpj')
        }),
        ('Contatos', {
            'fields': ('telefone', 'email', 'contato_responsavel')
        }),
        ('Endereço', {
            'fields': ('cep', 'logradouro', 'numero', 'complemento', 'bairro', 'cidade', 'estado'),
            'classes': ('collapse',)
        }),
        ('Informações Adicionais', {
            'fields': ('condicoes_pagamento', 'observacoes', 'ativo'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['data_cadastro']