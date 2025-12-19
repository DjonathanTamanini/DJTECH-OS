from django.db import models
from django.contrib.auth.models import User


class CategoriaFinanceira(models.Model):
    TIPO_CHOICES = [
        ('receita', 'Receita'),
        ('despesa', 'Despesa'),
    ]
    
    nome = models.CharField(max_length=100)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    descricao = models.TextField(blank=True, null=True)
    cor = models.CharField(max_length=7, default='#3498db', help_text='Cor em hexadecimal')
    ativo = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Categoria Financeira"
        verbose_name_plural = "Categorias Financeiras"
        ordering = ['tipo', 'nome']
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.nome}"


class Transacao(models.Model):
    TIPO_CHOICES = [
        ('receita', 'Receita'),
        ('despesa', 'Despesa'),
    ]
    
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('pago', 'Pago'),
        ('cancelado', 'Cancelado'),
    ]
    
    FORMA_PAGAMENTO_CHOICES = [
        ('dinheiro', 'Dinheiro'),
        ('pix', 'PIX'),
        ('cartao_debito', 'Cartão de Débito'),
        ('cartao_credito', 'Cartão de Crédito'),
        ('transferencia', 'Transferência Bancária'),
        ('boleto', 'Boleto'),
        ('outros', 'Outros'),
    ]
    
    # Identificação
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    categoria = models.ForeignKey(CategoriaFinanceira, on_delete=models.PROTECT, related_name='transacoes')
    descricao = models.CharField(max_length=300)
    
    # Valores
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Datas
    data_vencimento = models.DateField()
    data_pagamento = models.DateField(null=True, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    forma_pagamento = models.CharField(max_length=20, choices=FORMA_PAGAMENTO_CHOICES, blank=True, null=True)
    
    # Relacionamentos opcionais
    ordem_servico = models.ForeignKey(
        'ordem_servico.OrdemServico',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transacoes_financeiras'
    )
    
    fornecedor = models.ForeignKey(
        'fornecedores.Fornecedor',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transacoes'
    )
    
    # Controle
    observacoes = models.TextField(blank=True, null=True)
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    data_cadastro = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Transação"
        verbose_name_plural = "Transações"
        ordering = ['-data_vencimento']
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.descricao} - R$ {self.valor}"
    
    @property
    def esta_vencida(self):
        """Verifica se a transação está vencida"""
        from datetime import date
        if self.status == 'pendente' and self.data_vencimento < date.today():
            return True
        return False


class ContaBancaria(models.Model):
    nome = models.CharField(max_length=100, help_text='Ex: Conta Corrente Banco X')
    banco = models.CharField(max_length=100)
    agencia = models.CharField(max_length=20, blank=True, null=True)
    conta = models.CharField(max_length=30, blank=True, null=True)
    saldo_inicial = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    ativo = models.BooleanField(default=True)
    observacoes = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Conta Bancária"
        verbose_name_plural = "Contas Bancárias"
        ordering = ['nome']
    
    def __str__(self):
        return self.nome
    
    def calcular_saldo(self):
        """Calcula o saldo atual da conta"""
        receitas = Transacao.objects.filter(
            tipo='receita',
            status='pago'
        ).aggregate(total=models.Sum('valor'))['total'] or 0
        
        despesas = Transacao.objects.filter(
            tipo='despesa',
            status='pago'
        ).aggregate(total=models.Sum('valor'))['total'] or 0
        
        return self.saldo_inicial + receitas - despesas