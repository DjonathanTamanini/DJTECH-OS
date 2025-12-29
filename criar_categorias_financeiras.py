import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from financeiro.models import CategoriaFinanceira

# Categorias padrão
categorias = [
    {
        'nome': 'Serviços Prestados',
        'tipo': 'receita',
        'descricao': 'Receitas de serviços de assistência técnica',
        'cor': '#27ae60'
    },
    {
        'nome': 'Peças e Componentes',
        'tipo': 'despesa',
        'descricao': 'Despesas com peças utilizadas em reparos',
        'cor': '#e74c3c'
    },
    {
        'nome': 'Compra de Peças',
        'tipo': 'despesa',
        'descricao': 'Despesas com compra de peças para estoque',
        'cor': '#e67e22'
    },
]

print("Criando categorias financeiras padrão...")

for cat_data in categorias:
    categoria, criada = CategoriaFinanceira.objects.get_or_create(
        nome=cat_data['nome'],
        tipo=cat_data['tipo'],
        defaults={
            'descricao': cat_data['descricao'],
            'cor': cat_data['cor']
        }
    )
    
    if criada:
        print(f"✓ Categoria '{categoria.nome}' criada com sucesso!")
    else:
        print(f"→ Categoria '{categoria.nome}' já existe.")

print("\nConcluído! Categorias padrão estão prontas.")