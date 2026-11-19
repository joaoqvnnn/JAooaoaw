# BELLAMY — Bot Telegram

## Deploy rápido no Render (mobile)

1. Suba todos os arquivos no GitHub (novo repositório).
2. No Render → **New** → **Blueprint** → conecte o repositório → escolha `render.yaml`.
   Ou: **New → Web Service** + **New → PostgreSQL** manualmente.
3. Preencha as variáveis de ambiente com os valores reais.
4. Após o deploy, copie a URL pública (ex.: `https://bellamy-bot.onrender.com`)
   e cole em `WEBHOOK_URL` (sem barra no final).
5. Faça redeploy para o webhook registrar.

## ⚠️ Configuração OBRIGATÓRIA do bot nos espaços

Para a **liberação automática de acesso** funcionar (via `chat_member`):

1. Adicione o bot como **Administrador** do **Canal oficial** e do **Grupo oficial**.
2. Conceda as permissões mínimas: "Convidar usuários" + "Gerenciar membros".
3. Sem isso, o Telegram **não envia** o evento `chat_member` e o bot não detecta a entrada.
4. Envie `/start` no canal/grupo uma vez para o bot se registrar.

## Estrutura de arquivos

- `main.py` — entrada + servidor webhook
- `config.py` — variáveis de ambiente
- `database.py` — modelos e helpers (User, UserState, Setting)
- `texts.py` — textos padrão + helper de renderização
- `keyboards.py` — teclados inline
- `handlers_start.py` — `/start`, verificação de acesso, `chat_member`
- `handlers_menu.py` — navegação do menu principal, `/cancelar`

## Comandos

- `/start` — entrada
- `/cancelar` — cancela operação em andamento
