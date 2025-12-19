from django.contrib import admin
from django.utils.html import format_html
from .models import OrdemServico, PecaUtilizada, HistoricoOS


class PecaUtilizadaInline(admin.TabularInline):
    model = PecaUtilizada
    extra = 1
    fields = ['peca', 'quantidade', 'valor_unitario', 'valor_total']
    readonly_fields = ['valor_total']


class HistoricoOSInline(admin.TabularInline):
    model = HistoricoOS
    extra = 0
    fields = ['status_anterior', 'status_novo', 'data_alteracao', 'usuario', 'observacao']
    readonly_fields = ['status_anterior', 'status_novo', 'data_alteracao', 'usuario']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(OrdemServico)
class OrdemServicoAdmin(admin.ModelAdmin):
    list_display = [
        'numero_os',
        'cliente',
        'tipo_equipamento',
        'status_colorido',
        'data_entrada',
        'prazo_estimado',
        'valor_total',
        'tecnico'
    ]
    list_filter = ['status', 'tipo_equipamento', 'data_entrada', 'tecnico']
    search_fields = [
        'numero_os', 
        'cliente__nome', 
        'marca', 
        'modelo',
        'numero_serie'
    ]
    date_hierarchy = 'data_entrada'
    list_per_page = 25
    inlines = [PecaUtilizadaInline, HistoricoOSInline]
    
    fieldsets = (
        ('Identificação', {
            'fields': ('numero_os', 'cliente', 'status')
        }),
        ('Equipamento', {
            'fields': ('tipo_equipamento', 'marca', 'modelo', 'numero_serie')
        }),
        ('Defeitos', {
            'fields': ('defeito_relatado', 'defeito_encontrado')
        }),
        ('Datas', {
            'fields': (
                'data_entrada',
                'data_avaliacao',
                'data_aprovacao', 
                'prazo_estimado',
                'data_conclusao',
                'data_entrega'
            )
        }),
        ('Valores', {
            'fields': ('valor_mao_obra', 'valor_pecas', 'desconto', 'valor_total')
        }),
        ('Garantia', {
            'fields': ('dias_garantia', 'data_fim_garantia')
        }),
        ('Responsáveis', {
            'fields': ('atendente', 'tecnico')
        }),
        ('Observações', {
            'fields': ('observacoes_internas', 'observacoes_cliente'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['numero_os', 'data_entrada', 'valor_total', 'data_fim_garantia']
    
    def status_colorido(self, obj):
        cores = {
            'recepcao': '#6c757d',
            'avaliacao': '#0dcaf0',
            'aguardando_aprovacao': '#ffc107',
            'aprovado': '#0d6efd',
            'em_reparo': '#fd7e14',
            'concluido': '#198754',
            'entregue': '#20c997',
            'cancelado': '#dc3545',
        }
        cor = cores.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            cor,
            obj.get_status_display()
        )
    status_colorido.short_description = 'Status'
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.atendente = request.user
        
        # Registrar mudança de status no histórico
        if change and 'status' in form.changed_data:
            status_anterior = OrdemServico.objects.get(pk=obj.pk).status
            super().save_model(request, obj, form, change)
            HistoricoOS.objects.create(
                ordem_servico=obj,
                status_anterior=status_anterior,
                status_novo=obj.status,
                usuario=request.user
            )
        else:
            super().save_model(request, obj, form, change)


@admin.register(PecaUtilizada)
class PecaUtilizadaAdmin(admin.ModelAdmin):
    list_display = ['ordem_servico', 'peca', 'quantidade', 'valor_unitario', 'valor_total']
    list_filter = ['ordem_servico__status']
    search_fields = ['ordem_servico__numero_os', 'peca__descricao']
    readonly_fields = ['valor_total']


@admin.register(HistoricoOS)
class HistoricoOSAdmin(admin.ModelAdmin):
    list_display = ['ordem_servico', 'status_anterior', 'status_novo', 'data_alteracao', 'usuario']
    list_filter = ['status_novo', 'data_alteracao', 'usuario']
    search_fields = ['ordem_servico__numero_os']
    date_hierarchy = 'data_alteracao'
    readonly_fields = ['ordem_servico', 'status_anterior', 'status_novo', 'data_alteracao', 'usuario']
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False