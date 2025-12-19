from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q, Count
from django.db.models.functions import TruncMonth
from datetime import datetime, date, timedelta
from .models import CategoriaFinanceira, Transacao, ContaBancaria
from .forms import CategoriaFinanceiraForm, TransacaoForm, ContaBancariaForm
from ordem_servico.models import OrdemServico


@login_required
def dashboard_financeiro(request):
    hoje = date.today()
    inicio_mes = hoje.replace(day=1)
    fim_mes = (inicio_mes + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    # Receitas e Despesas do mês
    receitas_mes = Transacao.objects.filter(
        tipo='receita',
        status='pago',
        data_pagamento__gte=inicio_mes,
        data_pagamento__lte=fim_mes
    ).aggregate(total=Sum('valor'))['total'] or 0
    
    despesas_mes = Transacao.objects.filter(
        tipo='despesa',
        status='pago',
        data_pagamento__gte=inicio_mes,
        data_pagamento__lte=fim_mes
    ).aggregate(total=Sum('valor'))['total'] or 0
    
    lucro_mes = receitas_mes - despesas_mes
    
    # Contas a receber e a pagar
    a_receber = Transacao.objects.filter(
        tipo='receita',
        status='pendente'
    ).aggregate(total=Sum('valor'))['total'] or 0
    
    a_pagar = Transacao.objects.filter(
        tipo='despesa',
        status='pendente'
    ).aggregate(total=Sum('valor'))['total'] or 0
    
    # Contas vencidas
    contas_vencidas = Transacao.objects.filter(
        status='pendente',
        data_vencimento__lt=hoje
    ).count()
    
    # Últimas transações
    ultimas_transacoes = Transacao.objects.select_related('categoria').order_by('-data_cadastro')[:10]
    
    # Gráfico de receitas x despesas (últimos 6 meses)
    seis_meses_atras = hoje - timedelta(days=180)
    dados_grafico = Transacao.objects.filter(
        status='pago',
        data_pagamento__gte=seis_meses_atras
    ).annotate(
        mes=TruncMonth('data_pagamento')
    ).values('mes', 'tipo').annotate(
        total=Sum('valor')
    ).order_by('mes')
    
    # Top categorias de despesa
    top_despesas = Transacao.objects.filter(
        tipo='despesa',
        status='pago',
        data_pagamento__gte=inicio_mes
    ).values('categoria__nome').annotate(
        total=Sum('valor')
    ).order_by('-total')[:5]
    
    context = {
        'receitas_mes': receitas_mes,
        'despesas_mes': despesas_mes,
        'lucro_mes': lucro_mes,
        'a_receber': a_receber,
        'a_pagar': a_pagar,
        'contas_vencidas': contas_vencidas,
        'ultimas_transacoes': ultimas_transacoes,
        'dados_grafico': dados_grafico,
        'top_despesas': top_despesas,
    }
    
    return render(request, 'financeiro/dashboard.html', context)

@login_required
def transacao_lista(request):
    tipo_filtro = request.GET.get('tipo', '')
    status_filtro = request.GET.get('status', '')
    categoria_filtro = request.GET.get('categoria', '')
    mes_filtro = request.GET.get('mes', '')
    
    transacoes = Transacao.objects.select_related('categoria', 'ordem_servico', 'fornecedor')
    
    if tipo_filtro:
        transacoes = transacoes.filter(tipo=tipo_filtro)
    
    if status_filtro:
        transacoes = transacoes.filter(status=status_filtro)
    
    if categoria_filtro:
        transacoes = transacoes.filter(categoria_id=categoria_filtro)
    
    if mes_filtro:
        ano, mes = mes_filtro.split('-')
        transacoes = transacoes.filter(
            data_vencimento__year=ano,
            data_vencimento__month=mes
        )
    
    transacoes = transacoes.order_by('-data_vencimento')
    
    # Totais
    total_receitas = transacoes.filter(tipo='receita', status='pago').aggregate(Sum('valor'))['valor__sum'] or 0
    total_despesas = transacoes.filter(tipo='despesa', status='pago').aggregate(Sum('valor'))['valor__sum'] or 0
    
    categorias = CategoriaFinanceira.objects.filter(ativo=True)
    
    context = {
        'transacoes': transacoes,
        'categorias': categorias,
        'total_receitas': total_receitas,
        'total_despesas': total_despesas,
        'saldo': total_receitas - total_despesas,
        'tipo_filtro': tipo_filtro,
        'status_filtro': status_filtro,
        'categoria_filtro': categoria_filtro,
    }
    
    return render(request, 'financeiro/transacao_lista.html', context)


@login_required
def transacao_criar(request):
    if request.method == 'POST':
        form = TransacaoForm(request.POST)
        if form.is_valid():
            transacao = form.save(commit=False)
            transacao.usuario = request.user
            transacao.save()
            messages.success(request, 'Transação cadastrada com sucesso!')
            return redirect('transacao_lista')
    else:
        form = TransacaoForm()
    
    context = {'form': form, 'titulo': 'Nova Transação'}
    return render(request, 'financeiro/transacao_form.html', context)


@login_required
def transacao_editar(request, pk):
    transacao = get_object_or_404(Transacao, pk=pk)
    
    if request.method == 'POST':
        form = TransacaoForm(request.POST, instance=transacao)
        if form.is_valid():
            form.save()
            messages.success(request, 'Transação atualizada com sucesso!')
            return redirect('transacao_lista')
    else:
        form = TransacaoForm(instance=transacao)
    
    context = {'form': form, 'titulo': 'Editar Transação', 'transacao': transacao}
    return render(request, 'financeiro/transacao_form.html', context)


@login_required
def transacao_deletar(request, pk):
    transacao = get_object_or_404(Transacao, pk=pk)
    
    if request.method == 'POST':
        transacao.delete()
        messages.success(request, 'Transação excluída com sucesso!')
        return redirect('transacao_lista')
    
    context = {'transacao': transacao}
    return render(request, 'financeiro/transacao_confirmar_exclusao.html', context)


@login_required
def transacao_pagar(request, pk):
    """Marca uma transação como paga"""
    transacao = get_object_or_404(Transacao, pk=pk)
    
    if request.method == 'POST':
        transacao.status = 'pago'
        transacao.data_pagamento = date.today()
        transacao.save()
        messages.success(request, f'Transação marcada como paga!')
        return redirect('transacao_lista')
    
    context = {'transacao': transacao}
    return render(request, 'financeiro/transacao_confirmar_pagamento.html', context)


@login_required
def relatorio_financeiro(request):
    """Relatório financeiro detalhado com filtros"""
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    
    if not data_inicio or not data_fim:
        # Padrão: mês atual
        hoje = date.today()
        data_inicio = hoje.replace(day=1)
        data_fim = (data_inicio + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    else:
        data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
        data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
    
    # Transações do período
    transacoes = Transacao.objects.filter(
        data_vencimento__gte=data_inicio,
        data_vencimento__lte=data_fim
    ).select_related('categoria')
    
    # Receitas por categoria
    receitas_categoria = transacoes.filter(
        tipo='receita',
        status='pago'
    ).values('categoria__nome').annotate(
        total=Sum('valor')
    ).order_by('-total')
    
    # Despesas por categoria
    despesas_categoria = transacoes.filter(
        tipo='despesa',
        status='pago'
    ).values('categoria__nome').annotate(
        total=Sum('valor')
    ).order_by('-total')
    
    # Totais
    total_receitas_pagas = transacoes.filter(tipo='receita', status='pago').aggregate(Sum('valor'))['valor__sum'] or 0
    total_despesas_pagas = transacoes.filter(tipo='despesa', status='pago').aggregate(Sum('valor'))['valor__sum'] or 0
    
    total_receitas_pendentes = transacoes.filter(tipo='receita', status='pendente').aggregate(Sum('valor'))['valor__sum'] or 0
    total_despesas_pendentes = transacoes.filter(tipo='despesa', status='pendente').aggregate(Sum('valor'))['valor__sum'] or 0
    
    # Lucro por OS
    os_com_lucro = OrdemServico.objects.filter(
        status='entregue',
        data_entrega__gte=data_inicio,
        data_entrega__lte=data_fim
    ).annotate(
        lucro=models.F('valor_total') - models.F('valor_pecas')
    ).order_by('-lucro')[:10]
    
    context = {
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'receitas_categoria': receitas_categoria,
        'despesas_categoria': despesas_categoria,
        'total_receitas_pagas': total_receitas_pagas,
        'total_despesas_pagas': total_despesas_pagas,
        'total_receitas_pendentes': total_receitas_pendentes,
        'total_despesas_pendentes': total_despesas_pendentes,
        'lucro_liquido': total_receitas_pagas - total_despesas_pagas,
        'os_com_lucro': os_com_lucro,
    }
    
    return render(request, 'financeiro/relatorio.html', context)


@login_required
def categoria_lista(request):
    categorias = CategoriaFinanceira.objects.all()
    return render(request, 'financeiro/categoria_lista.html', {'categorias': categorias})


@login_required
def categoria_criar(request):
    if request.method == 'POST':
        form = CategoriaFinanceiraForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Categoria cadastrada com sucesso!')
            return redirect('categoria_financeira_lista')
    else:
        form = CategoriaFinanceiraForm()
    
    context = {'form': form, 'titulo': 'Nova Categoria'}
    return render(request, 'financeiro/categoria_form.html', context)