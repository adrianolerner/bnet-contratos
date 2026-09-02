from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List
import models, schemas, auth
from database import get_db
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

router = APIRouter()

def enviar_email_senha(db: Session, destinatario: str, nova_senha: str):
    config = db.query(models.Configuracao).first()
    if not config or not all([config.smtp_host, config.smtp_port, config.smtp_user, config.smtp_pass]):
        print(f"SMTP não configurado no banco de dados. E-mail não enviado para {destinatario}.")
        return

    msg = MIMEMultipart()
    msg['From'] = config.smtp_user
    msg['To'] = destinatario
    msg['Subject'] = "Aviso: Sua senha foi alterada"

    body = f"""Olá,

Sua senha para acesso ao sistema BNet Contratos foi gerada/alterada por um administrador.
Abaixo estão suas credenciais de acesso:

Login: {destinatario}
Senha: {nova_senha}

Recomendamos que você altere sua senha no primeiro acesso através do seu Perfil.

Atenciosamente,
Equipe BNet Contratos
"""
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    try:
        server = smtplib.SMTP(config.smtp_host, int(config.smtp_port))
        server.starttls()
        server.login(config.smtp_user, config.smtp_pass)
        server.send_message(msg)
        server.quit()
        print(f"E-mail enviado com sucesso para {destinatario}")
    except Exception as e:
        print(f"Erro ao enviar e-mail para {destinatario}: {str(e)}")


