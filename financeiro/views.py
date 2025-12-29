from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q, Count
from django.db.models.functions import TruncMonth
from django.db import transaction
from datetime import datetime, date, timedelta
from .models import CategoriaFinanceira, Transacao, ContaBancaria, NotaFiscal, ItemNotaFiscal
from .forms import (CategoriaFinanceiraForm, TransacaoForm, ContaBancariaForm, 
                    NotaFiscalForm, ItemNotaFiscalFormSet)
from ordem_servico.models import OrdemServico
from estoque.models import MovimentacaoEstoque


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


# ==================== NOTAS FISCAIS ====================

@login_required
def nota_fiscal_lista(request):
    """Lista todas as notas fiscais"""
    notas = NotaFiscal.objects.select_related('fornecedor', 'cliente', 'usuario').order_by('-data_entrada')
    
    # Filtros
    tipo_filtro = request.GET.get('tipo', '')
    if tipo_filtro:
        notas = notas.filter(tipo=tipo_filtro)
    
    context = {
        'notas': notas,
        'tipo_filtro': tipo_filtro,
    }
    return render(request, 'financeiro/nota_fiscal_lista.html', context)


@login_required
@transaction.atomic
def nota_fiscal_criar(request):
    """Cria uma nova nota fiscal com seus itens"""
    if request.method == 'POST':
        form = NotaFiscalForm(request.POST)
        formset = ItemNotaFiscalFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            # Salva a nota fiscal
            nota = form.save(commit=False)
            nota.usuario = request.user
            nota.save()
            
            # Salva os itens
            formset.instance = nota
            formset.save()
            
            messages.success(request, f'Nota Fiscal {nota.numero_nota} cadastrada com sucesso!')
            return redirect('nota_fiscal_detalhe', pk=nota.pk)
    else:
        form = NotaFiscalForm()
        formset = ItemNotaFiscalFormSet()
    
    context = {
        'form': form,
        'formset': formset,
        'titulo': 'Nova Nota Fiscal'
    }
    return render(request, 'financeiro/nota_fiscal_form.html', context)


@login_required
def nota_fiscal_detalhe(request, pk):
    """Exibe detalhes de uma nota fiscal"""
    nota = get_object_or_404(NotaFiscal.objects.select_related('fornecedor', 'cliente', 'usuario'), pk=pk)
    itens = nota.itens.select_related('peca').all()
    
    context = {
        'nota': nota,
        'itens': itens,
    }
    return render(request, 'financeiro/nota_fiscal_detalhe.html', context)


@login_required
@transaction.atomic
def nota_fiscal_integrar_estoque(request, pk):
    """Integra a nota fiscal ao estoque (dá entrada nas peças)"""
    nota = get_object_or_404(NotaFiscal, pk=pk)
    
    if nota.integrada_estoque:
        messages.warning(request, 'Esta nota já foi integrada ao estoque!')
        return redirect('nota_fiscal_detalhe', pk=pk)
    
    if nota.tipo != 'entrada':
        messages.error(request, 'Apenas notas de ENTRADA podem ser integradas ao estoque!')
        return redirect('nota_fiscal_detalhe', pk=pk)
    
    if request.method == 'POST':
        try:
            # Para cada item da nota, cria uma movimentação de entrada no estoque
            itens_processados = 0
            for item in nota.itens.all():
                MovimentacaoEstoque.objects.create(
                    peca=item.peca,
                    tipo='entrada',
                    quantidade=item.quantidade,
                    valor_unitario=item.valor_unitario,
                    nota_fiscal=nota,
                    fornecedor=nota.fornecedor,
                    usuario=request.user,
                    observacoes=f'Entrada via NF {nota.numero_nota}'
                )
                itens_processados += 1
            
            # Marca a nota como integrada ao estoque
            nota.integrada_estoque = True
            nota.save()
            
            messages.success(
                request,
                f'Nota Fiscal integrada ao estoque com sucesso! {itens_processados} item(ns) processado(s).'
            )
        except Exception as e:
            messages.error(request, f'Erro ao integrar nota ao estoque: {str(e)}')
        
        return redirect('nota_fiscal_detalhe', pk=pk)
    
    context = {'nota': nota}
    return render(request, 'financeiro/nota_fiscal_confirmar_integracao.html', context)


