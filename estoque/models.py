from django.db import models
from django.core.validators import MinValueValidator
import uuid


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
    codigo_interno = models.CharField(
        max_length=50, unique=True, editable=False, verbose_name="Código Interno"
    )
    part_number = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Part Number"
    )
    nome = models.CharField(max_length=200, verbose_name="Nome da Peça")
    descricao = models.TextField(blank=True, null=True)
    categoria = models.ForeignKey(CategoriaPeca, on_delete=models.PROTECT, related_name='pecas')
    
    # Preços e Margens
    ultimo_preco_compra = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00, verbose_name="Último Preço de Compra"
    )
    preco_venda = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00, verbose_name="Preço de Venda"
    )
    margem_lucro = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00, verbose_name="Margem de Lucro (%)"
    )
    
    quantidade_minima = models.IntegerField(default=5, verbose_name="Quantidade Mínima")
    localizacao = models.CharField(max_length=100, blank=True, null=True, verbose_name="Localização")
    fornecedor_principal = models.ForeignKey(
        'fornecedores.Fornecedor', on_delete=models.SET_NULL, null=True, blank=True
    )
    observacoes = models.TextField(blank=True, null=True)
    ativo = models.BooleanField(default=True)
    data_cadastro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Peça"
        verbose_name_plural = "Peças"
        ordering = ['nome']

    def __str__(self):
        return f"{self.codigo_interno} - {self.nome}"

    def save(self, *args, **kwargs):
        # Gera código interno se não existir
        if not self.codigo_interno:
            self.codigo_interno = f"PC-{uuid.uuid4().hex[:8].upper()}"
        
        # Calcula preço de venda baseado na margem se houver custo
        if self.ultimo_preco_compra > 0 and self.margem_lucro > 0:
            self.preco_venda = self.ultimo_preco_compra * (1 + (self.margem_lucro / 100))
            
        super().save(*args, **kwargs)

    @property
    def quantidade_estoque(self):
        """Calcula o saldo atual baseado nas movimentações"""
        from .models import MovimentacaoEstoque
        from django.db.models import Sum, Q
        
        entradas = MovimentacaoEstoque.objects.filter(
            peca=self, tipo='entrada'
        ).aggregate(total=Sum('quantidade'))['total'] or 0
        
        saidas = MovimentacaoEstoque.objects.filter(
            peca=self, tipo='saida'
        ).aggregate(total=Sum('quantidade'))['total'] or 0
        
        return entradas - saidas

    @property
    def valor_total_estoque(self):
        """Calcula o valor financeiro total da peça no estoque"""
        return float(self.quantidade_estoque) * float(self.preco_venda)


class MovimentacaoEstoque(models.Model):
    TIPO_CHOICES = [
        ('entrada', 'Entrada'),
        ('saida', 'Saída'),
        ('ajuste', 'Ajuste'),
    ]
    
    peca = models.ForeignKey(
        Peca,
        on_delete=models.PROTECT,
        related_name='movimentacoes'
    )
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    quantidade = models.IntegerField(validators=[MinValueValidator(1)])
    
    # Valor unitário da movimentação
    valor_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Valor Unitário",
        help_text="Valor unitário nesta movimentação"
    )
    
    data_movimentacao = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey('auth.User', on_delete=models.PROTECT)
    
    # Relacionamento com Nota Fiscal (entrada via financeiro)
    nota_fiscal = models.ForeignKey(
        'financeiro.NotaFiscal',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movimentacoes_estoque',
        verbose_name="Nota Fiscal"
    )
    
    # Relacionamento com Ordem de Serviço (saída)
    ordem_servico = models.ForeignKey(
        'ordem_servico.OrdemServico',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movimentacoes_estoque'
    )
    
    # Fornecedor (para entradas manuais sem nota)
    fornecedor = models.ForeignKey(
        'fornecedores.Fornecedor',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    observacoes = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Movimentação de Estoque"
        verbose_name_plural = "Movimentações de Estoque"
        ordering = ['-data_movimentacao']
    
    def __str__(self):
        return f"{self.tipo.upper()} - {self.peca.codigo_interno} - {self.quantidade}un"
    
    def save(self, *args, **kwargs):
        # Atualiza o último preço de compra da peça se for ENTRADA
        if self.tipo == 'entrada' and self.valor_unitario > 0:
            self.peca.ultimo_preco_compra = self.valor_unitario
            self.peca.save()
        
        super().save(*args, **kwargs)
    
    @property
    def valor_total(self):
        """Calcula o valor total da movimentação"""
        return self.quantidade * self.valor_unitario