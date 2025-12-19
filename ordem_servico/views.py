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
            
            # Atualizar valor_pecas
            total_pecas = sum([p.valor_total for p in pecas])
            ordem.valor_pecas = total_pecas
            ordem.save()
            
            # Registrar movimentação de estoque para cada peça
            for peca_utilizada in pecas:
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
            
            # Se mudou o status, registrar no histórico
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
            
            # Processar peças
            # Primeiro, restaurar estoque das peças removidas
            pecas_antigas = set(PecaUtilizada.objects.filter(ordem_servico=ordem).values_list('id', flat=True))
            
            # Salvar novas peças
            pecas_novas = formset.save()
            pecas_novas_ids = set([p.id for p in pecas_novas])
            
            # Identificar peças removidas
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