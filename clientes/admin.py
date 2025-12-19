from django.contrib import admin
from .models import Cliente


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['nome', 'cpf_cnpj', 'telefone_principal', 'cidade', 'ativo', 'data_cadastro']
    list_filter = ['ativo', 'cidade', 'estado']
    search_fields = ['nome', 'cpf_cnpj', 'telefone_principal', 'email']
    list_per_page = 20
    
    fieldsets = (
        ('Dados Principais', {
            'fields': ('nome', 'cpf_cnpj', 'email')
        }),
        ('Contatos', {
            'fields': ('telefone_principal', 'telefone_secundario')
        }),
        ('Endereço', {
            'fields': ('cep', 'logradouro', 'numero', 'complemento', 'bairro', 'cidade', 'estado'),
            'classes': ('collapse',)
        }),
        ('Observações', {
            'fields': ('observacoes', 'ativo'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['data_cadastro']