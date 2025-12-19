from django import forms
from .models import CategoriaPeca, Peca, MovimentacaoEstoque


class CategoriaPecaForm(forms.ModelForm):
    class Meta:
        model = CategoriaPeca
        fields = ['nome', 'descricao']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome da categoria'
            }),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descrição da categoria'
            })
        }


class PecaForm(forms.ModelForm):
    class Meta:
        model = Peca
        fields = [
            'codigo_interno', 'descricao', 'categoria', 'quantidade_estoque',
            'estoque_minimo', 'localizacao', 'preco_custo', 'preco_venda',
            'fornecedor_principal', 'observacoes', 'ativo'
        ]
        widgets = {
            'codigo_interno': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Código único da peça'
            }),
            'descricao': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Descrição detalhada da peça'
            }),
            'categoria': forms.Select(attrs={
                'class': 'form-select'
            }),
            'quantidade_estoque': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'estoque_minimo': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            }),
            'localizacao': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Prateleira A1, Gaveta 3'
            }),
            'preco_custo': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'preco_venda': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'fornecedor_principal': forms.Select(attrs={
                'class': 'form-select'
            }),
            'observacoes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observações sobre a peça'
            }),
            'ativo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }


class MovimentacaoEstoqueForm(forms.ModelForm):
    class Meta:
        model = MovimentacaoEstoque
        fields = ['peca', 'tipo', 'quantidade', 'valor_unitario', 'fornecedor', 'observacoes']
        widgets = {
            'peca': forms.Select(attrs={
                'class': 'form-select'
            }),
            'tipo': forms.Select(attrs={
                'class': 'form-select'
            }),
            'quantidade': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            }),
            'valor_unitario': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'fornecedor': forms.Select(attrs={
                'class': 'form-select'
            }),
            'observacoes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observações sobre a movimentação'
            })
        }