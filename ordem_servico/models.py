from django.db import models
from datetime import timedelta
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings


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
        ('celular', 'Celular/Smartphone'),
        ('tablet', 'Tablet'),
        ('outro', 'Outro'),
    ]
    
    PRIORIDADE_CHOICES = [
        ('baixa', 'Baixa'),
        ('normal', 'Normal'),
        ('alta', 'Alta'),
        ('urgente', 'Urgente'),
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
    solucao_aplicada = models.TextField(blank=True, null=True, verbose_name="Solução Aplicada")
    
    # Status e datas
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='recepcao')
    prioridade = models.CharField(max_length=10, choices=PRIORIDADE_CHOICES, default='normal')
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
    
    # Notificações
    cliente_notificado_entrada = models.BooleanField(default=False)
    cliente_notificado_orcamento = models.BooleanField(default=False)
    cliente_notificado_conclusao = models.BooleanField(default=False)
    ultima_notificacao = models.DateTimeField(null=True, blank=True)
    
    # Avaliação
    avaliacao_cliente = models.IntegerField(null=True, blank=True, choices=[(i, i) for i in range(1, 6)])
    comentario_avaliacao = models.TextField(blank=True, null=True)
    
    observacoes_internas = models.TextField(blank=True, null=True, verbose_name="Observações Internas")
    observacoes_cliente = models.TextField(blank=True, null=True, verbose_name="Observações para o Cliente")
    
    class Meta:
        verbose_name = "Ordem de Serviço"
        verbose_name_plural = "Ordens de Serviço"
        ordering = ['-data_entrada']
        indexes = [
            models.Index(fields=['status', 'data_entrada']),
            models.Index(fields=['cliente', 'status']),
            models.Index(fields=['prazo_estimado']),
        ]
    
    def __str__(self):
        return f"OS {self.numero_os} - {self.cliente.nome}"
    
    def calcular_total(self):
        self.valor_total = (self.valor_mao_obra + self.valor_pecas) - self.desconto
        return self.valor_total
    
    def esta_atrasada(self):
        """Verifica se a OS está atrasada"""
        if self.prazo_estimado and self.status not in ['concluido', 'entregue', 'cancelado']:
            from datetime import date
            return date.today() > self.prazo_estimado
        return False
    
    def tempo_em_reparo(self):
        """Calcula o tempo total em reparo"""
        if self.data_conclusao:
            return (self.data_conclusao - self.data_entrada).days
        return (timezone.now() - self.data_entrada).days
    
    def enviar_notificacao_email(self, tipo):
        """Envia notificação por email ao cliente"""
        if not self.cliente.email:
            return False
        
        assunto = f"OS {self.numero_os} - "
        mensagem = ""
        
        if tipo == 'entrada':
            assunto += "Equipamento Recebido"
            mensagem = f"""
Olá {self.cliente.nome},

Confirmamos o recebimento do seu equipamento:
- Tipo: {self.get_tipo_equipamento_display()}
- Marca: {self.marca}
- Modelo: {self.modelo}
- Defeito: {self.defeito_relatado}

Número da OS: {self.numero_os}
Prazo Estimado: {self.prazo_estimado.strftime('%d/%m/%Y') if self.prazo_estimado else 'A definir'}

Você pode acompanhar o status da sua OS pelo nosso sistema.

Atenciosamente,
{settings.COMPANY_NAME if hasattr(settings, 'COMPANY_NAME') else 'DJTECH-OS'}
            """
            self.cliente_notificado_entrada = True
            
        elif tipo == 'orcamento':
            assunto += "Orçamento Disponível"
            mensagem = f"""
Olá {self.cliente.nome},

O orçamento da sua OS {self.numero_os} está disponível:

- Mão de Obra: R$ {self.valor_mao_obra}
- Peças: R$ {self.valor_pecas}
- Desconto: R$ {self.desconto}
TOTAL: R$ {self.valor_total}

Por favor, entre em contato para aprovação do orçamento.

Atenciosamente,
{settings.COMPANY_NAME if hasattr(settings, 'COMPANY_NAME') else 'DJTECH-OS'}
            """
            self.cliente_notificado_orcamento = True
            
        elif tipo == 'conclusao':
            assunto += "Reparo Concluído - Equipamento Pronto"
            mensagem = f"""
Olá {self.cliente.nome},

Seu equipamento está pronto para retirada!

OS: {self.numero_os}
Equipamento: {self.get_tipo_equipamento_display()} {self.marca} {self.modelo}
Valor Total: R$ {self.valor_total}

Aguardamos você em nosso estabelecimento.

Atenciosamente,
{settings.COMPANY_NAME if hasattr(settings, 'COMPANY_NAME') else 'DJTECH-OS'}
            """
            self.cliente_notificado_conclusao = True
        
        try:
            send_mail(
                assunto,
                mensagem,
                settings.DEFAULT_FROM_EMAIL,
                [self.cliente.email],
                fail_silently=False,
            )
            self.ultima_notificacao = timezone.now()
            self.save()
            return True
        except Exception as e:
            print(f"Erro ao enviar email: {e}")
            return False
    
    def save(self, *args, **kwargs):
        status_anterior = None
        if self.pk:
            status_anterior = OrdemServico.objects.get(pk=self.pk).status
        
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
        
        # Enviar notificações automáticas
        if status_anterior != self.status:
            if self.status == 'recepcao' and not self.cliente_notificado_entrada:
                self.enviar_notificacao_email('entrada')
            elif self.status == 'aguardando_aprovacao' and not self.cliente_notificado_orcamento:
                self.enviar_notificacao_email('orcamento')
            elif self.status == 'concluido' and not self.cliente_notificado_conclusao:
                self.enviar_notificacao_email('conclusao')


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


