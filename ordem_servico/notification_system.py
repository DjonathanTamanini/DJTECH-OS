# notifications/tasks.py
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from ordem_servico.models import OrdemServico
from datetime import date, timedelta
import requests


@shared_task
def enviar_email_status_os(os_id, tipo_notificacao):
    """
    Envia email ao cliente sobre mudança de status da OS
    Tipos: entrada, orcamento, aprovacao, conclusao, entrega
    """
    try:
        os = OrdemServico.objects.get(id=os_id)
        
        if not os.cliente.email:
            return {'status': 'erro', 'mensagem': 'Cliente sem email cadastrado'}
        
        assunto = f"OS {os.numero_os} - "
        mensagem = f"Olá {os.cliente.nome},\n\n"
        
        if tipo_notificacao == 'entrada':
            assunto += "Equipamento Recebido"
            mensagem += f"""Confirmamos o recebimento do seu equipamento:

📱 Equipamento: {os.get_tipo_equipamento_display()} {os.marca} {os.modelo}
🔧 Defeito relatado: {os.defeito_relatado}
📋 Número da OS: {os.numero_os}
📅 Data de entrada: {os.data_entrada.strftime('%d/%m/%Y %H:%M')}
⏰ Prazo estimado: {os.prazo_estimado.strftime('%d/%m/%Y') if os.prazo_estimado else 'A definir'}

Você receberá novas atualizações sobre o andamento do reparo.
"""
        
        elif tipo_notificacao == 'orcamento':
            assunto += "Orçamento Disponível para Aprovação"
            mensagem += f"""Seu equipamento foi avaliado e o orçamento está disponível:

💰 ORÇAMENTO:
• Mão de obra: R$ {os.valor_mao_obra}
• Peças: R$ {os.valor_pecas}
• Desconto: R$ {os.desconto}
━━━━━━━━━━━━━━━━━━━━
TOTAL: R$ {os.valor_total}

⏰ Prazo de execução: {os.prazo_estimado.strftime('%d/%m/%Y') if os.prazo_estimado else 'A definir'}
🛡️ Garantia: {os.dias_garantia} dias

Por favor, entre em contato para aprovar ou rejeitar o orçamento.
Telefone: {settings.COMPANY_PHONE if hasattr(settings, 'COMPANY_PHONE') else '(XX) XXXXX-XXXX'}
"""
        
        elif tipo_notificacao == 'aprovacao':
            assunto += "Orçamento Aprovado - Reparo Iniciado"
            mensagem += f"""Seu orçamento foi aprovado e o reparo já foi iniciado!

📋 OS: {os.numero_os}
💰 Valor: R$ {os.valor_total}
📅 Previsão de conclusão: {os.prazo_estimado.strftime('%d/%m/%Y') if os.prazo_estimado else 'Em breve'}

Você será notificado quando o reparo for concluído.
"""
        
        elif tipo_notificacao == 'conclusao':
            assunto += "✅ Reparo Concluído - Equipamento Pronto!"
            mensagem += f"""Ótimas notícias! Seu equipamento está pronto para retirada! 🎉

📋 OS: {os.numero_os}
🔧 Equipamento: {os.get_tipo_equipamento_display()} {os.marca} {os.modelo}
💰 Valor total: R$ {os.valor_total}
🛡️ Garantia: {os.dias_garantia} dias

Aguardamos você em nosso estabelecimento.
Horário de atendimento: Segunda a Sexta, 8h às 18h

Endereço: {settings.COMPANY_ADDRESS if hasattr(settings, 'COMPANY_ADDRESS') else 'Ver nosso site'}
"""
        
        elif tipo_notificacao == 'entrega':
            assunto += "Equipamento Entregue - Obrigado!"
            mensagem += f"""Obrigado por confiar em nossos serviços! 🙏

📋 OS: {os.numero_os}
🔧 Equipamento: {os.get_tipo_equipamento_display()} {os.marca} {os.modelo}
📅 Data de entrega: {os.data_entrega.strftime('%d/%m/%Y %H:%M')}
🛡️ Garantia válida até: {os.data_fim_garantia.strftime('%d/%m/%Y') if os.data_fim_garantia else 'N/A'}

Qualquer problema durante o período de garantia, entre em contato conosco.

Avalie nosso serviço: {settings.SITE_URL}/avaliar/{os.id}/
"""
        
        mensagem += f"""
━━━━━━━━━━━━━━━━━━━━

Atenciosamente,
{settings.COMPANY_NAME if hasattr(settings, 'COMPANY_NAME') else 'DJTECH-OS'}

---
Este é um email automático. Não responda.
"""
        
        send_mail(
            assunto,
            mensagem,
            settings.DEFAULT_FROM_EMAIL,
            [os.cliente.email],
            fail_silently=False,
        )
        
        return {'status': 'sucesso', 'mensagem': f'Email enviado para {os.cliente.email}'}
        
    except OrdemServico.DoesNotExist:
        return {'status': 'erro', 'mensagem': 'OS não encontrada'}
    except Exception as e:
        return {'status': 'erro', 'mensagem': str(e)}


