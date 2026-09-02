from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from database import SessionLocal
import models
from datetime import date

def verificar_contratos_vencimento():
    print("Executando verificação de contratos vencendo...")
    db = SessionLocal()
    try:
        contratos = db.query(models.Contrato).filter(
            models.Contrato.situacao.in_(['Em vigência', 'Emergencial'])
        ).all()
        hoje = date.today()
        
        config = db.query(models.Configuracao).first()
        
        for contrato in contratos:
            dias_restantes = (contrato.vencimento - hoje).days
            
            enviar_alerta = False
            
            if dias_restantes > 90:
                enviar_alerta = False
            elif 60 <= dias_restantes <= 89:
                # 1 notificação por semana (ex: toda Segunda-feira)
                if hoje.weekday() == 0:
                    enviar_alerta = True
            elif 30 <= dias_restantes <= 59:
                # 2 notificações por semana (ex: Segunda-feira e Quinta-feira)
                if hoje.weekday() in [0, 3]:
                    enviar_alerta = True
            elif dias_restantes < 30:
                # 1 notificação por dia
                enviar_alerta = True
                
            if enviar_alerta:
                if dias_restantes < 0:
                    mensagem = f"O contrato {contrato.numero} do fornecedor {contrato.fornecedor.nome_fantasia} está vencido há {abs(dias_restantes)} dias."
                elif dias_restantes == 0:
                    mensagem = f"O contrato {contrato.numero} do fornecedor {contrato.fornecedor.nome_fantasia} vence HOJE."
                else:
                    mensagem = f"O contrato {contrato.numero} do fornecedor {contrato.fornecedor.nome_fantasia} vencerá em {dias_restantes} dias."
                    
                print(f"Alerta: {mensagem}")
                
                # Criar notificação in-app para os usuários do setor
                for usuario in contrato.setor.usuarios:
                    notif = models.Notificacao(
                        usuario_id=usuario.id,
                        mensagem=mensagem
                    )
                    db.add(notif)
                
                db.commit()

                # Aqui entraria a chamada SMTP e WAHA usando as configurações
                if config and config.waha_api_url:
                    # Enviar WhatsApp (mock)
                    pass
                if config and config.smtp_host:
                    # Enviar E-mail (mock)
                    pass
                
    finally:
        db.close()

scheduler = BackgroundScheduler()
# Executa diariamente em horário comercial aleatório (12:30 +/- 4.5h = entre 08:00 e 17:00)
scheduler.add_job(verificar_contratos_vencimento, CronTrigger(hour=12, minute=30, jitter=16200))

def start_scheduler():
    scheduler.start()
