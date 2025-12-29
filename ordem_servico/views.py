from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum
from django.utils import timezone
from django.http import JsonResponse
from datetime import datetime
from .models import OrdemServico, PecaUtilizada, HistoricoOS
from .forms import OrdemServicoForm, PecaUtilizadaFormSet
from estoque.models import MovimentacaoEstoque
from clientes.models import Cliente
from financeiro.models import Transacao, CategoriaFinanceira
from estoque.models import Peca






@login_required
def ordem_servico_lista(request):
    busca = request.GET.get('busca', '')
    status_filtro = request.GET.get('status', '')
    status_excluir = request.GET.get('status_excluir', '')
    atrasadas = request.GET.get('atrasadas', '')
    
    ordens = OrdemServico.objects.select_related('cliente', 'tecnico')
    
    if busca:
        ordens = ordens.filter(
            Q(numero_os__icontains=busca) |
            Q(cliente__nome__icontains=busca) |
            Q(marca__icontains=busca) |
            Q(modelo__icontains=busca)
        )
    
    if status_filtro:
        ordens = ordens.filter(status=status_filtro)
    
    # Filtro para excluir status (usado no dashboard "OS Abertas")
    if status_excluir:
        status_list = status_excluir.split(',')
        ordens = ordens.exclude(status__in=status_list)
    
    # Filtro de OS atrasadas
    if atrasadas:
        from datetime import date
        hoje = date.today()
        ordens = ordens.filter(
            prazo_estimado__lt=hoje,
            status__in=['avaliacao', 'aprovado', 'em_reparo']
        )
    
    ordens = ordens.order_by('-data_entrada')
    
    # Estatísticas rápidas
    total = ordens.count()
    aguardando_aprovacao = ordens.filter(status='aguardando_aprovacao').count()
    em_reparo = ordens.filter(status='em_reparo').count()
    
    context = {
        'ordens': ordens,
        'busca': busca,
        'status_filtro': status_filtro,
        'total': total,
        'aguardando_aprovacao': aguardando_aprovacao,
        'em_reparo': em_reparo,
        'STATUS_CHOICES': OrdemServico.STATUS_CHOICES,
    }
    return render(request, 'ordem_servico/ordem_servico_lista.html', context)


@login_required
def ordem_servico_detalhe(request, pk):
    ordem = get_object_or_404(OrdemServico, pk=pk)
    pecas_utilizadas = ordem.pecas_utilizadas.all()
    historico = ordem.historico.all().order_by('-data_alteracao')
    
    context = {
        'ordem': ordem,
        'pecas_utilizadas': pecas_utilizadas,
        'historico': historico,
    }
    return render(request, 'ordem_servico/ordem_servico_detalhe.html', context)


