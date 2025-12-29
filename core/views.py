from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q, F, IntegerField
from django.db.models.functions import Coalesce
from datetime import datetime
from ordem_servico.models import OrdemServico
from estoque.models import Peca

@login_required
def dashboard(request):
    """
    View principal do sistema (Dashboard).
    Calcula estatísticas de OS e monitora o estoque de forma dinâmica.
    """
    hoje = datetime.now().date()
    inicio_mes = hoje.replace(day=1)
    
    # --- ESTATÍSTICAS GERAIS DE OS ---
    total_os_abertas = OrdemServico.objects.exclude(
        status__in=['entregue', 'cancelado']
    ).count()
    
    os_aguardando_aprovacao = OrdemServico.objects.filter(
        status='aguardando_aprovacao'
    ).count()
    
    os_em_reparo = OrdemServico.objects.filter(
        status='em_reparo'
    ).count()
    
    os_atrasadas = OrdemServico.objects.filter(
        prazo_estimado__lt=hoje,
        status__in=['avaliacao', 'aprovado', 'em_reparo']
    ).count()
    
    # --- CÁLCULO DE ESTOQUE BAIXO (SOLUÇÃO DINÂMICA) ---
    # Como não usamos campo fixo de quantidade, calculamos Saldo = Entradas - Saídas
    # Coalesce é usado para transformar valores nulos em 0.
    pecas_estoque = Peca.objects.annotate(
        total_entrada=Coalesce(
            Sum('movimentacoes__quantidade', filter=Q(movimentacoes__tipo='entrada')),
            0,
            output_field=IntegerField()
        ),
        total_saida=Coalesce(
            Sum('movimentacoes__quantidade', filter=Q(movimentacoes__tipo='saida')),
            0,
            output_field=IntegerField()
        )
    ).annotate(
        # Criamos o campo virtual 'saldo_atual' para comparar com o mínimo
        saldo_atual=F('total_entrada') - F('total_saida')
    )

    # Filtramos peças ativas que atingiram ou estão abaixo da quantidade mínima
    pecas_estoque_baixo_count = pecas_estoque.filter(
        ativo=True,
        saldo_atual__lte=F('quantidade_minima')
    ).count()
    
    # --- OS DO MÊS ---
    os_mes = OrdemServico.objects.filter(
        data_entrada__gte=inicio_mes
    ).count()
    
    # --- ÚLTIMAS OS (CORREÇÃO DO FIELD ERROR) ---
    # Removido 'equipamento' do select_related pois ele não é uma ForeignKey.
    # Mantemos 'cliente' para otimizar a performance da lista.
    ultimas_os = OrdemServico.objects.select_related(
        'cliente'
    ).all().order_by('-data_entrada')[:5]
    
    context = {
        'total_os_abertas': total_os_abertas,
        'os_aguardando_aprovacao': os_aguardando_aprovacao,
        'os_em_reparo': os_em_reparo,
        'os_atrasadas': os_atrasadas,
        'pecas_estoque_baixo': pecas_estoque_baixo_count,
        'os_mes': os_mes,
        'ultimas_os': ultimas_os,
    }
    
    return render(request, 'core/dashboard.html', context)