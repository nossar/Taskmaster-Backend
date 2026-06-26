# Trabalho 2 — API Backend do Taskmaster (INF1407)

## Integrantes do Grupo
* **Luiz Felipe Neves**: — *2311024*
* **Matheus Nossar**: — *Placeholder*

---

## 🚀 Visão Geral e Escopo do Projeto

O **Taskmaster Backend** é uma API REST robusta desenvolvida em **Django** utilizando o **Django REST Framework (DRF)**. O principal objetivo do sistema é fornecer uma API de gerenciamento de tarefas (Todo List Avançado), permitindo o isolamento total de dados entre usuários cadastrados.

Este backend **não contém códigos HTML, CSS ou JavaScript**, sendo projetado estritamente para ser consumido por um cliente Frontend em repositório e hospedagem separados.

### Características Principais
* **Isolamento de Dados**: Cada usuário autenticado tem sua visão exclusiva do site, acessando e manipulando apenas as suas próprias Listas, Tarefas e Subtarefas.
* **Autenticação JWT**: Login seguro com controle de sessão por tokens Access/Refresh (`django-rest-framework-simplejwt`) e invalidação de tokens no Logout (Blacklist).
* **Gestão de Senha**: Fluxo completo de troca de senha direta e recuperação de senha ("esqueci minha senha") enviando e-mail com token temporário.
* **CRUD Completo**: Operações de criação, leitura, atualização e exclusão em banco de dados para Listas de Tarefas, Tarefas e Subtarefas.
* **Painel / Dashboard**: Endpoints com dados consolidados agregando status das tarefas (pendentes, concluídas, atrasadas, próximas da data limite).
* **Swagger/OpenAPI**: Documentação viva e interativa da API exposta via Swagger UI (`drf-spectacular`).

---

## 🔗 Links do Projeto

* **Repositório do Frontend**: https://github.com/luizfneves404/taskmaster-frontend
* **Repositório do Backend**: https://github.com/nossar/Taskmaster-Backend
* **Site Publicado (Frontend)**: https://taskmaster-frontend.pages.dev
* **Site Publicado (Backend/API)**: https://taskmaster-backend-2p03.onrender.com

---

## 🛠️ Tecnologias Utilizadas