@login_required
def ordem_servico_criar(request):
    if request.method == 'POST':
        form = OrdemServicoForm(request.POST)
        formset = PecaUtilizadaFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            ordem = form.save(commit=False)
            ordem.atendente = request.user
            ordem.save()
            
            # Salvar peças utilizadas
            formset.instance = ordem
            pecas = formset.save()
            
            # Atualizar valor_pecas e registrar despesas
            total_pecas = 0
            for peca_utilizada in pecas:
                total_pecas += peca_utilizada.valor_total
                
                # Registrar movimentação de estoque
                MovimentacaoEstoque.objects.create(
                    peca=peca_utilizada.peca,
                    tipo='saida',
                    quantidade=peca_utilizada.quantidade,
                    usuario=request.user,
                    ordem_servico=ordem,
                    valor_unitario=peca_utilizada.valor_unitario
                )
                
                # Atualizar estoque
                peca_utilizada.peca.quantidade_estoque -= peca_utilizada.quantidade
                peca_utilizada.peca.save()
                
                # NOVO: Registrar despesa financeira automaticamente
                try:
                    categoria_pecas = CategoriaFinanceira.objects.get(
                        nome='Peças e Componentes',
                        tipo='despesa'
                    )
                except CategoriaFinanceira.DoesNotExist:
                    # Criar categoria se não existir
                    categoria_pecas = CategoriaFinanceira.objects.create(
                        nome='Peças e Componentes',
                        tipo='despesa',
                        descricao='Despesas com compra de peças para reparos',
                        cor='#e74c3c'
                    )
                
                Transacao.objects.create(
                    tipo='despesa',
                    categoria=categoria_pecas,
                    descricao=f'Peças utilizadas - OS {ordem.numero_os} - {peca_utilizada.peca.descricao}',
                    valor=peca_utilizada.peca.preco_custo * peca_utilizada.quantidade,
                    data_vencimento=ordem.data_entrada.date(),
                    data_pagamento=ordem.data_entrada.date(),
                    status='pago',
                    ordem_servico=ordem,
                    usuario=request.user,
                    observacoes=f'Peça: {peca_utilizada.peca.codigo_interno} - Qtd: {peca_utilizada.quantidade}'
                )
            
            ordem.valor_pecas = total_pecas
            ordem.save()
            
            messages.success(request, f'OS {ordem.numero_os} criada com sucesso!')
            return redirect('ordem_servico_detalhe', pk=ordem.pk)
    else:
        form = OrdemServicoForm()
        formset = PecaUtilizadaFormSet()
    
    context = {
        'form': form,
        'formset': formset,
        'titulo': 'Nova Ordem de Serviço'
    }
    return render(request, 'ordem_servico/ordem_servico_form.html', context)


@login_required
def ordem_servico_editar(request, pk):
    ordem = get_object_or_404(OrdemServico, pk=pk)
    status_anterior = ordem.status
    
    if request.method == 'POST':
        form = OrdemServicoForm(request.POST, instance=ordem)
        formset = PecaUtilizadaFormSet(request.POST, instance=ordem)
        
        if form.is_valid() and formset.is_valid():
            # Salvar ordem
            ordem = form.save(commit=False)
            
            # NOVO: Se mudou para status 'entregue', registrar receita
            if status_anterior != 'entregue' and ordem.status == 'entregue':
                try:
                    categoria_servicos = CategoriaFinanceira.objects.get(
                        nome='Serviços Prestados',
                        tipo='receita'
                    )
                except CategoriaFinanceira.DoesNotExist:
                    # Criar categoria se não existir
                    categoria_servicos = CategoriaFinanceira.objects.create(
                        nome='Serviços Prestados',
                        tipo='receita',
                        descricao='Receitas de serviços de assistência técnica',
                        cor='#27ae60'
                    )
                
                # Verificar se já existe transação para esta OS
                if not Transacao.objects.filter(
                    ordem_servico=ordem,
                    tipo='receita'
                ).exists():
                    Transacao.objects.create(
                        tipo='receita',
                        categoria=categoria_servicos,
                        descricao=f'Pagamento OS {ordem.numero_os} - {ordem.cliente.nome}',
                        valor=ordem.valor_total,
                        data_vencimento=ordem.data_entrega.date() if ordem.data_entrega else timezone.now().date(),
                        data_pagamento=ordem.data_entrega.date() if ordem.data_entrega else timezone.now().date(),
                        status='pago',
                        forma_pagamento='dinheiro',
                        ordem_servico=ordem,
                        usuario=request.user,
                        observacoes=f'Equipamento: {ordem.get_tipo_equipamento_display()} {ordem.marca} {ordem.modelo}'
                    )
                    messages.success(request, 'Receita registrada automaticamente no financeiro!')
            
            # Registrar histórico de mudança de status
            if status_anterior != ordem.status:
                HistoricoOS.objects.create(
                    ordem_servico=ordem,
                    status_anterior=status_anterior,
                    status_novo=ordem.status,
                    usuario=request.user
                )
                
                # Atualizar datas específicas
                if ordem.status == 'avaliacao' and not ordem.data_avaliacao:
                    ordem.data_avaliacao = timezone.now()
                elif ordem.status == 'aprovado' and not ordem.data_aprovacao:
                    ordem.data_aprovacao = timezone.now()
                elif ordem.status == 'concluido' and not ordem.data_conclusao:
                    ordem.data_conclusao = timezone.now()
                elif ordem.status == 'entregue' and not ordem.data_entrega:
                    ordem.data_entrega = timezone.now()
            
            ordem.save()
            
            # Processar peças (mantém a lógica original de estoque)
            pecas_antigas = set(PecaUtilizada.objects.filter(ordem_servico=ordem).values_list('id', flat=True))
            pecas_novas = formset.save()
            pecas_novas_ids = set([p.id for p in pecas_novas])
            pecas_removidas_ids = pecas_antigas - pecas_novas_ids
            
            # Restaurar estoque das peças removidas
            for peca_id in pecas_removidas_ids:
                try:
                    peca_util = PecaUtilizada.objects.get(id=peca_id)
                    peca_util.peca.quantidade_estoque += peca_util.quantidade
                    peca_util.peca.save()
                except PecaUtilizada.DoesNotExist:
                    pass
            
            # Atualizar valor_pecas
            total_pecas = sum([p.valor_total for p in ordem.pecas_utilizadas.all()])
            ordem.valor_pecas = total_pecas
            ordem.save()
            
            messages.success(request, f'OS {ordem.numero_os} atualizada com sucesso!')
            return redirect('ordem_servico_detalhe', pk=ordem.pk)
    else:
        form = OrdemServicoForm(instance=ordem)
        formset = PecaUtilizadaFormSet(instance=ordem)
    
    context = {
        'form': form,
        'formset': formset,
        'titulo': 'Editar Ordem de Serviço',
        'ordem': ordem
    }
    return render(request, 'ordem_servico/ordem_servico_form.html', context)


