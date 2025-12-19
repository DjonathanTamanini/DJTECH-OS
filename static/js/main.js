// ========== DATA E HORA ==========
function updateDateTime() {
    const dateElement = document.getElementById('current-date');
    if (!dateElement) return;
    
    const now = new Date();
    const options = { 
        weekday: 'long', 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric' 
    };
    
    dateElement.textContent = now.toLocaleDateString('pt-BR', options);
}

// Atualizar data quando a página carregar
document.addEventListener('DOMContentLoaded', function() {
    updateDateTime();
});

// ========== CONFIRMAÇÃO DE EXCLUSÃO ==========
function confirmarExclusao(mensagem) {
    return confirm(mensagem || 'Tem certeza que deseja excluir este item?');
}

// ========== AUTO-HIDE ALERTS ==========
document.addEventListener('DOMContentLoaded', function() {
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000); // 5 segundos
    });
});

// ========== MÁSCARA DE CPF/CNPJ ==========
function mascaraCpfCnpj(input) {
    let valor = input.value.replace(/\D/g, '');
    
    if (valor.length <= 11) {
        // CPF: 000.000.000-00
        valor = valor.replace(/(\d{3})(\d)/, '$1.$2');
        valor = valor.replace(/(\d{3})(\d)/, '$1.$2');
        valor = valor.replace(/(\d{3})(\d{1,2})$/, '$1-$2');
    } else {
        // CNPJ: 00.000.000/0000-00
        valor = valor.replace(/^(\d{2})(\d)/, '$1.$2');
        valor = valor.replace(/^(\d{2})\.(\d{3})(\d)/, '$1.$2.$3');
        valor = valor.replace(/\.(\d{3})(\d)/, '.$1/$2');
        valor = valor.replace(/(\d{4})(\d)/, '$1-$2');
    }
    
    input.value = valor;
}

// ========== MÁSCARA DE TELEFONE ==========
function mascaraTelefone(input) {
    let valor = input.value.replace(/\D/g, '');
    
    if (valor.length <= 10) {
        // (00) 0000-0000
        valor = valor.replace(/^(\d{2})(\d)/, '($1) $2');
        valor = valor.replace(/(\d{4})(\d)/, '$1-$2');
    } else {
        // (00) 00000-0000
        valor = valor.replace(/^(\d{2})(\d)/, '($1) $2');
        valor = valor.replace(/(\d{5})(\d)/, '$1-$2');
    }
    
    input.value = valor;
}

// ========== MÁSCARA DE CEP ==========
function mascaraCep(input) {
    let valor = input.value.replace(/\D/g, '');
    valor = valor.replace(/^(\d{5})(\d)/, '$1-$2');
    input.value = valor;
}

// ========== BUSCAR CEP (ViaCEP) ==========
async function buscarCep(cep) {
    cep = cep.replace(/\D/g, '');
    
    if (cep.length !== 8) {
        return;
    }
    
    try {
        const response = await fetch(`https://viacep.com.br/ws/${cep}/json/`);
        const data = await response.json();
        
        if (data.erro) {
            alert('CEP não encontrado!');
            return;
        }
        
        // Preencher os campos
        const logradouroInput = document.getElementById('id_logradouro');
        const bairroInput = document.getElementById('id_bairro');
        const cidadeInput = document.getElementById('id_cidade');
        const estadoInput = document.getElementById('id_estado');
        
        if (logradouroInput) logradouroInput.value = data.logradouro;
        if (bairroInput) bairroInput.value = data.bairro;
        if (cidadeInput) cidadeInput.value = data.localidade;
        if (estadoInput) estadoInput.value = data.uf;
        
    } catch (error) {
        console.error('Erro ao buscar CEP:', error);
    }
}

// ========== FORMATAÇÃO DE MOEDA ==========
function formatarMoeda(valor) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(valor);
}

// ========== CALCULAR TOTAL (OS) ==========
function calcularTotal() {
    const maoObra = parseFloat(document.getElementById('id_valor_mao_obra')?.value || 0);
    const pecas = parseFloat(document.getElementById('id_valor_pecas')?.value || 0);
    const desconto = parseFloat(document.getElementById('id_desconto')?.value || 0);
    
    const total = (maoObra + pecas) - desconto;
    
    const totalElement = document.getElementById('valor_total');
    if (totalElement) {
        totalElement.textContent = formatarMoeda(total);
    }
}

// ========== TOOLTIP BOOTSTRAP ==========
document.addEventListener('DOMContentLoaded', function() {
    const tooltipTriggerList = [].slice.call(
        document.querySelectorAll('[data-bs-toggle="tooltip"]')
    );
    
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

// ========== LOADING BUTTON ==========
function showLoading(button) {
    const originalText = button.innerHTML;
    button.disabled = true;
    button.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Aguarde...';
    
    return function() {
        button.disabled = false;
        button.innerHTML = originalText;
    };
}

// ========== PRINT ==========
function imprimirOS(numeroOS) {
    window.print();
}