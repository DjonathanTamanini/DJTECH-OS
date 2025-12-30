from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from django.http import JsonResponse

from .models import OrdemServico, PecaUtilizadaOS
from .forms import OrdemServicoForm, PecaUtilizadaFormSet
from estoque.models import Peca, MovimentacaoEstoque

@login_required
def ordem_servico_lista(request):
    busca = request.GET.get('busca', '')
    status_filtro = request.GET.get('status', '')
    
    ordens = OrdemServico.objects.select_related('cliente', 'tecnico').all().order_by('-data_entrada')
    
    if busca:
        ordens = ordens.filter(
            Q(id__icontains=busca) |
            Q(cliente__nome__icontains=busca) |
            Q(marca__icontains=busca) |
            Q(modelo__icontains=busca)
        )
    
    if status_filtro:
        ordens = ordens.filter(status=status_filtro)
    
    context = {
        'ordens': ordens,
        'STATUS_CHOICES': OrdemServico.STATUS_CHOICES,
        'total': OrdemServico.objects.count(),
        'aguardando_aprovacao': OrdemServico.objects.filter(status='aprovacao').count(),
        'em_reparo': OrdemServico.objects.filter(status='reparo').count(),
        'busca': busca,
        'status_filtro': status_filtro
    }
    return render(request, 'ordem_servico/ordem_servico_lista.html', context)

@login_required
def ordem_servico_criar(request):
    if request.method == 'POST':
        form = OrdemServicoForm(request.POST)
        formset = PecaUtilizadaFormSet(request.POST, prefix='pecas')
        
        if form.is_valid() and formset.is_valid():
            os = form.save(commit=False)
            os.atendente = request.user
            os.save()
            
            formset.instance = os
            formset.save()
            
            # Baixa no estoque
            for form_peca in formset:
                if form_peca.cleaned_data and not form_peca.cleaned_data.get('DELETE', False):
                    peca = form_peca.cleaned_data['peca']
                    qtd = form_peca.cleaned_data['quantidade']
                    
                    MovimentacaoEstoque.objects.create(
                        peca=peca,
                        tipo='saida',
                        quantidade=qtd,
                        valor_unitario=peca.preco_venda,
                        ordem_servico=os,
                        usuario=request.user,
                        observacoes=f"Saída automática via OS {os.id}"
                    )

            messages.success(request, 'Ordem de Serviço criada com sucesso!')
            return redirect('ordem_servico_detalhe', pk=os.pk)
    else:
        form = OrdemServicoForm()
        formset = PecaUtilizadaFormSet(prefix='pecas')
    
    context = {
        'form': form, 
        'pecas_formset': formset,
        'titulo': 'Nova Ordem de Serviço'
    }
    return render(request, 'ordem_servico/ordem_servico_form.html', context)

@login_required
def ordem_servico_editar(request, pk):
    os = get_object_or_404(OrdemServico, pk=pk)
    
    if request.method == 'POST':
        form = OrdemServicoForm(request.POST, instance=os)
        formset = PecaUtilizadaFormSet(request.POST, instance=os, prefix='pecas')
        
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, 'Ordem de Serviço atualizada com sucesso!')
            return redirect('ordem_servico_detalhe', pk=os.pk)
    else:
        form = OrdemServicoForm(instance=os)
        formset = PecaUtilizadaFormSet(instance=os, prefix='pecas')
    
    context = {
        'form': form, 
        'pecas_formset': formset,
        'ordem': os,
        'titulo': f'Editar OS {os.id}'
    }
    return render(request, 'ordem_servico/ordem_servico_form.html', context)

@login_required
def ordem_servico_detalhe(request, pk):
    os = get_object_or_404(OrdemServico, pk=pk)
    pecas = os.pecas.select_related('peca').all()
    
    context = {
        'ordem': os,
        'pecas_utilizadas': pecas,
        'historico': os.historico.all().order_by('-data_alteracao')
    }
    return render(request, 'ordem_servico/ordem_servico_detalhe.html', context)

@login_required
def ordem_servico_imprimir(request, pk):
    os = get_object_or_404(OrdemServico, pk=pk)
    pecas = os.pecas.select_related('peca').all()
    context = {'ordem': os, 'pecas_utilizadas': pecas}
    return render(request, 'ordem_servico/ordem_servico_imprimir.html', context)

@login_required
def buscar_clientes_ajax(request):
    termo = request.GET.get('termo', '')
    if len(termo) < 2: return JsonResponse({'clientes': []})
    from clientes.models import Cliente
    clientes = Cliente.objects.filter(Q(nome__icontains=termo) | Q(cpf_cnpj__icontains=termo)).values('id', 'nome', 'cpf_cnpj')[:10]
    return JsonResponse({'clientes': list(clientes)})

@login_required
def api_buscar_pecas_json(request):
    termo = request.GET.get('q', '')
    if not termo: return JsonResponse([], safe=False)
    pecas = Peca.objects.filter(Q(nome__icontains=termo)|Q(codigo_interno__icontains=termo), ativo=True)[:20]
    data = [{'id': p.id, 'codigo': p.codigo_interno, 'nome': p.nome, 'estoque': getattr(p, 'quantidade_estoque', 0), 'preco': str(p.preco_venda)} for p in pecas]
    return JsonResponse(data, safe=False)