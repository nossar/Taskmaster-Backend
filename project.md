# Pré-projeto — Todo List Avançado (Backend / API)

## Visão Geral

API REST de gerenciamento de tarefas, desenvolvida em **Django + Django REST Framework**, sem HTML, CSS ou JavaScript.
Cada usuário autenticado terá acesso apenas aos próprios dados (listas, tarefas e subtarefas), via autenticação JWT (access + refresh token).

O frontend (repositório separado, em HTML/CSS/TypeScript) consumirá esta API para montar a interface, incluindo o dashboard inicial e a página do usuário.

---

# Funcionalidades Principais (Backend)

- Cadastro de usuário
- Login (emissão de token JWT)
- Logout (invalidação/descarte de token)
- Recuperação de senha (esqueci minha senha, via e-mail)
- **Página do usuário**: visualização e edição dos dados da conta
- **Troca de senha** (usuário autenticado, a partir da própria página do usuário)
- CRUD de listas
- CRUD de tarefas
- CRUD de subtarefas
- Prioridade de tarefas
- Datas de planejamento e entrega
- Endpoints de resumo (dados agregados para o dashboard do frontend)
- Filtros e ordenação via query params
- Documentação via Swagger
- Permissões: dados sempre isolados por usuário (`request.user`)

---

# Models

## User (Django padrão)

- username
- email
- password

## TaskList

Representa grupos de tarefas.

- owner (User)
- name
- description
- created_at
- color

## Task

Tarefa principal do sistema.

- owner (User)
- task_list
- title
- description
- priority
- status
- due_date
- planned_date
- created_at
- updated_at

## SubTask

Etapas menores de uma tarefa.

- task
- title
- done

> Nenhum model novo é necessário para a página do usuário ou troca de senha — ambas operam sobre o model `User` padrão do Django.

---

# Endpoints / ViewSets

## Autenticação e Conta

| Método | Rota | Descrição |
|---|---|---|
| POST | `/api/auth/register/` | Cria novo usuário |
| POST | `/api/token/` | Login — retorna `access` + `refresh` |
| POST | `/api/token/refresh/` | Renova o `access` token |
| POST | `/api/auth/logout/` | Invalida o `refresh` token (blacklist) |
| POST | `/api/auth/password-reset/` | Solicita redefinição de senha por e-mail (esqueci a senha) |
| POST | `/api/auth/password-reset/confirm/` | Confirma nova senha via token recebido por e-mail |

**Implementação:** `djangorestframework-simplejwt` cobre login/refresh/logout (com blacklist), mas não inclui fluxo de recuperação de senha por e-mail. Será necessário implementar manualmente (usando `django.contrib.auth.tokens.PasswordResetTokenGenerator` + envio de e-mail via `EMAIL_*` em `settings.py`) ou usar um pacote como `django-rest-passwordreset`.

---

## Página do Usuário

| Método | Rota | Descrição |
|---|---|---|
| GET | `/api/users/me/` | Retorna os dados do usuário autenticado |
| PATCH | `/api/users/me/` | Atualiza dados da conta (ex: e-mail) |
| POST | `/api/users/me/change-password/` | Troca de senha do usuário autenticado |

A troca de senha exige usuário autenticado e deve receber `senha_atual` + `nova_senha`, diferente do fluxo de "esqueci minha senha" (que é público e baseado em e-mail). Validação da senha atual via `check_password()`, e gravação da nova via `set_password()` (nunca texto puro).

---

## CRUD de Listas (`TaskListViewSet`)

| Método | Rota | Descrição |
|---|---|---|
| GET / POST | `/api/lists/` | Lista / cria listas do usuário |
| GET / PATCH / DELETE | `/api/lists/{id}/` | Detalha / edita / remove uma lista |

## CRUD de Tarefas (`TaskViewSet`)

| Método | Rota | Descrição |
|---|---|---|
| GET / POST | `/api/tasks/` | Lista / cria tarefas |
| GET / PATCH / DELETE | `/api/tasks/{id}/` | Detalha / edita / remove uma tarefa |
| POST | `/api/tasks/{id}/toggle/` | Marca como concluída ou pendente |

## CRUD de Subtarefas (`SubTaskViewSet`)

| Método | Rota | Descrição |
|---|---|---|
| GET / POST | `/api/subtasks/` | Lista / cria subtarefas |
| PATCH / DELETE | `/api/subtasks/{id}/` | Edita / remove subtarefa |
| POST | `/api/subtasks/{id}/toggle/` | Marca subtarefa como feita |

---

## Endpoints de Resumo (suporte ao Dashboard do Frontend)

O backend não monta a interface do dashboard (isso é responsabilidade do frontend), mas fornece os dados agregados que ela vai consumir:

| Método | Rota | Descrição |
|---|---|---|
| GET | `/api/dashboard/summary/` | Contagens: pendentes, vencidas, para hoje, concluídas na semana |
| GET | `/api/dashboard/upcoming/` | Tarefas vencidas, próximas do prazo e de alta prioridade |
| GET | `/api/lists/` | Já retorna contagem de tarefas pendentes por lista (campo calculado) |

---

## Filtros e Views Extras

| Método | Rota | Descrição |
|---|---|---|
| GET | `/api/tasks/today/` | Tarefas planejadas para hoje |
| GET | `/api/tasks/late/` | Tarefas vencidas |
| GET | `/api/tasks/completed/` | Tarefas concluídas |
| GET | `/api/tasks/?ordering=priority` | Tarefas ordenadas por prioridade |

---

# Gerência de Usuário

- Todo objeto pertence a um usuário (`owner`).
- Autenticação via JWT (`Authorization: Bearer <access_token>`).
- Queryset sempre filtrado por `request.user` em cada ViewSet — nenhum usuário acessa dados de outro.
- Edição e exclusão restritas aos próprios dados.
- Endpoint de troca de senha e perfil acessível apenas com token válido.

Exemplo:

```python
def get_queryset(self):
    return Task.objects.filter(owner=self.request.user)
```