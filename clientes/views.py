from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Cliente
from .forms import ClienteForm


@login_required
def cliente_lista(request):
    busca = request.GET.get('busca', '')
    
    if busca:
        clientes = Cliente.objects.filter(
            Q(nome__icontains=busca) |
            Q(cpf_cnpj__icontains=busca) |
            Q(telefone_principal__icontains=busca) |
            Q(email__icontains=busca)
        ).order_by('nome')
    else:
        clientes = Cliente.objects.all().order_by('nome')
    
    context = {
        'clientes': clientes,
        'busca': busca,
    }
    return render(request, 'clientes/cliente_lista.html', context)


@login_required
def cliente_detalhe(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    ordens_servico = cliente.ordens_servico.all().order_by('-data_entrada')[:10]
    
    context = {
        'cliente': cliente,
        'ordens_servico': ordens_servico,
    }
    return render(request, 'clientes/cliente_detalhe.html', context)


@login_required
def cliente_criar(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            cliente = form.save()
            messages.success(request, f'Cliente {cliente.nome} cadastrado com sucesso!')
            return redirect('cliente_detalhe', pk=cliente.pk)
    else:
        form = ClienteForm()
    
    context = {'form': form, 'titulo': 'Novo Cliente'}
    return render(request, 'clientes/cliente_form.html', context)


@login_required
def cliente_editar(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, f'Cliente {cliente.nome} atualizado com sucesso!')
            return redirect('cliente_detalhe', pk=cliente.pk)
    else:
        form = ClienteForm(instance=cliente)
    
    context = {'form': form, 'titulo': 'Editar Cliente', 'cliente': cliente}
    return render(request, 'clientes/cliente_form.html', context)


@login_required
def cliente_deletar(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    
    if request.method == 'POST':
        nome = cliente.nome
        cliente.delete()
        messages.success(request, f'Cliente {nome} excluído com sucesso!')
        return redirect('cliente_lista')
    
    context = {'cliente': cliente}
    return render(request, 'clientes/cliente_confirmar_exclusao.html', context)