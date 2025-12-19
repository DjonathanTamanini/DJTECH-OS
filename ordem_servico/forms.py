from django import forms
from django.forms import inlineformset_factory
from .models import OrdemServico, PecaUtilizada
from clientes.models import Cliente
from estoque.models import Peca


class ClienteSelectWidget(forms.Select):
    """Widget customizado para buscar clientes por nome ou CPF"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attrs.update({
            'class': 'form-select cliente-select',
            'data-placeholder': 'Buscar cliente por nome ou CPF...'
        })


class OrdemServicoForm(forms.ModelForm):
    class Meta:
        model = OrdemServico
        fields = [
            'cliente', 'tipo_equipamento', 'marca', 'modelo', 'numero_serie',
            'defeito_relatado', 'defeito_encontrado', 'status', 'prazo_estimado',
            'valor_mao_obra', 'valor_pecas', 'desconto', 'dias_garantia',
            'tecnico', 'observacoes_internas', 'observacoes_cliente'
        ]
        widgets = {
            'cliente': ClienteSelectWidget(attrs={
                'class': 'form-select',
                'required': True
            }),
            'tipo_equipamento': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'marca': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Marca do equipamento',
                'required': True
            }),
            'modelo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Modelo do equipamento',
                'required': True
            }),
            'numero_serie': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de série (opcional)'
            }),
            'defeito_relatado': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descreva o problema relatado pelo cliente',
                'required': True
            }),
            'defeito_encontrado': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Diagnóstico técnico do problema'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'prazo_estimado': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'valor_mao_obra': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'value': '0'
            }),
            'valor_pecas': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'value': '0',
                'readonly': True
            }),
            'desconto': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'value': '0'
            }),
            'dias_garantia': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'value': '90'
            }),
            'tecnico': forms.Select(attrs={
                'class': 'form-select'
            }),
            'observacoes_internas': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observações internas (não visível ao cliente)'
            }),
            'observacoes_cliente': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observações para o cliente'
            }),
        }


class PecaUtilizadaForm(forms.ModelForm):
    class Meta:
        model = PecaUtilizada
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
            }),
        }


# Formset para gerenciar múltiplas peças utilizadas
PecaUtilizadaFormSet = inlineformset_factory(
    OrdemServico,
    PecaUtilizada,
    form=PecaUtilizadaForm,
    extra=1,
    can_delete=True
)