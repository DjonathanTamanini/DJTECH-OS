from django import forms
from .models import CategoriaFinanceira, Transacao, ContaBancaria, NotaFiscal, ItemNotaFiscal


class CategoriaFinanceiraForm(forms.ModelForm):
    class Meta:
        model = CategoriaFinanceira
        fields = ['nome', 'tipo', 'descricao', 'cor', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'cor': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class TransacaoForm(forms.ModelForm):
    class Meta:
        model = Transacao
        fields = [
            'tipo', 'categoria', 'descricao', 'valor', 'data_vencimento',
            'data_pagamento', 'status', 'forma_pagamento', 'ordem_servico',
            'fornecedor', 'observacoes'
        ]
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'descricao': forms.TextInput(attrs={'class': 'form-control'}),
            'valor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'data_vencimento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'data_pagamento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'forma_pagamento': forms.Select(attrs={'class': 'form-select'}),
            'ordem_servico': forms.Select(attrs={'class': 'form-select'}),
            'fornecedor': forms.Select(attrs={'class': 'form-select'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class ContaBancariaForm(forms.ModelForm):
    class Meta:
        model = ContaBancaria
        fields = ['nome', 'banco', 'agencia', 'conta', 'saldo_inicial', 'ativo', 'observacoes']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'banco': forms.TextInput(attrs={'class': 'form-control'}),
            'agencia': forms.TextInput(attrs={'class': 'form-control'}),
            'conta': forms.TextInput(attrs={'class': 'form-control'}),
            'saldo_inicial': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class NotaFiscalForm(forms.ModelForm):
    class Meta:
        model = NotaFiscal
        fields = [
            'numero_nota',
            'serie',
            'chave_acesso',
            'tipo',
            'fornecedor',
            'cliente',
            'data_emissao',
            'data_entrada',
            'valor_total',
            'valor_frete',
            'valor_desconto',
            'observacoes'
        ]
        widgets = {
            'numero_nota': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: 12345'
            }),
            'serie': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: 1'
            }),
            'chave_acesso': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '44 dígitos da NF-e (opcional)',
                'maxlength': '44'
            }),
            'tipo': forms.Select(attrs={
                'class': 'form-select'
            }),
            'fornecedor': forms.Select(attrs={
                'class': 'form-select'
            }),
            'cliente': forms.Select(attrs={
                'class': 'form-select'
            }),
            'data_emissao': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'data_entrada': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'valor_total': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'valor_frete': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'value': '0.00'
            }),
            'valor_desconto': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'value': '0.00'
            }),
            'observacoes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observações adicionais'
            })
        }
        labels = {
            'numero_nota': 'Número da Nota',
            'serie': 'Série',
            'chave_acesso': 'Chave de Acesso NF-e',
            'tipo': 'Tipo de Nota',
            'fornecedor': 'Fornecedor',
            'cliente': 'Cliente',
            'data_emissao': 'Data de Emissão',
            'data_entrada': 'Data de Entrada',
            'valor_total': 'Valor Total',
            'valor_frete': 'Valor do Frete',
            'valor_desconto': 'Valor do Desconto',
            'observacoes': 'Observações'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Define a data de entrada como hoje por padrão
        if not self.instance.pk:
            from datetime import date
            self.initial['data_entrada'] = date.today()
            self.initial['data_emissao'] = date.today()
        
        # Torna cliente e fornecedor opcionais baseado no tipo
        self.fields['fornecedor'].required = False
        self.fields['cliente'].required = False


class ItemNotaFiscalForm(forms.ModelForm):
    class Meta:
        model = ItemNotaFiscal
        fields = ['peca', 'quantidade', 'valor_unitario']
        widgets = {
            'peca': forms.Select(attrs={
                'class': 'form-select'
            }),
            'quantidade': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'value': '1'
            }),
            'valor_unitario': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            })
        }
        labels = {
            'peca': 'Peça',
            'quantidade': 'Quantidade',
            'valor_unitario': 'Valor Unitário'
        }


# FormSet para adicionar múltiplos itens à nota fiscal
from django.forms import inlineformset_factory

ItemNotaFiscalFormSet = inlineformset_factory(
    NotaFiscal,
    ItemNotaFiscal,
    form=ItemNotaFiscalForm,
    extra=1,  # Quantidade de formulários vazios extras
    can_delete=True,
    min_num=1,  # Mínimo de 1 item
    validate_min=True
)