from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Sum

# Importando modelos externos conforme estrutura existente
from estoque.models import Peca
from clientes.models import Cliente

class OrdemServico(models.Model):
    # --- Configurações de Status (Fluxo Controlado) ---
    STATUS_CHOICES = (
        ('recepcao', '1. Recepção'),
        ('analise', '2. Em Análise'),
        ('aprovacao', '3. Aguardando Aprovação'),
        ('reparo', '4. Em Reparo'),
        ('pronto', '5. Pronto'),
        ('entregue', '6. Entregue'),
        ('cancelado', '7. Cancelado'),
    )

    PRIORIDADE_CHOICES = [
        ('baixa', 'Baixa'),
        ('normal', 'Normal'),
        ('alta', 'Alta'),
        ('urgente', 'Urgente'),
    ]

    # --- Identificação ---
    # Usamos related_name para facilitar queries: cliente.ordens.all()
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='ordens')
    tecnico = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='os_tecnico')
    atendente = models.ForeignKey(User, on_delete=models.PROTECT, related_name='os_atendidas', null=True)
    
    # --- Equipamento ---
    tipo_equipamento = models.CharField(max_length=50, help_text="Ex: TV, Notebook, Celular")
    marca = models.CharField(max_length=50)
    modelo = models.CharField(max_length=50)
    numero_serie = models.CharField(max_length=50, blank=True, null=True)
    
    # --- Diagnóstico e Descrição ---
    defeito_cliente = models.TextField(verbose_name="Defeito relatado", help_text="Descrição do problema segundo o cliente")
    diagnostico_tecnico = models.TextField(blank=True, null=True, verbose_name="Diagnóstico Técnico")
    observacoes_internas = models.TextField(blank=True, null=True, help_text="Visível apenas para a equipe")
    observacoes_cliente = models.TextField(blank=True, null=True, help_text="Observações que saem na impressão")
    
    # --- Controle de Fluxo ---
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='recepcao')
    prioridade = models.CharField(max_length=10, choices=PRIORIDADE_CHOICES, default='normal')
    
    # --- Datas ---
    data_entrada = models.DateTimeField(auto_now_add=True)
    data_previsao = models.DateField(null=True, blank=True, verbose_name="Previsão de Entrega")
    data_conclusao = models.DateTimeField(null=True, blank=True)
    garantia_dias = models.IntegerField(default=90, verbose_name="Garantia (dias)")
    
    # --- Financeiro ---
    valor_mao_de_obra = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    desconto = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    class Meta:
        ordering = ['-data_entrada']
        verbose_name = "Ordem de Serviço"
        verbose_name_plural = "Ordens de Serviço"

    def __str__(self):
        return f"OS #{self.pk} - {self.cliente.nome}"

    # --- Propriedades Calculadas (Business Logic) ---

    @property
    def total_pecas(self):
        """Calcula o valor total das peças somando os itens relacionados."""
        # O aggregate retorna um dict, ex: {'total': 150.00} ou {'total': None}
        resultado = self.pecas.aggregate(total=Sum('valor_total'))['total']
        return resultado if resultado else 0.00

    @property
    def valor_total(self):
        """Calcula o valor final da OS: Mão de obra + Peças - Desconto."""
        # Convertemos para float para evitar erros de tipo Decimal vs Float em templates simples,
        # mas idealmente manteríamos Decimal. Aqui forçamos a conversão para cálculo seguro.
        mdo = self.valor_mao_de_obra or 0
        pecas = self.total_pecas or 0
        desc = self.desconto or 0
        return mdo + pecas - desc

    @property
    def esta_atrasada(self):
        """Verifica se a OS está atrasada (Previsão passada e não finalizada)."""
        if self.status not in ['pronto', 'entregue', 'cancelado'] and self.data_previsao:
            return self.data_previsao < timezone.now().date()
        return False

    @property
    def status_display_badge(self):
        """Helper para retornar a classe CSS do Bootstrap baseada no status."""
        classes = {
            'recepcao': 'secondary',
            'analise': 'info',
            'aprovacao': 'warning',
            'reparo': 'primary',
            'pronto': 'success',
            'entregue': 'success', # Darker green usually handled in CSS
            'cancelado': 'danger',
        }
        return classes.get(self.status, 'secondary')


class HistoricoStatusOS(models.Model):
    """
    Tabela imutável (Append-only) para auditoria e rastreabilidade do fluxo.
    Toda mudança de status na View deve gerar um registro aqui.
    """
    os = models.ForeignKey(OrdemServico, on_delete=models.CASCADE, related_name='historico')
    status_anterior = models.CharField(max_length=20, choices=OrdemServico.STATUS_CHOICES, null=True, blank=True)
    novo_status = models.CharField(max_length=20, choices=OrdemServico.STATUS_CHOICES)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    data_alteracao = models.DateTimeField(auto_now_add=True)
    observacao = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-data_alteracao']

    def __str__(self):
        return f"{self.os.pk}: {self.novo_status} em {self.data_alteracao}"


class PecaUtilizadaOS(models.Model):
    """
    Relacionamento N:N entre OS e Estoque.
    IMPORTANTE: Grava o preço unitário NO MOMENTO da adição para histórico financeiro.
    """
    os = models.ForeignKey(OrdemServico, on_delete=models.CASCADE, related_name='pecas')
    peca = models.ForeignKey(Peca, on_delete=models.PROTECT)
    quantidade = models.IntegerField(default=1)
    
    # Snapshot do preço (se o preço da peça subir amanhã, essa OS antiga não muda de valor)
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Preço Unitário (Venda)")
    valor_total = models.DecimalField(max_digits=10, decimal_places=2, editable=False)

    class Meta:
        verbose_name = "Peça Utilizada"
        verbose_name_plural = "Peças Utilizadas"

    def save(self, *args, **kwargs):
        # Auto-cálculo do total da linha antes de salvar
        self.valor_total = self.quantidade * self.preco_unitario
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.peca.nome} (x{self.quantidade})"


class FotoOS(models.Model):
    """
    Modelo dedicado para uploads de fotos do equipamento (entrada, defeito, pronto).
    """
    os = models.ForeignKey(OrdemServico, on_delete=models.CASCADE, related_name='fotos')
    imagem = models.ImageField(upload_to='os_fotos/%Y/%m/')
    descricao = models.CharField(max_length=100, blank=True, help_text="Ex: Arranhão na tampa, Tela quebrada")
    data_upload = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Foto OS #{self.os.pk}"