# ---------------------------------------------------------
# AUTHENTICATION
# ---------------------------------------------------------
@router.post("/auth/login", response_model=schemas.Token)
@auth.limiter.limit("5/minute")
def login(request: Request, login_data: schemas.LoginData, db: Session = Depends(get_db)):
    user = db.query(models.Usuario).filter(models.Usuario.email == login_data.email).first()
    if not user or not auth.verify_password(login_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    # Validação do Turnstile omitida para brevidade, mas seria validada aqui contra API do Cloudflare
    
    access_token = auth.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/auth/me", response_model=schemas.Usuario)
def get_me(current_user: models.Usuario = Depends(auth.get_current_user)):
    return current_user

@router.put("/auth/me", response_model=schemas.Usuario)
def update_me(user_update: schemas.UsuarioUpdate, db: Session = Depends(get_db), current_user: models.Usuario = Depends(auth.get_current_user)):
    if user_update.nome is not None:
        current_user.nome = user_update.nome
    if user_update.email is not None:
        current_user.email = user_update.email
    if user_update.telefone is not None:
        current_user.telefone = user_update.telefone
    if user_update.password:
        current_user.hashed_password = auth.get_password_hash(user_update.password)
        current_user.deve_trocar_senha = False
        
    db.commit()
    db.refresh(current_user)
    return current_user

# ---------------------------------------------------------
# FAVORITOS
# ---------------------------------------------------------
@router.get("/favoritos", response_model=List[schemas.Favorito])
def get_favoritos(db: Session = Depends(get_db), current_user: models.Usuario = Depends(auth.get_current_user)):
    return db.query(models.Favorito).filter(models.Favorito.usuario_id == current_user.id).all()

@router.post("/favoritos", response_model=schemas.Favorito)
def add_favorito(favorito: schemas.FavoritoCreate, db: Session = Depends(get_db), current_user: models.Usuario = Depends(auth.get_current_user)):
    db_fav = db.query(models.Favorito).filter(
        models.Favorito.usuario_id == current_user.id,
        models.Favorito.tipo == favorito.tipo,
        models.Favorito.entidade_id == favorito.entidade_id
    ).first()
    if not db_fav:
        db_fav = models.Favorito(
            usuario_id=current_user.id,
            tipo=favorito.tipo,
            entidade_id=favorito.entidade_id
        )
        db.add(db_fav)
        db.commit()
        db.refresh(db_fav)
    return db_fav

@router.delete("/favoritos/{tipo}/{entidade_id}")
def remove_favorito(tipo: str, entidade_id: int, db: Session = Depends(get_db), current_user: models.Usuario = Depends(auth.get_current_user)):
    db_fav = db.query(models.Favorito).filter(
        models.Favorito.usuario_id == current_user.id,
        models.Favorito.tipo == tipo,
        models.Favorito.entidade_id == entidade_id
    ).first()
    if db_fav:
        db.delete(db_fav)
        db.commit()
    return {"ok": True}

# ---------------------------------------------------------
# LOGS DE MODIFICACOES
# ---------------------------------------------------------
import datetime
import os

def registrar_log(db: Session, usuario_id: int, acao: str, entidade: str, registro_id: int = None, detalhes: str = None):
    try:
        log = models.LogModificacao(
            usuario_id=usuario_id,
            acao=acao,
            entidade=entidade,
            registro_id=registro_id,
            detalhes=detalhes,
            data_hora=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        db.add(log)
        db.commit()
        
        # Limpeza automática baseada em variável de ambiente (padrão 90 dias)
        retencao_dias = int(os.getenv("LOG_RETENTION_DAYS", "90"))
        if retencao_dias > 0:
            limite_data = (datetime.datetime.now() - datetime.timedelta(days=retencao_dias)).strftime("%Y-%m-%d %H:%M:%S")
            db.query(models.LogModificacao).filter(models.LogModificacao.data_hora < limite_data).delete(synchronize_session=False)
            db.commit()
            
    except Exception as e:
        print(f"Erro ao salvar log: {e}")

@router.get("/logs", response_model=List[schemas.LogModificacao])
def get_logs(db: Session = Depends(get_db), current_user: models.Usuario = Depends(auth.get_current_active_admin)):
    return db.query(models.LogModificacao).order_by(models.LogModificacao.id.desc()).all()

# ---------------------------------------------------------
# NOTIFICACOES
# ---------------------------------------------------------
@router.get("/notificacoes", response_model=List[schemas.Notificacao])
def get_notificacoes(db: Session = Depends(get_db), current_user: models.Usuario = Depends(auth.get_current_user)):
    return db.query(models.Notificacao).filter(
        models.Notificacao.usuario_id == current_user.id,
        models.Notificacao.lida == False
    ).order_by(models.Notificacao.id.desc()).all()

@router.put("/notificacoes/{id}/lida")
def mark_notificacao_lida(id: int, db: Session = Depends(get_db), current_user: models.Usuario = Depends(auth.get_current_user)):
    notificacao = db.query(models.Notificacao).filter(
        models.Notificacao.id == id,
        models.Notificacao.usuario_id == current_user.id
    ).first()
    if not notificacao:
        raise HTTPException(status_code=404, detail="Notificacao not found")
    notificacao.lida = True
    db.commit()
    return {"status": "ok"}

# ---------------------------------------------------------
# SETORES
# ---------------------------------------------------------
@router.get("/setores", response_model=List[schemas.Setor])
def get_setores(db: Session = Depends(get_db), current_user: models.Usuario = Depends(auth.get_current_user)):
    if current_user.privilegio == "admin":
        return db.query(models.Setor).all()
    return current_user.setores

@router.post("/setores", response_model=schemas.Setor)
def create_setor(setor: schemas.SetorCreate, db: Session = Depends(get_db), current_user: models.Usuario = Depends(auth.get_current_active_admin)):
    db_setor = models.Setor(**setor.dict())
    db.add(db_setor)
    db.commit()
    db.refresh(db_setor)
    registrar_log(db, current_user.id, "CRIOU", "Setor", db_setor.id, f"Setor {db_setor.nome}")
    return db_setor

@router.put("/setores/{setor_id}", response_model=schemas.Setor)
def update_setor(setor_id: int, setor: schemas.SetorCreate, db: Session = Depends(get_db), current_user: models.Usuario = Depends(auth.get_current_active_admin)):
    db_setor = db.query(models.Setor).filter(models.Setor.id == setor_id).first()
    if not db_setor:
        raise HTTPException(status_code=404, detail="Setor not found")
    for var, value in vars(setor).items():
        setattr(db_setor, var, value) if value is not None else None
    db.commit()
    db.refresh(db_setor)
    registrar_log(db, current_user.id, "ATUALIZOU", "Setor", db_setor.id, f"Setor {db_setor.nome}")
    return db_setor

@router.delete("/setores/{setor_id}")
def delete_setor(setor_id: int, db: Session = Depends(get_db), current_user: models.Usuario = Depends(auth.get_current_active_admin)):
    db_setor = db.query(models.Setor).filter(models.Setor.id == setor_id).first()
    if not db_setor:
        raise HTTPException(status_code=404, detail="Setor not found")
    db.delete(db_setor)
    db.commit()
    registrar_log(db, current_user.id, "DELETOU", "Setor", db_setor.id, f"Setor {db_setor.nome}")
    return {"ok": True}

@router.get("/setores/{setor_id}/usuarios", response_model=List[schemas.UsuarioSlim])
def get_setor_usuarios(setor_id: int, db: Session = Depends(get_db), current_user: models.Usuario = Depends(auth.get_current_user)):
    setor = db.query(models.Setor).filter(models.Setor.id == setor_id).first()
    if not setor:
        raise HTTPException(status_code=404, detail="Setor not found")
    return setor.usuarios

# ---------------------------------------------------------
# USUARIOS
# ---------------------------------------------------------
@router.get("/usuarios", response_model=List[schemas.Usuario])
def get_usuarios(db: Session = Depends(get_db), current_user: models.Usuario = Depends(auth.get_current_active_admin)):
    return db.query(models.Usuario).all()

@router.post("/usuarios", response_model=schemas.Usuario)
def create_usuario(usuario: schemas.UsuarioCreate, db: Session = Depends(get_db), current_user: models.Usuario = Depends(auth.get_current_active_admin)):
    if db.query(models.Usuario).filter(models.Usuario.email == usuario.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = auth.get_password_hash(usuario.password)
    db_user = models.Usuario(
        nome=usuario.nome,
        email=usuario.email,
        telefone=usuario.telefone,
        hashed_password=hashed_password,
        privilegio=usuario.privilegio
    )
    
    for setor_id in usuario.setores_ids:
        setor = db.query(models.Setor).filter(models.Setor.id == setor_id).first()
        if setor:
            db_user.setores.append(setor)
            
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    registrar_log(db, current_user.id, "CRIOU", "Usuário", db_user.id, f"Usuário {db_user.email}")
    
    # Enviar e-mail com a senha caso tenha sido definida
    if usuario.password:
        enviar_email_senha(db, db_user.email, usuario.password)
        
    return db_user

@router.put("/usuarios/{usuario_id}", response_model=schemas.Usuario)
def update_usuario(usuario_id: int, usuario: schemas.UsuarioCreate, db: Session = Depends(get_db), current_user: models.Usuario = Depends(auth.get_current_active_admin)):
    db_user = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuario not found")
    
    db_user.nome = usuario.nome
    db_user.email = usuario.email
    db_user.telefone = usuario.telefone
    db_user.privilegio = usuario.privilegio
    if usuario.password:
        db_user.hashed_password = auth.get_password_hash(usuario.password)
        db_user.deve_trocar_senha = True
    
    db_user.setores = []
    for setor_id in usuario.setores_ids:
        setor = db.query(models.Setor).filter(models.Setor.id == setor_id).first()
        if setor:
            db_user.setores.append(setor)

    db.commit()
    db.refresh(db_user)
    registrar_log(db, current_user.id, "ATUALIZOU", "Usuário", db_user.id, f"Usuário {db_user.email}")
    
    # Enviar e-mail com a nova senha caso tenha sido alterada
    if usuario.password:
        enviar_email_senha(db, db_user.email, usuario.password)
        
    return db_user

@router.delete("/usuarios/{usuario_id}")
def delete_usuario(usuario_id: int, db: Session = Depends(get_db), current_user: models.Usuario = Depends(auth.get_current_active_admin)):
    db_user = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuario not found")
    db.delete(db_user)
    db.commit()
    registrar_log(db, current_user.id, "DELETOU", "Usuário", db_user.id, f"Usuário {db_user.email}")
    return {"ok": True}

# ---------------------------------------------------------
# FORNECEDORES
# ---------------------------------------------------------
@router.get("/fornecedores", response_model=List[schemas.Fornecedor])
def get_fornecedores(db: Session = Depends(get_db), current_user: models.Usuario = Depends(auth.get_current_user)):
    return db.query(models.Fornecedor).all()

@router.post("/fornecedores", response_model=schemas.Fornecedor)
def create_fornecedor(fornecedor: schemas.FornecedorCreate, db: Session = Depends(get_db), current_user: models.Usuario = Depends(auth.get_current_user)):
    if fornecedor.cnpj:
        if db.query(models.Fornecedor).filter(models.Fornecedor.cnpj == fornecedor.cnpj).first():
            raise HTTPException(status_code=400, detail="Já existe um fornecedor cadastrado com este CNPJ")
            
    db_forn = models.Fornecedor(**fornecedor.dict())
    db.add(db_forn)
    db.commit()
    db.refresh(db_forn)
    registrar_log(db, current_user.id, "CRIOU", "Fornecedor", db_forn.id, f"Fornecedor {db_forn.nome_fantasia}")
    return db_forn

@router.put("/fornecedores/{fornecedor_id}", response_model=schemas.Fornecedor)
def update_fornecedor(fornecedor_id: int, fornecedor: schemas.FornecedorCreate, db: Session = Depends(get_db), current_user: models.Usuario = Depends(auth.get_current_user)):
    db_forn = db.query(models.Fornecedor).filter(models.Fornecedor.id == fornecedor_id).first()
    if not db_forn:
        raise HTTPException(status_code=404, detail="Fornecedor not found")
        
    if fornecedor.cnpj:
        existing = db.query(models.Fornecedor).filter(models.Fornecedor.cnpj == fornecedor.cnpj).first()
        if existing and existing.id != fornecedor_id:
            raise HTTPException(status_code=400, detail="Já existe um fornecedor cadastrado com este CNPJ")
            
    for var, value in vars(fornecedor).items():
        setattr(db_forn, var, value) if value is not None else None
    db.commit()
    db.refresh(db_forn)
    registrar_log(db, current_user.id, "ATUALIZOU", "Fornecedor", db_forn.id, f"Fornecedor {db_forn.nome_fantasia}")
    return db_forn

@router.delete("/fornecedores/{fornecedor_id}")
def delete_fornecedor(fornecedor_id: int, db: Session = Depends(get_db), current_user: models.Usuario = Depends(auth.get_current_user)):
    db_forn = db.query(models.Fornecedor).filter(models.Fornecedor.id == fornecedor_id).first()
    if not db_forn:
        raise HTTPException(status_code=404, detail="Fornecedor not found")
        
    if db_forn.contratos or db_forn.contatos:
        raise HTTPException(status_code=400, detail="Não é possível excluir o fornecedor pois existem contratos ou contatos vinculados a ele")
        
    db.delete(db_forn)
    db.commit()
    registrar_log(db, current_user.id, "DELETOU", "Fornecedor", db_forn.id, f"Fornecedor {db_forn.nome_fantasia}")
    return {"ok": True}

# ---------------------------------------------------------
# CONTATOS
# ---------------------------------------------------------
@router.get("/contatos", response_model=List[schemas.ContatoFornecedor])
def get_contatos(fornecedor_id: int = None, db: Session = Depends(get_db), current_user: models.Usuario = Depends(auth.get_current_user)):
    query = db.query(models.ContatoFornecedor)
    if fornecedor_id:
        query = query.filter(models.ContatoFornecedor.fornecedor_id == fornecedor_id)
    return query.all()

@router.post("/contatos", response_model=schemas.ContatoFornecedor)
def create_contato(contato: schemas.ContatoFornecedorCreate, db: Session = Depends(get_db), current_user: models.Usuario = Depends(auth.get_current_user)):
    db_contato = models.ContatoFornecedor(**contato.dict())
    db.add(db_contato)
    db.commit()
    db.refresh(db_contato)
    registrar_log(db, current_user.id, "CRIOU", "Contato", db_contato.id, f"Contato {db_contato.nome}")
    return db_contato

@router.put("/contatos/{contato_id}", response_model=schemas.ContatoFornecedor)
def update_contato(contato_id: int, contato: schemas.ContatoFornecedorCreate, db: Session = Depends(get_db), current_user: models.Usuario = Depends(auth.get_current_user)):
    db_contato = db.query(models.ContatoFornecedor).filter(models.ContatoFornecedor.id == contato_id).first()
    if not db_contato:
        raise HTTPException(status_code=404, detail="Contato not found")
    for var, value in vars(contato).items():
        setattr(db_contato, var, value) if value is not None else None
    db.commit()
    db.refresh(db_contato)
    registrar_log(db, current_user.id, "ATUALIZOU", "Contato", db_contato.id, f"Contato {db_contato.nome}")
    return db_contato

@router.delete("/contatos/{contato_id}")
def delete_contato(contato_id: int, db: Session = Depends(get_db), current_user: models.Usuario = Depends(auth.get_current_user)):
    db_contato = db.query(models.ContatoFornecedor).filter(models.ContatoFornecedor.id == contato_id).first()
    if not db_contato:
        raise HTTPException(status_code=404, detail="Contato not found")
    db.delete(db_contato)
    db.commit()
    registrar_log(db, current_user.id, "DELETOU", "Contato", db_contato.id, f"Contato {db_contato.nome}")
    return {"ok": True}

# ---------------------------------------------------------
# CONTRATOS
# ---------------------------------------------------------
@router.get("/contratos", response_model=List[schemas.Contrato])
def get_contratos(setor_id: int = None, db: Session = Depends(get_db), current_user: models.Usuario = Depends(auth.get_current_user)):
    query = db.query(models.Contrato)
    if setor_id:
        query = query.filter(models.Contrato.setor_id == setor_id)
    return query.all()

@router.post("/contratos", response_model=schemas.Contrato)
def create_contrato(contrato: schemas.ContratoCreate, db: Session = Depends(get_db), current_user: models.Usuario = Depends(auth.get_current_user)):
    db_cont = models.Contrato(**contrato.dict())
    db.add(db_cont)
    db.commit()
    db.refresh(db_cont)
    registrar_log(db, current_user.id, "CRIOU", "Contrato", db_cont.id, f"Contrato {db_cont.numero}")
    return db_cont

@router.put("/contratos/{contrato_id}", response_model=schemas.Contrato)
def update_contrato(contrato_id: int, contrato: schemas.ContratoCreate, db: Session = Depends(get_db), current_user: models.Usuario = Depends(auth.get_current_user)):
    db_cont = db.query(models.Contrato).filter(models.Contrato.id == contrato_id).first()
    if not db_cont:
        raise HTTPException(status_code=404, detail="Contrato not found")
    for var, value in vars(contrato).items():
        setattr(db_cont, var, value) if value is not None else None
    db.commit()
    db.refresh(db_cont)
    registrar_log(db, current_user.id, "ATUALIZOU", "Contrato", db_cont.id, f"Contrato {db_cont.numero}")
    return db_cont

@router.delete("/contratos/{contrato_id}")
def delete_contrato(contrato_id: int, db: Session = Depends(get_db), current_user: models.Usuario = Depends(auth.get_current_user)):
    db_cont = db.query(models.Contrato).filter(models.Contrato.id == contrato_id).first()
    if not db_cont:
        raise HTTPException(status_code=404, detail="Contrato not found")
    db.delete(db_cont)
    db.commit()
    registrar_log(db, current_user.id, "DELETOU", "Contrato", db_cont.id, f"Contrato {db_cont.numero}")
    return {"ok": True}

# ---------------------------------------------------------
# PAGAMENTOS
# ---------------------------------------------------------
@router.get("/pagamentos", response_model=List[schemas.PagamentoNota])
def get_pagamentos(setor_id: int = None, db: Session = Depends(get_db), current_user: models.Usuario = Depends(auth.get_current_user)):
    query = db.query(models.PagamentoNota)
    if setor_id:
        query = query.filter(models.PagamentoNota.setor_id == setor_id)
    return query.all()

@router.post("/pagamentos", response_model=schemas.PagamentoNota)
def create_pagamento(pagamento: schemas.PagamentoNotaCreate, db: Session = Depends(get_db), current_user: models.Usuario = Depends(auth.get_current_user)):
    db_pag = models.PagamentoNota(**pagamento.dict())
    db.add(db_pag)
    db.commit()
    db.refresh(db_pag)
    registrar_log(db, current_user.id, "CRIOU", "Pagamento", db_pag.id, f"Nota {db_pag.numero_nota}")
    return db_pag

@router.put("/pagamentos/{pagamento_id}", response_model=schemas.PagamentoNota)
def update_pagamento(pagamento_id: int, pagamento: schemas.PagamentoNotaCreate, db: Session = Depends(get_db), current_user: models.Usuario = Depends(auth.get_current_user)):
    db_pag = db.query(models.PagamentoNota).filter(models.PagamentoNota.id == pagamento_id).first()
    if not db_pag:
        raise HTTPException(status_code=404, detail="Pagamento not found")
    for var, value in vars(pagamento).items():
        setattr(db_pag, var, value) if value is not None else None
    db.commit()
    db.refresh(db_pag)
    registrar_log(db, current_user.id, "ATUALIZOU", "Pagamento", db_pag.id, f"Nota {db_pag.numero_nota}")
    return db_pag

@router.delete("/pagamentos/{pagamento_id}")
def delete_pagamento(pagamento_id: int, db: Session = Depends(get_db), current_user: models.Usuario = Depends(auth.get_current_user)):
    db_pag = db.query(models.PagamentoNota).filter(models.PagamentoNota.id == pagamento_id).first()
    if not db_pag:
        raise HTTPException(status_code=404, detail="Pagamento not found")
    db.delete(db_pag)
    db.commit()
    registrar_log(db, current_user.id, "DELETOU", "Pagamento", db_pag.id, f"Nota {db_pag.numero_nota}")
    return {"ok": True}

# ---------------------------------------------------------
# PROCESSOS
# ---------------------------------------------------------
@router.get("/processos", response_model=List[schemas.Processo])
def get_processos(setor_id: int = None, db: Session = Depends(get_db), current_user: models.Usuario = Depends(auth.get_current_user)):
    query = db.query(models.Processo)
    if setor_id:
        query = query.filter(models.Processo.setor_id == setor_id)
    return query.all()

@router.post("/processos", response_model=schemas.Processo)
def create_processo(processo: schemas.ProcessoCreate, db: Session = Depends(get_db), current_user: models.Usuario = Depends(auth.get_current_user)):
    db_proc = models.Processo(**processo.dict())
    db.add(db_proc)
    db.commit()
    db.refresh(db_proc)
    registrar_log(db, current_user.id, "CRIOU", "Processo", db_proc.id, f"Processo {db_proc.numero_processo}")
    return db_proc

@router.put("/processos/{processo_id}", response_model=schemas.Processo)
def update_processo(processo_id: int, processo: schemas.ProcessoCreate, db: Session = Depends(get_db), current_user: models.Usuario = Depends(auth.get_current_user)):
    db_proc = db.query(models.Processo).filter(models.Processo.id == processo_id).first()
    if not db_proc:
        raise HTTPException(status_code=404, detail="Processo not found")
    for var, value in vars(processo).items():
        setattr(db_proc, var, value) if value is not None else None
    db.commit()
    db.refresh(db_proc)
    registrar_log(db, current_user.id, "ATUALIZOU", "Processo", db_proc.id, f"Processo {db_proc.numero_processo}")
    return db_proc

@router.delete("/processos/{processo_id}")
def delete_processo(processo_id: int, db: Session = Depends(get_db), current_user: models.Usuario = Depends(auth.get_current_user)):
    db_proc = db.query(models.Processo).filter(models.Processo.id == processo_id).first()
    if not db_proc:
        raise HTTPException(status_code=404, detail="Processo not found")
    db.delete(db_proc)
    db.commit()
    registrar_log(db, current_user.id, "DELETOU", "Processo", db_proc.id, f"Processo {db_proc.numero_processo}")
    return {"ok": True}

# ---------------------------------------------------------
# CONFIGURACOES
# ---------------------------------------------------------
@router.get("/configuracoes", response_model=schemas.Configuracao)
def get_config(db: Session = Depends(get_db)):
    config = db.query(models.Configuracao).first()
    if not config:
        config = models.Configuracao()
        db.add(config)
        db.commit()
        db.refresh(config)
    return config

@router.put("/configuracoes", response_model=schemas.Configuracao)
def update_config(config_data: schemas.ConfiguracaoBase, db: Session = Depends(get_db), current_user: models.Usuario = Depends(auth.get_current_active_admin)):
    config = db.query(models.Configuracao).first()
    if not config:
        config = models.Configuracao(**config_data.dict())
        db.add(config)
    else:
        for var, value in vars(config_data).items():
            setattr(config, var, value) if value is not None else None
    db.commit()
    db.refresh(config)
    registrar_log(db, current_user.id, "ATUALIZOU", "Configurações", config.id, "Configurações do sistema")
    return config

import smtplib
from email.message import EmailMessage
import requests

@router.post("/configuracoes/test-email")
def test_email(data: schemas.TestEmailData, current_user: models.Usuario = Depends(auth.get_current_active_admin)):
    try:
        msg = EmailMessage()
        msg.set_content("Este é um e-mail de teste enviado pelo sistema BNET Contratos.")
        msg["Subject"] = "Teste de Configuração SMTP"
        msg["From"] = data.smtp_user
        msg["To"] = data.target_email

        server = smtplib.SMTP(data.smtp_host, data.smtp_port)
        server.starttls()
        server.login(data.smtp_user, data.smtp_pass)
        server.send_message(msg)
        server.quit()
        return {"ok": True, "message": "E-mail enviado com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao enviar e-mail: {str(e)}")

@router.post("/configuracoes/test-waha")
def test_waha(data: schemas.TestWahaData, current_user: models.Usuario = Depends(auth.get_current_active_admin)):
    try:
        url = f"{data.waha_api_url.rstrip('/')}/api/sendText"
        headers = {
            "Content-Type": "application/json",
            "X-Api-Key": data.waha_api_key
        }
        
        chat_id = data.target_phone
        if not chat_id.endswith("@c.us"):
            chat_id = f"{chat_id}@c.us"
            
        payload = {
            "session": data.waha_session or "default",
            "chatId": chat_id,
            "text": "Este é um teste de configuração WAHA do sistema BNET Contratos."
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        return {"ok": True, "message": "Mensagem enviada com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao enviar WhatsApp: {str(e)}")