@login_required
@transaction.atomic
def nota_fiscal_integrar_financeiro(request, pk):
    """Integra a nota fiscal ao financeiro (cria transação de despesa)"""
    nota = get_object_or_404(NotaFiscal, pk=pk)
    
    if nota.integrada_financeiro:
        messages.warning(request, 'Esta nota já foi integrada ao financeiro!')
        return redirect('nota_fiscal_detalhe', pk=pk)
    
    if request.method == 'POST':
        try:
            # Busca ou cria a categoria "Compra de Peças"
            categoria, created = CategoriaFinanceira.objects.get_or_create(
                nome='Compra de Peças',
                tipo='despesa',
                defaults={
                    'descricao': 'Despesas com compra de peças para estoque',
                    'cor': '#e67e22'
                }
            )
            
            # Cria a transação financeira
            Transacao.objects.create(
                tipo='despesa',
                categoria=categoria,
                descricao=f'NF {nota.numero_nota} - {nota.fornecedor}',
                valor=nota.valor_liquido,
                data_vencimento=nota.data_emissao,
                data_pagamento=nota.data_entrada,
                status='pago',
                fornecedor=nota.fornecedor,
                usuario=request.user,
                observacoes=f'Nota Fiscal {nota.numero_nota} | Série: {nota.serie}'
            )
            
            # Marca a nota como integrada ao financeiro
            nota.integrada_financeiro = True
            nota.save()
            
            messages.success(request, 'Nota Fiscal integrada ao financeiro com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao integrar nota ao financeiro: {str(e)}')
        
        return redirect('nota_fiscal_detalhe', pk=pk)
    
    context = {'nota': nota}
    return render(request, 'financeiro/nota_fiscal_confirmar_integracao_financeiro.html', context)


@login_required
@transaction.atomic
def nota_fiscal_integrar_completo(request, pk):
    """Integra a nota tanto no estoque quanto no financeiro"""
    nota = get_object_or_404(NotaFiscal, pk=pk)
    
    if nota.integrada_estoque and nota.integrada_financeiro:
        messages.warning(request, 'Esta nota já foi totalmente integrada!')
        return redirect('nota_fiscal_detalhe', pk=pk)
    
    if request.method == 'POST':
        try:
            # Integra ao estoque (se ainda não foi)
            if not nota.integrada_estoque and nota.tipo == 'entrada':
                itens_processados = 0
                for item in nota.itens.all():
                    MovimentacaoEstoque.objects.create(
                        peca=item.peca,
                        tipo='entrada',
                        quantidade=item.quantidade,
                        valor_unitario=item.valor_unitario,
                        nota_fiscal=nota,
                        fornecedor=nota.fornecedor,
                        usuario=request.user,
                        observacoes=f'Entrada via NF {nota.numero_nota}'
                    )
                    itens_processados += 1
                nota.integrada_estoque = True
            
            # Integra ao financeiro (se ainda não foi)
            if not nota.integrada_financeiro:
                categoria, created = CategoriaFinanceira.objects.get_or_create(
                    nome='Compra de Peças',
                    tipo='despesa',
                    defaults={
                        'descricao': 'Despesas com compra de peças para estoque',
                        'cor': '#e67e22'
                    }
                )
                
                Transacao.objects.create(
                    tipo='despesa',
                    categoria=categoria,
                    descricao=f'NF {nota.numero_nota} - {nota.fornecedor}',
                    valor=nota.valor_liquido,
                    data_vencimento=nota.data_emissao,
                    data_pagamento=nota.data_entrada,
                    status='pago',
                    fornecedor=nota.fornecedor,
                    usuario=request.user,
                    observacoes=f'Nota Fiscal {nota.numero_nota} | Série: {nota.serie}'
                )
                nota.integrada_financeiro = True
            
            nota.save()
            
            messages.success(request, 'Nota Fiscal integrada completamente (Estoque + Financeiro)!')
        except Exception as e:
            messages.error(request, f'Erro ao integrar nota: {str(e)}')
        
        return redirect('nota_fiscal_detalhe', pk=pk)
    
    context = {'nota': nota}
    return render(request, 'financeiro/nota_fiscal_confirmar_integracao_completa.html', context)