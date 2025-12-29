from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, F
from .models import CategoriaPeca, Peca, MovimentacaoEstoque
from .forms import CategoriaPecaForm, PecaForm, MovimentacaoEstoqueForm
from financeiro.models import Transacao, CategoriaFinanceira


@login_required
def peca_lista(request):
    busca = request.GET.get('busca', '')
    categoria_id = request.GET.get('categoria', '')
    estoque_baixo = request.GET.get('estoque_baixo', '')
    
    pecas = Peca.objects.select_related('categoria', 'fornecedor_principal')
    
    if busca:
        pecas = pecas.filter(
            Q(codigo_interno__icontains=busca) |
            Q(descricao__icontains=busca)
        )
    
    if categoria_id:
        pecas = pecas.filter(categoria_id=categoria_id)
    
    if estoque_baixo:
        pecas = pecas.filter(quantidade_estoque__lte=F('estoque_minimo'))
    
    pecas = pecas.order_by('descricao')
    categorias = CategoriaPeca.objects.all().order_by('nome')
    
    context = {
        'pecas': pecas,
        'categorias': categorias,
        'busca': busca,
        'categoria_selecionada': categoria_id,
        'estoque_baixo': estoque_baixo,
    }
    return render(request, 'estoque/peca_lista.html', context)


@login_required
def peca_detalhe(request, pk):
    peca = get_object_or_404(Peca, pk=pk)
    movimentacoes = peca.movimentacoes.all().order_by('-data_movimentacao')[:20]
    
    context = {
        'peca': peca,
        'movimentacoes': movimentacoes,
    }
    return render(request, 'estoque/peca_detalhe.html', context)


@login_required
def peca_criar(request):
    if request.method == 'POST':
        form = PecaForm(request.POST)
        if form.is_valid():
            peca = form.save()
            messages.success(request, f'Peça {peca.codigo_interno} cadastrada com sucesso!')
            return redirect('peca_detalhe', pk=peca.pk)
    else:
        form = PecaForm()
    
    context = {'form': form, 'titulo': 'Nova Peça'}
    return render(request, 'estoque/peca_form.html', context)


@login_required
def peca_editar(request, pk):
    peca = get_object_or_404(Peca, pk=pk)
    
    if request.method == 'POST':
        form = PecaForm(request.POST, instance=peca)
        if form.is_valid():
            form.save()
            messages.success(request, f'Peça {peca.codigo_interno} atualizada com sucesso!')
            return redirect('peca_detalhe', pk=peca.pk)
    else:
        form = PecaForm(instance=peca)
    
    context = {'form': form, 'titulo': 'Editar Peça', 'peca': peca}
    return render(request, 'estoque/peca_form.html', context)


@login_required
def peca_deletar(request, pk):
    peca = get_object_or_404(Peca, pk=pk)
    
    if request.method == 'POST':
        codigo = peca.codigo_interno
        peca.delete()
        messages.success(request, f'Peça {codigo} excluída com sucesso!')
        return redirect('peca_lista')
    
    context = {'peca': peca}
    return render(request, 'estoque/peca_confirmar_exclusao.html', context)


@login_required
def movimentacao_criar(request):
    if request.method == 'POST':
        form = MovimentacaoEstoqueForm(request.POST)
        if form.is_valid():
            movimentacao = form.save(commit=False)
            movimentacao.usuario = request.user
            movimentacao.save()
            
            # Atualizar estoque
            peca = movimentacao.peca
            if movimentacao.tipo == 'entrada':
                peca.quantidade_estoque += movimentacao.quantidade
                
                # NOVO: Registrar despesa financeira na entrada de peças
                if movimentacao.valor_unitario and movimentacao.valor_unitario > 0:
                    try:
                        categoria_compra_pecas = CategoriaFinanceira.objects.get(
                            nome='Compra de Peças',
                            tipo='despesa'
                        )
                    except CategoriaFinanceira.DoesNotExist:
                        # Criar categoria se não existir
                        categoria_compra_pecas = CategoriaFinanceira.objects.create(
                            nome='Compra de Peças',
                            tipo='despesa',
                            descricao='Despesas com compra de peças para estoque',
                            cor='#e67e22'
                        )
                    
                    valor_total = movimentacao.quantidade * movimentacao.valor_unitario
                    
                    Transacao.objects.create(
                        tipo='despesa',
                        categoria=categoria_compra_pecas,
                        descricao=f'Compra de estoque - {peca.descricao}',
                        valor=valor_total,
                        data_vencimento=timezone.now().date(),
                        data_pagamento=timezone.now().date(),
                        status='pago',
                        fornecedor=movimentacao.fornecedor,
                        usuario=request.user,
                        observacoes=f'Peça: {peca.codigo_interno} - Qtd: {movimentacao.quantidade} - Valor unitário: R$ {movimentacao.valor_unitario}'
                    )
                    messages.success(request, 'Movimentação registrada e despesa lançada no financeiro!')
                else:
                    messages.success(request, 'Movimentação registrada com sucesso!')
                    
            elif movimentacao.tipo == 'saida':
                peca.quantidade_estoque -= movimentacao.quantidade
                messages.success(request, 'Movimentação registrada com sucesso!')
            else:  # ajuste
                peca.quantidade_estoque = movimentacao.quantidade
                messages.success(request, 'Movimentação registrada com sucesso!')
            
            peca.save()
            
            return redirect('peca_detalhe', pk=peca.pk)
    else:
        form = MovimentacaoEstoqueForm()
    
    context = {'form': form, 'titulo': 'Nova Movimentação'}
    return render(request, 'estoque/movimentacao_form.html', context)


@login_required
def categoria_lista(request):
    categorias = CategoriaPeca.objects.all().order_by('nome')
    context = {'categorias': categorias}
    return render(request, 'estoque/categoria_lista.html', context)


@login_required
def categoria_criar(request):
    if request.method == 'POST':
        form = CategoriaPecaForm(request.POST)
        if form.is_valid():
            categoria = form.save()
            messages.success(request, f'Categoria {categoria.nome} cadastrada com sucesso!')
            return redirect('categoria_lista')
    else:
        form = CategoriaPecaForm()
    
    context = {'form': form, 'titulo': 'Nova Categoria'}
    return render(request, 'estoque/categoria_form.html', context)


@login_required
def categoria_editar(request, pk):
    categoria = get_object_or_404(CategoriaPeca, pk=pk)
    
    if request.method == 'POST':
        form = CategoriaPecaForm(request.POST, instance=categoria)
        if form.is_valid():
            form.save()
            messages.success(request, f'Categoria {categoria.nome} atualizada com sucesso!')
            return redirect('categoria_lista')
    else:
        form = CategoriaPecaForm(instance=categoria)
    
    context = {'form': form, 'titulo': 'Editar Categoria', 'categoria': categoria}
    return render(request, 'estoque/categoria_form.html', context)