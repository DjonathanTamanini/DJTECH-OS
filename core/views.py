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
    # Status finalizados conforme novo models.py: 'entregue', 'cancelado', 'pronto'
    total_os_abertas = OrdemServico.objects.exclude(
        status__in=['entregue', 'cancelado', 'pronto']
    ).count()
    
    # Correção: O status no novo model é 'aprovacao' (não 'aguardando_aprovacao')
    os_aguardando_aprovacao = OrdemServico.objects.filter(
        status='aprovacao'
    ).count()
    
    # Correção: O status no novo model é 'reparo' (não 'em_reparo')
    os_em_reparo = OrdemServico.objects.filter(
        status='reparo'
    ).count()
    
    # Correção do Erro Crítico: 'prazo_estimado' virou 'data_previsao'
    # Ajustado também a lista de status para os códigos novos
    os_atrasadas = OrdemServico.objects.filter(
        data_previsao__lt=hoje
    ).exclude(
        status__in=['pronto', 'entregue', 'cancelado']
    ).count()
    
    # --- CÁLCULO DE ESTOQUE BAIXO (SOLUÇÃO DINÂMICA) ---
    # Verifica se existem peças ativas com saldo abaixo do mínimo
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
        # Saldo = Entradas - Saídas
        saldo_atual=F('total_entrada') - F('total_saida')
    )

    # Nota: Certifique-se que o model Peca tem o campo 'quantidade_minima'
    # Se não tiver, altere para um número fixo, ex: saldo_atual__lte=5
    pecas_estoque_baixo_count = pecas_estoque.filter(
        ativo=True,
        saldo_atual__lte=F('quantidade_minima') 
    ).count()
    
    # --- OS DO MÊS ---
    os_mes = OrdemServico.objects.filter(
        data_entrada__gte=inicio_mes
    ).count()
    
    # --- ÚLTIMAS OS ---
    # Traz as 5 últimas, otimizando a consulta do cliente
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