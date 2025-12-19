from django.db import models


class CategoriaPeca(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Categoria de Peça"
        verbose_name_plural = "Categorias de Peças"
        ordering = ['nome']
    
    def __str__(self):
        return self.nome


class Peca(models.Model):
    codigo_interno = models.CharField(max_length=50, unique=True, verbose_name="Código Interno")
    descricao = models.CharField(max_length=300, verbose_name="Descrição")
    categoria = models.ForeignKey(CategoriaPeca, on_delete=models.PROTECT, related_name='pecas')
    
    # Estoque
    quantidade_estoque = models.IntegerField(default=0, verbose_name="Quantidade em Estoque")
    estoque_minimo = models.IntegerField(default=1, verbose_name="Estoque Mínimo")
    localizacao = models.CharField(max_length=100, blank=True, null=True, verbose_name="Localização no Estoque")
    
    # Valores
    preco_custo = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Preço de Custo")
    preco_venda = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Preço de Venda")
    
    # Relacionamentos
    fornecedor_principal = models.ForeignKey(
        'fornecedores.Fornecedor', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='pecas_fornecidas',
        verbose_name="Fornecedor Principal"
    )
    
    observacoes = models.TextField(blank=True, null=True)
    data_cadastro = models.DateTimeField(auto_now_add=True)
    ativo = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Peça"
        verbose_name_plural = "Peças"
        ordering = ['descricao']
    
    def __str__(self):
        return f"{self.codigo_interno} - {self.descricao}"
    
    @property
    def estoque_baixo(self):
        return self.quantidade_estoque <= self.estoque_minimo


class MovimentacaoEstoque(models.Model):
    TIPO_CHOICES = [
        ('entrada', 'Entrada'),
        ('saida', 'Saída'),
        ('ajuste', 'Ajuste'),
    ]
    
    peca = models.ForeignKey(Peca, on_delete=models.PROTECT, related_name='movimentacoes')
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    quantidade = models.IntegerField()
    data_movimentacao = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey('auth.User', on_delete=models.PROTECT)
    
    # Relacionamentos opcionais
    ordem_servico = models.ForeignKey(
        'ordem_servico.OrdemServico', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='movimentacoes_estoque'
    )
    fornecedor = models.ForeignKey(
        'fornecedores.Fornecedor',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    valor_unitario = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    observacoes = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Movimentação de Estoque"
        verbose_name_plural = "Movimentações de Estoque"
        ordering = ['-data_movimentacao']
    
    def __str__(self):
        return f"{self.tipo.upper()} - {self.peca.codigo_interno} - {self.quantidade}un"