from django import forms
from django.forms import inlineformset_factory
from .models import OrdemServico, PecaUtilizadaOS # CORREÇÃO
from clientes.models import Cliente

class OrdemServicoForm(forms.ModelForm):
    class Meta:
        model = OrdemServico
        fields = [
            'cliente', 'tipo_equipamento', 'marca', 'modelo', 'numero_serie',
            'defeito_cliente', 'diagnostico_tecnico', 'status', 'prioridade', # CORREÇÃO: defeito_cliente
            'data_previsao', 'garantia_dias', 'valor_mao_de_obra', 'desconto',
            'tecnico', 'observacoes_internas', 'observacoes_cliente'
        ]
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'tipo_equipamento': forms.TextInput(attrs={'class': 'form-control'}), # Ajustado para CharField
            'marca': forms.TextInput(attrs={'class': 'form-control'}),
            'modelo': forms.TextInput(attrs={'class': 'form-control'}),
            'numero_serie': forms.TextInput(attrs={'class': 'form-control'}),
            'defeito_cliente': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'diagnostico_tecnico': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'prioridade': forms.Select(attrs={'class': 'form-select'}),
            'data_previsao': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'garantia_dias': forms.NumberInput(attrs={'class': 'form-control'}),
            'valor_mao_de_obra': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'desconto': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tecnico': forms.Select(attrs={'class': 'form-select'}),
            'observacoes_internas': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'observacoes_cliente': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

class PecaUtilizadaForm(forms.ModelForm):
    class Meta:
        model = PecaUtilizadaOS # CORREÇÃO
        fields = ['peca', 'quantidade', 'preco_unitario'] # CORREÇÃO: preco_unitario
        widgets = {
            'peca': forms.Select(attrs={'class': 'form-select'}),
            'quantidade': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'preco_unitario': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

# CORREÇÃO: Formset usando o modelo correto e extra=0
PecaUtilizadaFormSet = inlineformset_factory(
    OrdemServico,
    PecaUtilizadaOS, # CORREÇÃO
    form=PecaUtilizadaForm,
    extra=0,
    min_num=0,
    validate_min=False,
    can_delete=True
)