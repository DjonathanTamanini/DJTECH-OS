from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Fornecedor
from .forms import FornecedorForm


@login_required
def fornecedor_lista(request):
    busca = request.GET.get('busca', '')
    
    if busca:
        fornecedores = Fornecedor.objects.filter(
            Q(razao_social__icontains=busca) |
            Q(nome_fantasia__icontains=busca) |
            Q(cnpj__icontains=busca) |
            Q(telefone__icontains=busca)
        ).order_by('razao_social')
    else:
        fornecedores = Fornecedor.objects.all().order_by('razao_social')
    
    context = {
        'fornecedores': fornecedores,
        'busca': busca,
    }
    return render(request, 'fornecedores/fornecedor_lista.html', context)


@login_required
def fornecedor_detalhe(request, pk):
    fornecedor = get_object_or_404(Fornecedor, pk=pk)
    pecas = fornecedor.pecas_fornecidas.all().order_by('descricao')
    
    context = {
        'fornecedor': fornecedor,
        'pecas': pecas,
    }
    return render(request, 'fornecedores/fornecedor_detalhe.html', context)


@login_required
def fornecedor_criar(request):
    if request.method == 'POST':
        form = FornecedorForm(request.POST)
        if form.is_valid():
            fornecedor = form.save()
            messages.success(request, f'Fornecedor {fornecedor.razao_social} cadastrado com sucesso!')
            return redirect('fornecedor_detalhe', pk=fornecedor.pk)
    else:
        form = FornecedorForm()
    
    context = {'form': form, 'titulo': 'Novo Fornecedor'}
    return render(request, 'fornecedores/fornecedor_form.html', context)


@login_required
def fornecedor_editar(request, pk):
    fornecedor = get_object_or_404(Fornecedor, pk=pk)
    
    if request.method == 'POST':
        form = FornecedorForm(request.POST, instance=fornecedor)
        if form.is_valid():
            form.save()
            messages.success(request, f'Fornecedor {fornecedor.razao_social} atualizado com sucesso!')
            return redirect('fornecedor_detalhe', pk=fornecedor.pk)
    else:
        form = FornecedorForm(instance=fornecedor)
    
    context = {'form': form, 'titulo': 'Editar Fornecedor', 'fornecedor': fornecedor}
    return render(request, 'fornecedores/fornecedor_form.html', context)


@login_required
def fornecedor_deletar(request, pk):
    fornecedor = get_object_or_404(Fornecedor, pk=pk)
    
    if request.method == 'POST':
        razao_social = fornecedor.razao_social
        fornecedor.delete()
        messages.success(request, f'Fornecedor {razao_social} excluído com sucesso!')
        return redirect('fornecedor_lista')
    
    context = {'fornecedor': fornecedor}
    return render(request, 'fornecedores/fornecedor_confirmar_exclusao.html', context)