@shared_task
def enviar_sms_status_os(os_id, tipo_notificacao):
    """
    Envia SMS ao cliente (requer integração com gateway SMS)
    Ex: Twilio, Nexmo, TotalVoice, etc.
    """
    try:
        os = OrdemServico.objects.get(id=os_id)
        
        if not os.cliente.telefone_principal:
            return {'status': 'erro', 'mensagem': 'Cliente sem telefone'}
        
        mensagem = ""
        
        if tipo_notificacao == 'entrada':
            mensagem = f"DJTECH-OS: Equipamento recebido. OS {os.numero_os}. Aguarde atualizações."
        
        elif tipo_notificacao == 'orcamento':
            mensagem = f"DJTECH-OS: Orçamento pronto! OS {os.numero_os} - R$ {os.valor_total}. Entre em contato."
        
        elif tipo_notificacao == 'conclusao':
            mensagem = f"DJTECH-OS: Equipamento pronto! OS {os.numero_os}. Retire em nosso estabelecimento."
        
        # Exemplo com Twilio (substituir por seu gateway)
        # from twilio.rest import Client
        # client = Client(settings.TWILIO_SID, settings.TWILIO_TOKEN)
        # client.messages.create(
        #     body=mensagem,
        #     from_=settings.TWILIO_PHONE,
        #     to=os.cliente.telefone_principal
        # )
        
        # Exemplo genérico com API REST
        # response = requests.post(
        #     'https://api.gateway-sms.com/send',
        #     json={
        #         'to': os.cliente.telefone_principal,
        #         'message': mensagem,
        #         'token': settings.SMS_API_TOKEN
        #     }
        # )
        
        return {'status': 'sucesso', 'mensagem': 'SMS enviado'}
        
    except Exception as e:
        return {'status': 'erro', 'mensagem': str(e)}


@shared_task
def verificar_os_atrasadas():
    """
    Tarefa agendada (diária) para notificar OS atrasadas
    Executar via Celery Beat: todo dia às 9h
    """
    hoje = date.today()
    os_atrasadas = OrdemServico.objects.filter(
        prazo_estimado__lt=hoje,
        status__in=['avaliacao', 'aprovado', 'em_reparo']
    ).select_related('cliente', 'tecnico')
    
    if os_atrasadas.count() == 0:
        return {'status': 'ok', 'mensagem': 'Nenhuma OS atrasada'}
    
    # Notificar gerente/admin
    mensagem = f"⚠️ ATENÇÃO: {os_atrasadas.count()} ordem(ns) de serviço atrasada(s):\n\n"
    
    for os in os_atrasadas:
        dias_atraso = (hoje - os.prazo_estimado).days
        mensagem += f"• OS {os.numero_os} - {os.cliente.nome}\n"
        mensagem += f"  Atraso: {dias_atraso} dia(s)\n"
        mensagem += f"  Técnico: {os.tecnico.get_full_name() if os.tecnico else 'Não atribuído'}\n\n"
    
    # Enviar para administradores
    from django.contrib.auth.models import User
    admins = User.objects.filter(is_staff=True, email__isnull=False)
    
    for admin in admins:
        send_mail(
            '⚠️ Alerta: Ordens de Serviço Atrasadas',
            mensagem,
            settings.DEFAULT_FROM_EMAIL,
            [admin.email],
            fail_silently=True,
        )
    
    return {
        'status': 'sucesso',
        'total_atrasadas': os_atrasadas.count(),
        'notificados': admins.count()
    }


