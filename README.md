# Sistema de Gestão e Fiscalização de Contratos (BNET Contratos)

Sistema desenvolvido para controle e gestão eficiente de contratos públicos e privados. Ele conta com segmentação por setor, cadastro de fornecedores, pagamentos de notas fiscais, controle de processos e alertas de vencimentos através de um Dashboard inteligente.

<img width="1916" height="945" alt="image" src="https://github.com/user-attachments/assets/9262945c-2022-4a31-a4ce-371193e43a84" />

## 🚀 Funcionalidades Principais (Versão 1.0)
- **Dashboard e Alertas:** Visão consolidada de contratos em vigência, próximos do vencimento ou vencidos.
- **Favoritos e Filtros dinâmicos:** Marcação de itens favoritos e buscas avançadas.
- **Segurança de Acesso:** Rate limiting (proteção contra força bruta no login), cabeçalhos seguros (CORS e anti-clickjacking) e rotina de troca obrigatória de senha padrão.
- **Gestão Integrada:** Relacionamento entre fornecedores e seus respectivos contratos e contatos.
- **Notificações por E-mail (SMTP):** Alertas aos usuários no cadastro de contas ou reset de senhas. (WAHA/WhatsApp opcional configurável).
- **Relatórios:** Geração instantânea de PDFs e visualização detalhada em Modais modernos e responsivos.

## 🛠 Tecnologias Utilizadas
- **Backend:** Python (FastAPI, SQLAlchemy, PostgreSQL, APScheduler, SlowAPI para Rate Limit).
- **Frontend:** Vue.js 3 (Vite, Pinia) + Vuetify 3 (Dark Theme Padrão).
- **Infraestrutura:** Docker e Docker Compose.

## 📁 Estrutura de Diretórios
- `/src`: Código-fonte da API em Python.
- `/frontend`: Código-fonte do frontend em Vue (SPA).
- `/backups`: Pasta onde o sistema salva backups diários (se configurado).
- `docker-compose.yml`: Orquestração de containers para deploy local/produção.
- `.env`: Arquivo de variáveis sensíveis e chaves da aplicação.

## 🚀 Passo a Passo de Configuração e Instalação

### 1. Pré-requisitos
- Ter o **Docker** e o **Docker Compose** instalados na sua máquina ou servidor.
- Renomear `.env.example` para `.env` e ajustar as credenciais de banco, chave e URL do frontend.

### 2. Rodando o Sistema
No diretório raiz do projeto, execute o comando:
```bash
docker compose up -d --build
```
Isso irá iniciar e orquestrar três containers:
1. `bnet-contratos-db`: Banco de dados PostgreSQL (na porta 5432 apenas internamente).
2. `bnet-contratos-api`: Backend (FastAPI) rodando na porta 8000.
3. `bnet-contratos-frontend`: Frontend (Nginx) expondo o sistema web na porta 80.

### 3. Acessando
- **Sistema Web (Frontend):** Acesse `http://localhost/` (ou o IP do servidor).
- **Documentação da API:** Acesse `http://localhost:8000/docs`.

### 4. Configurações Dinâmicas pelo Painel Admin
Muitos recursos não exigem a alteração do código ou `.env`, e podem ser configurados via banco de dados na aba **Configurações** (acessível ao admin):
- **Identidade Visual:** Definir o Nome do Órgão (que reflete na aba do navegador) e o Brasão/Logo.
- **E-mails e Notificações (SMTP):** Configurar host, usuário e senha para disparos automáticos.
- **Segurança (Turnstile/WAHA):** Se habilitados, também são geridos pelo painel.

## 🔐 Backup e Restauração
O backend possui uma funcionalidade de backup automático via painel, mas caso queira realizar manualmente via Docker:

**Backup Completo:**
```bash
docker exec -t bnet-contratos-db pg_dumpall -c -U postgres > dump_bnet.sql
```
**Restauração:**
```bash
cat dump_bnet.sql | docker exec -i bnet-contratos-db psql -U postgres
```

## 📜 Licença e Autoria
Desenvolvido por **Adriano Lerner Biesek** (SMCTI - Castro).  
Distribuído sob a **MIT License**.