* **Framework Principal**: [Django 6.x](https://www.djangoproject.com/)
* **Camada de API**: [Django REST Framework (DRF)](https://www.django-rest-framework.org/)
* **Autenticação**: SimpleJWT (JSON Web Token)
* **Documentação**: OpenAPI 3 + `drf-spectacular` (Swagger UI)
* **Serviço de E-mail**: Anymail (com provedor Resend para produção) e Console backend em desenvolvimento
* **Arquivos Estáticos (Swagger UI)**: WhiteNoise (servindo assets estáticos de forma eficiente)
* **Banco de Dados**: PostgreSQL (Produção) / SQLite (Desenvolvimento)
* **Gerenciador de Pacotes**: `uv` (rápido e moderno) ou `pip` tradicional

---

## 📦 Instalação e Execução Local

Siga os passos abaixo para configurar e executar o backend em sua máquina local.

### 1. Clonar o Repositório
```bash
git clone https://github.com/.../Taskmaster-Backend.git
cd Taskmaster-Backend
```

### 2. Configurar as Variáveis de Ambiente
Copie o arquivo `.env.example` para `.env` e ajuste as variáveis necessárias:
```bash
cp .env.example .env
```
Variáveis principais no `.env`:
* `SECRET_KEY`: Chave secreta de criptografia do Django.
* `DEBUG`: Defina como `True` para ambiente local.
* `DATABASE_URL`: Deixe em branco para usar SQLite local (`db.sqlite3`), ou insira a string de conexão PostgreSQL.
* `FRONTEND_URL`: URL do cliente frontend (usada para montar links de e-mail de redefinição de senha). Padrão: `http://localhost:5173`.
* `RESEND_API_KEY`: Necessário em ambiente de produção (DEBUG=False) para envio de e-mails via Resend.

### 3. Instalar Dependências e Ativar Ambiente Virtual
Se estiver usando o gerenciador **`uv`** (recomendado):
```bash
uv sync
```
Caso queira utilizar o **`pip`** e virtualenv tradicional:
```bash
python -m venv .venv
source .venv/bin/activate  # No Windows: .venv\Scripts\activate
pip install -e .
```

### 4. Executar Migrações do Banco de Dados
```bash
uv run manage.py migrate
# Ou se estiver usando o venv ativado:
python manage.py migrate
```

### 5. Criar Usuário Administrador (Opcional)
Crie um superusuário para acessar o painel de administração nativo do Django (`/admin/`):
```bash
uv run manage.py createsuperuser
# Ou se estiver usando o venv ativado:
python manage.py createsuperuser
```

### 6. Executar os Testes Automatizados
O projeto conta com uma suite completa de testes. Certifique-se de que tudo está verde:
```bash
uv run manage.py test
# Ou se estiver usando o venv ativado:
python manage.py test
```

### 7. Iniciar o Servidor de Desenvolvimento
```bash
uv run manage.py runserver
# Ou se estiver usando o venv ativado:
python manage.py runserver
```
O backend estará disponível em `http://127.0.0.1:8000/`. A documentação do Swagger UI estará acessível em `http://127.0.0.1:8000/api/docs/`.

---

## 📖 Manual do Usuário e Estrutura de Endpoints (API)

A API do **Taskmaster** é totalmente documentada pelo Swagger. Abaixo está o resumo das principais rotas, métodos e comportamentos esperados de cada uma:

### 🔑 Autenticação e Registro

* `POST /api/auth/register/` (Público): Cria uma nova conta informando `username`, `email` e `password`.
* `POST /api/token/` (Público): Realiza o login. Exige `username` e `password` e retorna os tokens JWT `access` e `refresh`.
* `POST /api/token/refresh/` (Público): Renova o `access` token utilizando o `refresh` token.
* `POST /api/auth/logout/` (Autenticado): Envia o `refresh` token para a blacklist, invalidando a sessão.

### 👤 Gestão do Perfil e Senha

* `GET /api/users/me/` (Autenticado): Retorna as informações do usuário logado.
* `PATCH /api/users/me/` (Autenticado): Atualiza dados parciais do perfil (como o endereço de e-mail).
* `POST /api/users/me/change-password/` (Autenticado): Altera a senha do usuário autenticado. Exige a `current_password` (senha atual) e `new_password` (nova senha).
* `POST /api/auth/password-reset/` (Público): Solicita a redefinição de senha via e-mail. Se o e-mail existir, envia um link com um token gerado temporariamente.
* `POST /api/auth/password-reset/confirm/` (Público): Confirma a nova senha utilizando o `uid`, `token` (recebidos por e-mail) e a `new_password`.

### 📋 Listas de Tarefas (`TaskList`)

* `GET /api/lists/` (Autenticado): Lista as coleções de tarefas pertencentes ao usuário autenticado. Retorna também o cálculo de quantas tarefas estão pendentes na lista (`pending_count`).
* `POST /api/lists/` (Autenticado): Cria uma lista. Atribui automaticamente o `user` criador.
* `GET /api/lists/{id}/` (Autenticado): Detalhes de uma lista.
* `PATCH /api/lists/{id}/` / `PUT /api/lists/{id}/` (Autenticado): Atualiza uma lista.
* `DELETE /api/lists/{id}/` (Autenticado): Exclui a lista de tarefas e todas as tarefas dependentes.

### 📝 Tarefas (`Task`)

* `GET /api/tasks/` (Autenticado): Lista as tarefas do usuário autenticado. Suporta ordenação via query params (`?ordering=priority`, `?ordering=-due_date`, etc.).
* `POST /api/tasks/` (Autenticado): Cria uma nova tarefa vinculando-a a uma lista válida do usuário.
* `GET /api/tasks/{id}/` (Autenticado): Detalha uma tarefa específica.
* `PATCH /api/tasks/{id}/` / `PUT /api/tasks/{id}/` (Autenticado): Atualiza a tarefa.
* `DELETE /api/tasks/{id}/` (Autenticado): Remove a tarefa.
* `POST /api/tasks/{id}/toggle/` (Autenticado): Alterna de forma rápida o status da tarefa entre concluído (`done`) e pendente (`pending`).

#### ⚡ Filtros Rápidos
* `GET /api/tasks/today/`: Filtra tarefas planejadas ou com data de vencimento marcadas para o dia de hoje.
* `GET /api/tasks/late/`: Filtra tarefas não finalizadas cuja data de vencimento (`due_date`) já expirou.
* `GET /api/tasks/completed/`: Filtra todas as tarefas já marcadas como concluídas pelo usuário.

### 📌 Subtarefas (`SubTask`)

* `GET /api/subtasks/` / `POST /api/subtasks/` (Autenticado): Lista e cria subtarefas vinculadas a tarefas do usuário.
* `PATCH /api/subtasks/{id}/` / `DELETE /api/subtasks/{id}/` (Autenticado): Atualiza ou exclui subtarefas.
* `POST /api/subtasks/{id}/toggle/` (Autenticado): Marca/desmarca a subtarefa como feita (`done`).

### 📊 Dashboard

* `GET /api/dashboard/summary/` (Autenticado): Estatísticas quantitativas resumidas (`pending`, `overdue`, `today`, `completed_week`).
* `GET /api/dashboard/upcoming/` (Autenticado): Lista consolidada de tarefas importantes (atrasadas, que vencem nos próximos 7 dias e de alta prioridade), deduplicadas e limitadas às 10 mais urgentes.

---

## 📈 Relato de Testes (O que Funcionou / O que Não Funcionou)

Para garantir a confiabilidade e robustez de todas as implementações exigidas no trabalho, foi desenvolvido um conjunto rigoroso de **51 testes automatizados**, abrangendo cenários de sucesso, falha e regras de segurança.

### ✅ O que Funcionou e foi Testado
* **Segurança e Isolamento Rígido**: Testado exaustivamente que usuários não autorizados não conseguem visualizar, criar, atualizar ou excluir listas, tarefas ou subtarefas que pertençam a outro usuário (retorna erro HTTP `404 Not Found` ou `403 Forbidden`).
* **Autenticação JWT Completa**: Cadastro, login (emissão de tokens), renovação via token refresh, e logout com blacklist testados com sucesso.
* **Operações de CRUD**: Todas as 4 operações básicas em banco de dados para Listas, Tarefas e Subtarefas funcionando 100% integradas.
* **Dashboard e Filtros**: Agregação de contadores para o painel principal, filtragem de tarefas do dia, atrasadas, concluídas e ordenamento flexível.
* **Fluxo de Recuperação e Troca de Senhas**: A redefinição de senhas com token por e-mail (usando backend em console em ambiente de dev) e a troca de senha ativa no perfil funcionam sem falhas.
* **Documentação Swagger**: Rota `/api/docs/` carrega a interface OpenAPI interativa perfeitamente, com descrição detalhada de todos os payloads de requisição e resposta.
* **Status da Suite de Testes**: **51 de 51 testes passando com status OK** no backend.

---

## 📸 Imagens da Aplicação

Abaixo estão capturas de tela demonstrando 3 telas do aplicativo:

![Screenshot from 2026-06-26 10-56-25](docs/Screenshot%20from%202026-06-26%2010-56-25.png)
![Screenshot from 2026-06-26 10-56-34](docs/Screenshot%20from%202026-06-26%2010-56-34.png)
![Screenshot from 2026-06-26 10-56-42](docs/Screenshot%20from%202026-06-26%2010-56-42.png)