@shared_task
def lembrete_prazo_estimado():
    """
    Envia lembrete 1 dia antes do prazo estimado
    Executar diariamente às 10h
    """
    amanha = date.today() + timedelta(days=1)
    
    os_proximas = OrdemServico.objects.filter(
        prazo_estimado=amanha,
        status__in=['avaliacao', 'aprovado', 'em_reparo']
    ).select_related('tecnico')
    
    for os in os_proximas:
        if os.tecnico and os.tecnico.email:
            send_mail(
                f'Lembrete: OS {os.numero_os} vence amanhã',
                f"""Olá {os.tecnico.get_full_name()},

A OS {os.numero_os} tem prazo para amanhã ({amanha.strftime('%d/%m/%Y')}).

Cliente: {os.cliente.nome}
Equipamento: {os.get_tipo_equipamento_display()} {os.marca} {os.modelo}
Status atual: {os.get_status_display()}

Acesse o sistema para atualizar o status.
""",
                settings.DEFAULT_FROM_EMAIL,
                [os.tecnico.email],
                fail_silently=True,
            )
    
    return {
        'status': 'sucesso',
        'lembretes_enviados': os_proximas.count()
    }


@shared_task
def solicitar_avaliacao_cliente(os_id):
    """
    Solicita avaliação do cliente após a entrega
    Enviar 2-3 dias após a entrega
    """
    try:
        os = OrdemServico.objects.get(id=os_id)
        
        if not os.cliente.email or os.status != 'entregue':
            return {'status': 'erro', 'mensagem': 'Condições não atendidas'}
        
        mensagem = f"""Olá {os.cliente.nome},

Esperamos que esteja satisfeito com o reparo do seu {os.get_tipo_equipamento_display()}!

Sua opinião é muito importante para nós. 
Por favor, avalie nosso serviço (leva apenas 1 minuto):

{settings.SITE_URL}/avaliar/{os.id}/

OS: {os.numero_os}
Data de entrega: {os.data_entrega.strftime('%d/%m/%Y')}

Obrigado pela confiança!

Atenciosamente,
{settings.COMPANY_NAME if hasattr(settings, 'COMPANY_NAME') else 'DJTECH-OS'}
"""
        
        send_mail(
            'Avalie nosso serviço',
            mensagem,
            settings.DEFAULT_FROM_EMAIL,
            [os.cliente.email],
            fail_silently=False,
        )
        
        return {'status': 'sucesso'}
        
    except Exception as e:
        return {'status': 'erro', 'mensagem': str(e)}


# celery.py (configuração)
"""
from celery import Celery
from celery.schedules import crontab
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djtech.settings')

app = Celery('djtech')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Tarefas agendadas
app.conf.beat_schedule = {
    'verificar-os-atrasadas': {
        'task': 'notifications.tasks.verificar_os_atrasadas',
        'schedule': crontab(hour=9, minute=0),  # Todo dia às 9h
    },
    'lembrete-prazo-estimado': {
        'task': 'notifications.tasks.lembrete_prazo_estimado',
        'schedule': crontab(hour=10, minute=0),  # Todo dia às 10h
    },
}

# settings.py
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'America/Sao_Paulo'

# Configurações de email
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'seu-email@gmail.com'
EMAIL_HOST_PASSWORD = 'sua-senha-app'
DEFAULT_FROM_EMAIL = 'DJTECH-OS <seu-email@gmail.com>'

# Informações da empresa
COMPANY_NAME = 'DJTECH Assistência Técnica'
COMPANY_PHONE = '(XX) XXXXX-XXXX'
COMPANY_ADDRESS = 'Rua Exemplo, 123 - Cidade/UF'
SITE_URL = 'https://seu-site.com.br'
"""
