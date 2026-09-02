from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import date

# Setores
class SetorBase(BaseModel):
    nome: str
    observacao: Optional[str] = None

class SetorCreate(SetorBase):
    pass

class Setor(SetorBase):
    id: int
    class Config:
        from_attributes = True

# Usuarios
class UsuarioBase(BaseModel):
    nome: str
    email: EmailStr
    telefone: Optional[str] = None
    privilegio: str = "usuario"
    deve_trocar_senha: bool = True

class UsuarioSlim(BaseModel):
    id: int
    nome: str
    class Config:
        from_attributes = True

class UsuarioCreate(UsuarioBase):
    password: str
    setores_ids: List[int] = []

class UsuarioUpdate(BaseModel):
    nome: Optional[str] = None
    email: Optional[EmailStr] = None
    telefone: Optional[str] = None
    password: Optional[str] = None

class Usuario(UsuarioBase):
    id: int
    setores: List[Setor] = []
    class Config:
        from_attributes = True

# Fornecedores
class FornecedorBase(BaseModel):
    nome_fantasia: str
    razao_social: str
    cnpj: str
    observacoes: Optional[str] = None

class FornecedorCreate(FornecedorBase):
    pass

class Fornecedor(FornecedorBase):
    id: int
    class Config:
        from_attributes = True

# Contatos
class ContatoFornecedorBase(BaseModel):
    nome: str
    setor: str
    telefone: str
    email: EmailStr
    observacao: Optional[str] = None
    fornecedor_id: int

class ContatoFornecedorCreate(ContatoFornecedorBase):
    pass

class ContatoFornecedor(ContatoFornecedorBase):
    id: int
    fornecedor: Optional[Fornecedor] = None
    class Config:
        from_attributes = True

# Contratos
class ContratoBase(BaseModel):
    numero: str
    servico: str
    fiscal: str
    vencimento: date
    numero_empenho: str
    numero_ordem_compra: str
    numero_processo_digital: str
    valor_total: float
    numero_licitacao: str
    situacao: str
    observacao: Optional[str] = None
    fornecedor_id: int
    setor_id: int

class ContratoCreate(ContratoBase):
    pass

class Contrato(ContratoBase):
    id: int
    fornecedor: Optional[Fornecedor] = None
    setor: Optional[Setor] = None
    class Config:
        from_attributes = True

# Pagamentos
class PagamentoNotaBase(BaseModel):
    numero_nota: str
    valor: float
    numero_empenho: str
    numero_ordem_compra: str
    data_nota: date
    data_vencimento: date
    item: str
    status_pagamento: str
    numero_processo_pagamento: str
    observacao: Optional[str] = None
    fornecedor_id: int
    setor_id: int

class PagamentoNotaCreate(PagamentoNotaBase):
    pass

class PagamentoNota(PagamentoNotaBase):
    id: int
    fornecedor: Optional[Fornecedor] = None
    setor: Optional[Setor] = None
    class Config:
        from_attributes = True

# Processos
class ProcessoBase(BaseModel):
    nome: str
    numero_processo: str
    status: str
    observacoes: Optional[str] = None
    setor_id: int
    responsavel_id: Optional[int] = None

class ProcessoCreate(ProcessoBase):
    pass

class Processo(ProcessoBase):
    id: int
    setor: Optional[Setor] = None
    responsavel: Optional[UsuarioSlim] = None
    class Config:
        from_attributes = True

# Configuracao
class ConfiguracaoBase(BaseModel):
    nome_orgao: str
    logo_url: Optional[str] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_pass: Optional[str] = None
    waha_api_url: Optional[str] = None
    waha_api_key: Optional[str] = None
    waha_chat_id: Optional[str] = None
    waha_session: Optional[str] = None
    turnstile_secret_key: Optional[str] = None
    turnstile_site_key: Optional[str] = None
    turnstile_enabled: bool = False

class ConfiguracaoCreate(ConfiguracaoBase):
    pass

class Configuracao(ConfiguracaoBase):
    id: int
    class Config:
        from_attributes = True

# Notificacoes
class NotificacaoBase(BaseModel):
    mensagem: str
    lida: bool = False
    usuario_id: int

class NotificacaoCreate(NotificacaoBase):
    pass

class Notificacao(NotificacaoBase):
    id: int
    data_criacao: date
    class Config:
        from_attributes = True

# Logs de Modificacao
class LogModificacaoBase(BaseModel):
    usuario_id: int
    acao: str
    entidade: str
    registro_id: Optional[int] = None
    detalhes: Optional[str] = None
    data_hora: str

class LogModificacaoCreate(LogModificacaoBase):
    pass

class LogModificacao(LogModificacaoBase):
    id: int
    usuario: Optional[Usuario] = None
    class Config:
        from_attributes = True

# Favoritos
class FavoritoBase(BaseModel):
    tipo: str
    entidade_id: int

class FavoritoCreate(FavoritoBase):
    pass

class Favorito(FavoritoBase):
    id: int
    usuario_id: int
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class LoginData(BaseModel):
    email: str
    password: str
    turnstile_token: Optional[str] = None

class TestEmailData(BaseModel):
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_pass: str
    target_email: str

class TestWahaData(BaseModel):
    waha_api_url: str
    waha_api_key: str
    waha_chat_id: str
    waha_session: str
    target_phone: str