@login_required
def ordem_servico_imprimir(request, pk):
    ordem = get_object_or_404(OrdemServico, pk=pk)
    pecas_utilizadas = ordem.pecas_utilizadas.all()
    
    context = {
        'ordem': ordem,
        'pecas_utilizadas': pecas_utilizadas,
    }
    return render(request, 'ordem_servico/ordem_servico_imprimir.html', context)

from django.http import JsonResponse

@login_required
def buscar_clientes_ajax(request):
    """Busca clientes por nome ou CPF via AJAX"""
    termo = request.GET.get('termo', '')
    
    if len(termo) < 2:
        return JsonResponse({'clientes': []})
    
    clientes = Cliente.objects.filter(
        Q(nome__icontains=termo) |
        Q(cpf_cnpj__icontains=termo)
    ).values('id', 'nome', 'cpf_cnpj', 'telefone_principal')[:10]
    
    return JsonResponse({'clientes': list(clientes)})


@login_required
def buscar_clientes_ajax(request):
    """Busca clientes por nome ou CPF via AJAX"""
    termo = request.GET.get('termo', '')
    
    if len(termo) < 2:
        return JsonResponse({'clientes': []})
    
    clientes = Cliente.objects.filter(
        Q(nome__icontains=termo) |
        Q(cpf_cnpj__icontains=termo)
    ).values('id', 'nome', 'cpf_cnpj', 'telefone_principal')[:10]
    
    return JsonResponse({'clientes': list(clientes)})


def api_buscar_pecas_json(request):
    """
    View que retorna a lista de peças em formato JSON para o modal de busca.
    Filtra por nome, código interno ou part number.
    """
    termo = request.GET.get('q', '')
    
    # Filtra apenas peças ativas que contenham o termo pesquisado
    pecas = Peca.objects.filter(
        Q(nome__icontains=termo) | 
        Q(codigo_interno__icontains=termo) | 
        Q(part_number__icontains=termo),
        ativo=True
    ).order_by('nome')[:15] # Limita a 15 resultados por performance

    # Monta a lista de dicionários para o JSON
    dados = []
    for p in pecas:
        dados.append({
            'id': p.id,
            'codigo': p.codigo_interno,
            'nome': p.nome,
            'estoque': p.quantidade_estoque, # Usa a @property que criamos no models.py
            'preco': str(p.preco_venda)      # Decimal precisa virar string para JSON
        })
    
    return JsonResponse(dados, safe=False)