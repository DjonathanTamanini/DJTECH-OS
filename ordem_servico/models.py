from django.db import models
from datetime import timedelta


class OrdemServico(models.Model):
    STATUS_CHOICES = [
        ('recepcao', 'Recepção'),
        ('avaliacao', 'Em Avaliação'),
        ('aguardando_aprovacao', 'Aguardando Aprovação'),
        ('aprovado', 'Aprovado'),
        ('em_reparo', 'Em Reparo'),
        ('concluido', 'Concluído'),
        ('entregue', 'Entregue'),
        ('cancelado', 'Cancelado'),
    ]
    
    TIPO_EQUIPAMENTO_CHOICES = [
        ('tv', 'TV'),
        ('notebook', 'Notebook'),
        ('desktop', 'Computador Desktop'),
        ('monitor', 'Monitor'),
        ('impressora', 'Impressora'),
        ('outro', 'Outro'),
    ]
    
    # Identificação
    numero_os = models.CharField(max_length=20, unique=True, verbose_name="Número da OS")
    cliente = models.ForeignKey('clientes.Cliente', on_delete=models.PROTECT, related_name='ordens_servico')
    
    # Equipamento
    tipo_equipamento = models.CharField(max_length=20, choices=TIPO_EQUIPAMENTO_CHOICES)
    marca = models.CharField(max_length=100)
    modelo = models.CharField(max_length=100)
    numero_serie = models.CharField(max_length=100, blank=True, null=True, verbose_name="Número de Série")
    
    # Defeitos
    defeito_relatado = models.TextField(verbose_name="Defeito Relatado pelo Cliente")
    defeito_encontrado = models.TextField(blank=True, null=True, verbose_name="Defeito Encontrado")
    
    # Status e datas
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='recepcao')
    data_entrada = models.DateTimeField(auto_now_add=True)
    data_avaliacao = models.DateTimeField(null=True, blank=True)
    data_aprovacao = models.DateTimeField(null=True, blank=True)
    prazo_estimado = models.DateField(null=True, blank=True)
    data_conclusao = models.DateTimeField(null=True, blank=True)
    data_entrega = models.DateTimeField(null=True, blank=True)
    
    # Valores
    valor_mao_obra = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Valor Mão de Obra")
    valor_pecas = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Valor das Peças")
    desconto = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    valor_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Garantia
    dias_garantia = models.IntegerField(default=90, verbose_name="Dias de Garantia")
    data_fim_garantia = models.DateField(null=True, blank=True)
    
    # Responsáveis
    atendente = models.ForeignKey(
        'auth.User', 
        on_delete=models.PROTECT, 
        related_name='os_atendidas',
        verbose_name="Atendente Responsável"
    )
    tecnico = models.ForeignKey(
        'auth.User', 
        on_delete=models.PROTECT, 
        related_name='os_tecnico',
        null=True,
        blank=True,
        verbose_name="Técnico Responsável"
    )
    
    observacoes_internas = models.TextField(blank=True, null=True, verbose_name="Observações Internas")
    observacoes_cliente = models.TextField(blank=True, null=True, verbose_name="Observações para o Cliente")
    
    class Meta:
        verbose_name = "Ordem de Serviço"
        verbose_name_plural = "Ordens de Serviço"
        ordering = ['-data_entrada']
    
    def __str__(self):
        return f"OS {self.numero_os} - {self.cliente.nome}"
    
    def calcular_total(self):
        self.valor_total = (self.valor_mao_obra + self.valor_pecas) - self.desconto
        return self.valor_total
    
    def save(self, *args, **kwargs):
        # Gerar número da OS automaticamente se não existir
        if not self.numero_os:
            ultimo = OrdemServico.objects.order_by('-id').first()
            if ultimo:
                numero = int(ultimo.numero_os.split('-')[1]) + 1
            else:
                numero = 1
            self.numero_os = f"OS-{numero:06d}"
        
        # Calcular valor total
        self.calcular_total()
        
        # Calcular data fim garantia quando entregue
        if self.status == 'entregue' and self.data_entrega and not self.data_fim_garantia:
            self.data_fim_garantia = self.data_entrega.date() + timedelta(days=self.dias_garantia)
        
        super().save(*args, **kwargs)


class PecaUtilizada(models.Model):
    ordem_servico = models.ForeignKey(OrdemServico, on_delete=models.CASCADE, related_name='pecas_utilizadas')
    peca = models.ForeignKey('estoque.Peca', on_delete=models.PROTECT)
    quantidade = models.IntegerField(default=1)
    valor_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    valor_total = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        verbose_name = "Peça Utilizada"
        verbose_name_plural = "Peças Utilizadas"
    
    def __str__(self):
        return f"{self.peca.descricao} - {self.quantidade}un"
    
    def save(self, *args, **kwargs):
        self.valor_total = self.quantidade * self.valor_unitario
        super().save(*args, **kwargs)


class HistoricoOS(models.Model):
    ordem_servico = models.ForeignKey(OrdemServico, on_delete=models.CASCADE, related_name='historico')
    status_anterior = models.CharField(max_length=30)
    status_novo = models.CharField(max_length=30)
    data_alteracao = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey('auth.User', on_delete=models.PROTECT)
    observacao = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Histórico da OS"
        verbose_name_plural = "Históricos das OS"
        ordering = ['-data_alteracao']
    
    def __str__(self):
        return f"OS {self.ordem_servico.numero_os} - {self.status_anterior} → {self.status_novo}"