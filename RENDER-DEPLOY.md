# Deploy da LM TECH CRM no Render

O projeto está preparado para o **Render Blueprint**, criando o Web Service e o PostgreSQL e ligando os dois automaticamente.

## 1. Suba estes arquivos para um repositório GitHub

O arquivo `render.yaml` precisa ficar na **raiz do repositório**, no mesmo nível de `app.py`, `requirements.txt` e `start.sh`.

## 2. Crie pelo Blueprint

No Render:

1. `New` → `Blueprint`.
2. Conecte o repositório.
3. O Render detectará `render.yaml`.
4. Ele criará:
   - `lm-tech-crm` — Web Service Python.
   - `lm-tech-crm-db` — PostgreSQL.
5. Antes/finalizando o Blueprint, preencha as variáveis marcadas como secretas:
   - `GOOGLE_CLIENT_ID`
   - `GOOGLE_CLIENT_SECRET`
   - `ALLOWED_GOOGLE_EMAILS`

`DATABASE_URL` **não precisa ser copiada manualmente** quando você usa o Blueprint: ela vem do PostgreSQL criado pelo próprio `render.yaml`.

## 3. Google OAuth

Depois que o Web Service existir, copie a URL pública do Render, por exemplo:

`https://lm-tech-crm.onrender.com`

No Google Cloud Console, no OAuth Client do tipo **Web application**, adicione em **Authorized redirect URIs**:

`https://SEU-SERVICO.onrender.com/auth/google/callback`

Se depois você usar domínio próprio, adicione também:

`https://SEU-DOMINIO/auth/google/callback`

Você **não precisa** criar `PUBLIC_BASE_URL` no Render. O backend usa automaticamente a variável oficial `RENDER_EXTERNAL_URL` para montar o callback HTTPS. Se um dia quiser forçar um domínio próprio, você pode criar `PUBLIC_BASE_URL=https://seu-dominio.com` manualmente nas variáveis do serviço.

### Formato dos dois usuários permitidos

Em `ALLOWED_GOOGLE_EMAILS`:

`email1@gmail.com,email2@gmail.com`

Sem espaços é o formato mais simples.

## 4. Inicialização automática

O `start.sh` executa `python init_db.py` antes do Gunicorn. Esse processo:

- cria as tabelas caso ainda não existam;
- importa os leads iniciais apenas quando a tabela de leads está vazia;
- não apaga metas, reuniões, contratos, usuários ou alterações existentes.

Depois inicia:

`gunicorn app:app`

na porta fornecida pelo Render.

## 5. Health check

O Render consulta:

`/api/health`

O endpoint testa também uma consulta real ao banco. Se o PostgreSQL estiver indisponível, retorna HTTP 503 em vez de dizer falsamente que o sistema está saudável.

## Atenção ao plano gratuito

O Web Service Free pode adormecer após período sem tráfego. O PostgreSQL Free do Render atualmente expira depois de 30 dias. Para usar este CRM como sistema permanente da empresa, faça upgrade do **banco PostgreSQL** antes do vencimento ou use outro PostgreSQL persistente e coloque sua URL em `DATABASE_URL`.

Não use SQLite no Web Service Free para dados reais: o filesystem do serviço é efêmero e o arquivo pode desaparecer em restart, spin-down ou novo deploy.


## Blueprint de produção opcional

O arquivo `render-production.yaml` é uma alternativa para uso permanente com Web Service Starter e PostgreSQL Basic. Ele pode gerar cobrança. Para usá-lo, crie o Blueprint escolhendo esse arquivo como **Blueprint Path**. O `render.yaml` padrão continua configurado para os planos gratuitos.
