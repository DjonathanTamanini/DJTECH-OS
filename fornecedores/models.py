from django.db import models
from django.core.validators import RegexValidator


class Fornecedor(models.Model):
    razao_social = models.CharField(max_length=200, verbose_name="Razão Social")
    nome_fantasia = models.CharField(max_length=200, blank=True, null=True, verbose_name="Nome Fantasia")
    cnpj = models.CharField(
        max_length=18, 
        unique=True,
        validators=[RegexValidator(
            r'^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$',
            'CNPJ inválido'
        )],
        verbose_name="CNPJ"
    )
    
    # Contatos
    telefone = models.CharField(max_length=15)
    email = models.EmailField(blank=True, null=True)
    contato_responsavel = models.CharField(max_length=100, blank=True, null=True)
    
    # Endereço
    cep = models.CharField(max_length=9, blank=True, null=True)
    logradouro = models.CharField(max_length=200, blank=True, null=True)
    numero = models.CharField(max_length=10, blank=True, null=True)
    complemento = models.CharField(max_length=100, blank=True, null=True)
    bairro = models.CharField(max_length=100, blank=True, null=True)
    cidade = models.CharField(max_length=100, blank=True, null=True)
    estado = models.CharField(max_length=2, blank=True, null=True)
    
    condicoes_pagamento = models.TextField(blank=True, null=True, verbose_name="Condições de Pagamento")
    observacoes = models.TextField(blank=True, null=True)
    data_cadastro = models.DateTimeField(auto_now_add=True)
    ativo = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Fornecedor"
        verbose_name_plural = "Fornecedores"
        ordering = ['razao_social']
    
    def __str__(self):
        return self.nome_fantasia or self.razao_social