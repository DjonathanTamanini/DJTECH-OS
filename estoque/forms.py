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
            'part_number',
            'nome',
            'descricao',
            'categoria',
            'quantidade_minima',
            'localizacao',
            'margem_lucro',
            'fornecedor_principal',
            'observacoes',
            'ativo'
        ]
        widgets = {
            'part_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: PN-12345, REF-ABC'
            }),
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome da peça'
            }),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Descrição detalhada da peça, especificações técnicas, compatibilidade, etc.'
            }),
            'categoria': forms.Select(attrs={
                'class': 'form-select'
            }),
            'quantidade_minima': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'value': '1'
            }),
            'localizacao': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Prateleira A1, Gaveta 3'
            }),
            'margem_lucro': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'placeholder': 'Ex: 30.00 (para 30%)'
            }),
            'fornecedor_principal': forms.Select(attrs={
                'class': 'form-select'
            }),
            'observacoes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observações adicionais sobre a peça'
            }),
            'ativo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'part_number': 'Part Number (Código do Fabricante)',
            'nome': 'Nome da Peça',
            'descricao': 'Descrição Detalhada',
            'categoria': 'Categoria',
            'quantidade_minima': 'Quantidade Mínima (Alerta de Compra)',
            'localizacao': 'Localização no Estoque',
            'margem_lucro': 'Margem de Lucro (%)',
            'fornecedor_principal': 'Fornecedor Principal',
            'observacoes': 'Observações',
            'ativo': 'Ativo'
        }
        help_texts = {
            'part_number': 'Código do fabricante/fornecedor (opcional)',
            'quantidade_minima': 'Quantidade que gera alerta de estoque baixo',
            'margem_lucro': 'O preço de venda será calculado automaticamente baseado no último preço de compra + esta margem',
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
        labels = {
            'peca': 'Peça',
            'tipo': 'Tipo de Movimentação',
            'quantidade': 'Quantidade',
            'valor_unitario': 'Valor Unitário',
            'fornecedor': 'Fornecedor (opcional)',
            'observacoes': 'Observações'
        }
        help_texts = {
            'valor_unitario': 'Para ENTRADA, este valor atualizará o último preço de compra',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Torna o fornecedor não obrigatório
        self.fields['fornecedor'].required = False