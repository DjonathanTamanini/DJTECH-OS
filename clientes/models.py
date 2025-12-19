from django.db import models
from django.core.validators import RegexValidator


class Cliente(models.Model):
    nome = models.CharField(max_length=200, verbose_name="Nome Completo")
    cpf_cnpj = models.CharField(
        max_length=18, 
        unique=True,
        validators=[RegexValidator(
            r'^\d{3}\.\d{3}\.\d{3}-\d{2}$|^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$',
            'CPF ou CNPJ inválido'
        )],
        verbose_name="CPF/CNPJ"
    )
    telefone_principal = models.CharField(max_length=15, verbose_name="Telefone Principal")
    telefone_secundario = models.CharField(max_length=15, blank=True, null=True, verbose_name="Telefone Secundário")
    email = models.EmailField(blank=True, null=True)
    
    # Endereço
    cep = models.CharField(max_length=9, blank=True, null=True)
    logradouro = models.CharField(max_length=200, blank=True, null=True)
    numero = models.CharField(max_length=10, blank=True, null=True)
    complemento = models.CharField(max_length=100, blank=True, null=True)
    bairro = models.CharField(max_length=100, blank=True, null=True)
    cidade = models.CharField(max_length=100, blank=True, null=True)
    estado = models.CharField(max_length=2, blank=True, null=True)
    
    observacoes = models.TextField(blank=True, null=True)
    data_cadastro = models.DateTimeField(auto_now_add=True)
    ativo = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ['nome']
    
    def __str__(self):
        return f"{self.nome} - {self.telefone_principal}"