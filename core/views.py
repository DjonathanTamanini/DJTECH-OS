from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, F
from datetime import datetime, timedelta
from ordem_servico.models import OrdemServico
from estoque.models import Peca
from clientes.models import Cliente


@login_required
def dashboard(request):
    hoje = datetime.now().date()
    inicio_mes = hoje.replace(day=1)
    
    # Estatísticas gerais
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
    
    # Peças com estoque baixo
    pecas_estoque_baixo = Peca.objects.filter(
        quantidade_estoque__lte=F('estoque_minimo'),
        ativo=True
    ).count()
    
    # OS do mês
    os_mes = OrdemServico.objects.filter(
        data_entrada__gte=inicio_mes
    ).count()
    
    # Últimas OS
    ultimas_os = OrdemServico.objects.select_related('cliente').order_by('-data_entrada')[:5]
    
    context = {
        'total_os_abertas': total_os_abertas,
        'os_aguardando_aprovacao': os_aguardando_aprovacao,
        'os_em_reparo': os_em_reparo,
        'os_atrasadas': os_atrasadas,
        'pecas_estoque_baixo': pecas_estoque_baixo,
        'os_mes': os_mes,
        'ultimas_os': ultimas_os,
    }
    
    return render(request, 'core/dashboard.html', context)