class AnexoOS(models.Model):
    """Model para armazenar fotos e documentos da OS"""
    TIPO_CHOICES = [
        ('foto_entrada', 'Foto na Entrada'),
        ('foto_defeito', 'Foto do Defeito'),
        ('foto_reparo', 'Foto do Reparo'),
        ('foto_entrega', 'Foto na Entrega'),
        ('documento', 'Documento'),
        ('outro', 'Outro'),
    ]
    
    ordem_servico = models.ForeignKey(OrdemServico, on_delete=models.CASCADE, related_name='anexos')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    arquivo = models.FileField(upload_to='os_anexos/%Y/%m/')
    descricao = models.CharField(max_length=200, blank=True)
    data_upload = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey('auth.User', on_delete=models.PROTECT)
    
    class Meta:
        verbose_name = "Anexo da OS"
        verbose_name_plural = "Anexos das OS"
        ordering = ['-data_upload']
    
    def __str__(self):
        return f"Anexo {self.get_tipo_display()} - OS {self.ordem_servico.numero_os}"


class ChecklistOS(models.Model):
    """Checklist de verificação do equipamento"""
    ordem_servico = models.OneToOneField(OrdemServico, on_delete=models.CASCADE, related_name='checklist')
    
    # Itens do checklist
    possui_arranhoes = models.BooleanField(default=False, verbose_name="Possui arranhões")
    possui_amassados = models.BooleanField(default=False, verbose_name="Possui amassados")
    possui_quebras = models.BooleanField(default=False, verbose_name="Possui quebras")
    possui_oxidacao = models.BooleanField(default=False, verbose_name="Possui oxidação")
    liga_normalmente = models.BooleanField(default=True, verbose_name="Liga normalmente")
    tem_senha = models.BooleanField(default=False, verbose_name="Equipamento tem senha")
    senha_fornecida = models.BooleanField(default=False, verbose_name="Senha foi fornecida")
    
    # Acessórios
    possui_bateria = models.BooleanField(default=True, verbose_name="Possui bateria")
    possui_carregador = models.BooleanField(default=False, verbose_name="Possui carregador")
    possui_cabo = models.BooleanField(default=False, verbose_name="Possui cabo")
    possui_case = models.BooleanField(default=False, verbose_name="Possui case/capa")
    
    observacoes_checklist = models.TextField(blank=True, null=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Checklist da OS"
        verbose_name_plural = "Checklists das OS"
    
    def __str__(self):
        return f"Checklist - OS {self.ordem_servico.numero_os}"