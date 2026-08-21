# LM TECH CRM

CRM comercial para gestão de leads jurídicos, reuniões, contratos, metas e desempenho por usuário.

## Stack

- Flask
- Flask-SQLAlchemy
- PostgreSQL no Render
- Gunicorn
- Google OAuth

## Recursos

- Base compartilhada de leads
- Reuniões vinculadas aos leads
- Contratos vinculados aos leads
- Contrato fechado soma automaticamente no realizado da meta mensal
- Metas de faturamento, contratos e reuniões
- Metas por equipe e por usuário
- Histórico de atividades
- Controle de desempenho dos usuários
- Login Google limitado pelos e-mails permitidos
- Seed automático dos leads existentes

## Render

Use `render.yaml`. Veja `RENDER-DEPLOY.md`.

O startup espera o PostgreSQL ficar disponível antes de iniciar o Gunicorn, evitando falha por corrida entre criação do banco e inicialização do Web Service.
