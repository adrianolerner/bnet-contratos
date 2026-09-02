from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Boolean, Table, Text
from sqlalchemy.orm import relationship
from database import Base
import datetime

usuario_setor = Table(
    'usuario_setor', Base.metadata,
    Column('usuario_id', Integer, ForeignKey('usuarios.id')),
    Column('setor_id', Integer, ForeignKey('setores.id'))
)

class Setor(Base):
    __tablename__ = "setores"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), unique=True, index=True)
    observacao = Column(Text, nullable=True)
    
    usuarios = relationship("Usuario", secondary=usuario_setor, back_populates="setores")
    contratos = relationship("Contrato", back_populates="setor")
    pagamentos = relationship("PagamentoNota", back_populates="setor")
    processos = relationship("Processo", back_populates="setor")

class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100))
    email = Column(String(100), unique=True, index=True)
    telefone = Column(String(20))
    hashed_password = Column(String)
    privilegio = Column(String(20), default="usuario") # admin, usuario
    deve_trocar_senha = Column(Boolean, default=True)
    
    setores = relationship("Setor", secondary=usuario_setor, back_populates="usuarios")

class Fornecedor(Base):
    __tablename__ = "fornecedores"
    id = Column(Integer, primary_key=True, index=True)
    nome_fantasia = Column(String(90))
    razao_social = Column(String(90))
    cnpj = Column(String(18), unique=True, index=True)
    observacoes = Column(String(120), nullable=True)
    
    contatos = relationship("ContatoFornecedor", back_populates="fornecedor")
    contratos = relationship("Contrato", back_populates="fornecedor")
    pagamentos = relationship("PagamentoNota", back_populates="fornecedor")

class ContatoFornecedor(Base):
    __tablename__ = "contatos_fornecedores"
    id = Column(Integer, primary_key=True, index=True)
    fornecedor_id = Column(Integer, ForeignKey("fornecedores.id"))
    nome = Column(String(60))
    setor = Column(String(60))
    telefone = Column(String(20))
    email = Column(String(90))
    observacao = Column(String(120), nullable=True)
    
    fornecedor = relationship("Fornecedor", back_populates="contatos")

class Contrato(Base):
    __tablename__ = "contratos"
    id = Column(Integer, primary_key=True, index=True)
    numero = Column(String(12)) # 0000/0000
    fornecedor_id = Column(Integer, ForeignKey("fornecedores.id"))
    setor_id = Column(Integer, ForeignKey("setores.id"))
    servico = Column(String(90))
    fiscal = Column(String(90))
    vencimento = Column(Date)
    numero_empenho = Column(String(12))
    numero_ordem_compra = Column(String(12))
    numero_processo_digital = Column(String(12))
    valor_total = Column(Float)
    numero_licitacao = Column(String(12))
    situacao = Column(String(50)) # Emergencial, Em renovação, Renovado, Em vigência, Encerrado
    observacao = Column(String(120), nullable=True)
    
    fornecedor = relationship("Fornecedor", back_populates="contratos")
    setor = relationship("Setor", back_populates="contratos")

class PagamentoNota(Base):
    __tablename__ = "pagamentos_notas"
    id = Column(Integer, primary_key=True, index=True)
    fornecedor_id = Column(Integer, ForeignKey("fornecedores.id"))
    setor_id = Column(Integer, ForeignKey("setores.id"))
    numero_nota = Column(String(25))
    valor = Column(Float)
    numero_empenho = Column(String(12))
    numero_ordem_compra = Column(String(12))
    data_nota = Column(Date)
    data_vencimento = Column(Date)
    item = Column(String(60))
    status_pagamento = Column(String(50)) # Pago, Pendente, Em processo, Cancelado
    numero_processo_pagamento = Column(String(12))
    observacao = Column(String(120), nullable=True)
    
    fornecedor = relationship("Fornecedor", back_populates="pagamentos")
    setor = relationship("Setor", back_populates="pagamentos")

class Processo(Base):
    __tablename__ = "processos"
    id = Column(Integer, primary_key=True, index=True)
    setor_id = Column(Integer, ForeignKey("setores.id"))
    nome = Column(String(60))
    numero_processo = Column(String(12))
    status = Column(String(50)) # Não inciada, Em execução, Bloqueada, Concluido, Cancelada
    observacoes = Column(String(120), nullable=True)
    responsavel_id = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    
    setor = relationship("Setor", back_populates="processos")
    responsavel = relationship("Usuario")

class Notificacao(Base):
    __tablename__ = "notificacoes"
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    mensagem = Column(Text)
    lida = Column(Boolean, default=False)
    data_criacao = Column(Date, default=datetime.date.today)

class LogModificacao(Base):
    __tablename__ = "logs_modificacoes"
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    acao = Column(String(50)) # CRIOU, ATUALIZOU, DELETOU
    entidade = Column(String(100)) # Contrato, Processo, etc
    registro_id = Column(Integer, nullable=True)
    detalhes = Column(Text, nullable=True)
    data_hora = Column(String(30)) # Pode ser string ISO format para ser simples
    
    usuario = relationship("Usuario", backref="logs")

class Favorito(Base):
    __tablename__ = "favoritos"
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    tipo = Column(String(50)) # 'fornecedor', 'contato'
    entidade_id = Column(Integer)
    
    usuario = relationship("Usuario", backref="favoritos")

class Configuracao(Base):
    __tablename__ = "configuracoes"
    id = Column(Integer, primary_key=True, index=True)
    nome_orgao = Column(String(200), default="Prefeitura Municipal")
    logo_url = Column(Text, nullable=True) # caminho ou base64
    smtp_host = Column(String(100), nullable=True)
    smtp_port = Column(Integer, nullable=True)
    smtp_user = Column(String(100), nullable=True)
    smtp_pass = Column(String(100), nullable=True)
    waha_api_url = Column(String(200), nullable=True)
    waha_api_key = Column(String(200), nullable=True)
    waha_chat_id = Column(String(100), nullable=True)
    waha_session = Column(String(100), nullable=True)
    turnstile_secret_key = Column(String(200), nullable=True)
    turnstile_site_key = Column(String(200), nullable=True)
    turnstile_enabled = Column(Boolean, default=False)
