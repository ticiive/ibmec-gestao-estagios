# Autenticação

A API IBMEC Estágios utiliza autenticação por **token** baseada em `rest_framework.authtoken` (DRF Token Authentication). Não há sessão, nem cookie, nem CSRF: cada cliente obtém um token via login e o envia no header `Authorization` em todas as requisições subsequentes. O token é opaco, persistente até logout, e está vinculado a um único `Usuario`.

O campo de identidade é **`email_institucional`** (`Usuario.USERNAME_FIELD = 'email_institucional'`): tanto o login quanto a redefinição de senha são endereçados por email. O campo `username` continua existindo no schema (exigência do `AbstractUser`), mas é sincronizado automaticamente com o email pelo `Usuario.save()` quando vazio — clientes não devem manipulá-lo.

## Visão geral

Pseudo-fluxo do ciclo de autenticação:

```
Cliente ─► POST /api/auth/login/        ─► 200 { token, id, tipo, nome, email }
                                                │
                                                ▼
Cliente ─► (toda request seguinte)
           Header: Authorization: Token <key>
                                                │
                                                ▼
Cliente ─► POST /api/auth/logout/       ─► 200 { mensagem }
           (invalida o token atual)

# Esqueci minha senha — fluxo paralelo:
Cliente ─► POST /api/auth/esqueci-senha/    ─► 200 (mensagem genérica)
                                                │
                                                ▼ email com link
                                  http://.../redefinir-senha/?uid=&token=
                                                │
                                                ▼
Cliente ─► POST /api/auth/redefinir-senha/  ─► 200 { mensagem }
```

Enquanto o token estiver válido, ele é a credencial única do cliente. Não há expiração automática; a invalidação acontece em `logout` ou por ação administrativa.

> **Cadastro pelo SPA desativado.** A criação de usuários comuns é feita via seed (`python manage.py seed_completo --force`) ou via admin Django. O endpoint `POST /api/auth/register/` continua existindo para suportar fluxos administrativos (ex: cadastro de empresa por aluno, que cria automaticamente um `SupervisorEmpresa`), mas o botão "Cadastre-se" foi removido da tela de login para evitar criação descontrolada de contas.

## Tipos de usuário

O campo `tipo` em `Usuario` define o papel do ator no sistema. Os três primeiros (`aluno`, `coordenador`, `supervisor_empresa`) vêm acompanhados de um perfil 1:1 com FK (`Aluno`, `Coordenador`, `SupervisorEmpresa`). Os quatro últimos são perfis administrativos com **visão global read-only** — não têm tabela própria e são reconhecidos pelo helper `is_administrativo` em `permissions.py` (que junto com `is_admin` compõe `has_global_access`). Administradores técnicos continuam fora do campo `tipo`: são `Usuario` com `is_staff=True` e/ou `is_superuser=True`, criados via `python manage.py createsuperuser` ou pelo seed.

| `tipo` | Quem é | O que faz no sistema |
| --- | --- | --- |
| `aluno` | Estudante do IBMEC matriculado em estágio obrigatório | Cria/cancela processos, envia documentos, avalia a empresa de forma anônima, preenche o relatório de estágio dinâmico |
| `coordenador` | Coordenador acadêmico de um ou mais cursos | Aprova, rejeita, solicita correção, ativa e encerra processos dos alunos dos cursos sob sua coordenação; edita o `ModeloFormulario`; valida documentos |
| `supervisor_empresa` | Profissional da empresa concedente | Visualiza alunos e documentos do estágio na sua empresa em modo read-only; **não vê** `respostas_formulario` nem estatísticas agregadas (privacidade da avaliação) |
| `secretaria` | Secretaria acadêmica | Visão global read-only de todos os cursos, alunos e processos |
| `casa` | CASA (Centro Acadêmico/Serviços) | Visão global read-only |
| `reitor` | Reitoria | Visão global read-only |
| `pro_reitor` | Pró-Reitoria | Visão global read-only |
| `carreiras` | Setor de Carreiras | Visão global read-only |
| _admin_ (sem `tipo`) | `is_staff=True` ou `is_superuser=True`, criado via `createsuperuser` ou seed | Acesso total a todos os recursos e a qualquer transição da máquina de estados |

> Os perfis administrativos têm acesso de **leitura** a tudo, mas **não editam** modelos de formulário, não aprovam processos e não validam documentos. Para esses perfis, o ViewSet retorna `403 Forbidden` em qualquer ação de escrita.

## POST /api/auth/register/

Cria simultaneamente o `Usuario` e o perfil correspondente ao `tipo`, e devolve um token pronto para uso.

- **Auth requerida:** não (`AllowAny`).
- **Content-Type:** `application/json`.

### Body comum (todos os tipos)

| Campo | Tipo | Obrigatório | Observação |
| --- | --- | --- | --- |
| `tipo` | string | sim | `aluno`, `coordenador`, `supervisor_empresa`, `secretaria`, `casa`, `reitor`, `pro_reitor` ou `carreiras` |
| `email` | string (email) | sim | Identificador único de login (mapeia para `Usuario.email_institucional`). Para compatibilidade, a view também aceita `email_institucional` ou `username` no payload, mas o campo canônico é `email` |
| `password` | string | sim | Senha em texto plano (será hasheada pelo Django) |
| `nome` | string | recomendado | Nome civil do usuário |

> O campo `username` do `AbstractUser` é preenchido automaticamente com o email pelo `Usuario.save()` quando vazio; clientes **não devem** enviá-lo manualmente.

> Os tipos administrativos (`secretaria`, `casa`, `reitor`, `pro_reitor`, `carreiras`) **não exigem campos extras** — não há tabela de perfil 1:1 para eles. Para administrador técnico (`is_staff=True`), use `python manage.py createsuperuser`, não este endpoint.

### Campos extras por tipo

#### `tipo = "aluno"`

| Campo | Tipo | Obrigatório | Observação |
| --- | --- | --- | --- |
| `cpf` | string | sim | Único na base de alunos |
| `rg` | string | não | Texto livre |
| `coeficiente_rendimento` | decimal | não | Default `0` |
| `curso_id` | int (FK `Curso`) | não | Recomendado para que o sistema atribua coordenador automaticamente ao criar processo |
| `matriculado_estagio` | bool | não | Default `false` |

#### `tipo = "coordenador"`

| Campo | Tipo | Obrigatório | Observação |
| --- | --- | --- | --- |
| `departamento` | string | sim | Não pode ser vazio |

#### `tipo = "supervisor_empresa"`

| Campo | Tipo | Obrigatório | Observação |
| --- | --- | --- | --- |
| `empresa_id` | int (FK `EmpresaConcedente`) | sim | Deve referenciar empresa existente |
| `cargo` | string | não | Texto livre |

### Resposta de sucesso

`201 Created`:

```json
{
  "token": "c2f1a9d4e3b8...",
  "id": 17,
  "tipo": "aluno"
}
```

### Erros comuns

`400 Bad Request`:

```json
{ "erro": "email e password são obrigatórios." }
```

```json
{ "erro": "campo \"departamento\" é obrigatório para coordenador." }
```

```json
{ "erro": "campo \"empresa_id\" é obrigatório para supervisor_empresa." }
```

```json
{ "erro": "EmpresaConcedente não encontrada." }
```

```json
{ "erro": "tipo inválido. Opções: aluno, coordenador, supervisor_empresa, secretaria, casa, reitor, pro_reitor, carreiras" }
```

Erros de integridade de banco (`email_institucional` duplicado, `cpf` duplicado, etc.) também retornam `400` com a mensagem da exceção em `erro`.

### Exemplos curl

Aluno:

```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "tipo": "aluno",
    "email": "ana.lima@al.ibmec.edu.br",
    "password": "senha-forte-123",
    "nome": "Ana Lima",
    "cpf": "123.456.789-00",
    "curso_id": 1,
    "coeficiente_rendimento": 8.4
  }'
```

Coordenador:

```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "tipo": "coordenador",
    "email": "carlos.souza@ibmec.edu.br",
    "password": "senha-forte-123",
    "nome": "Carlos Souza",
    "departamento": "Computação"
  }'
```

Supervisor de empresa:

```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "tipo": "supervisor_empresa",
    "email": "marcia@acme.com",
    "password": "senha-forte-123",
    "nome": "Márcia Pereira",
    "empresa_id": 3,
    "cargo": "Gerente de RH"
  }'
```

Perfil administrativo (ex.: secretaria) — sem campos extras:

```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "tipo": "secretaria",
    "email": "secretaria.coord@ibmec.edu.br",
    "password": "senha-forte-123",
    "nome": "Secretaria Coordenação"
  }'
```

## POST /api/auth/login/

Autentica `email`/`password` e devolve o token persistente do usuário (cria um, se ainda não existir).

- **Auth requerida:** não (`AllowAny`).
- **Campo de identidade:** `email` (com fallback para `username` por compatibilidade). O backend resolve via `email_institucional` porque é o `USERNAME_FIELD` do `Usuario`.

### Body

```json
{
  "email": "ana.lima@al.ibmec.edu.br",
  "password": "senha-forte-123"
}
```

### Resposta de sucesso

`200 OK`:

```json
{
  "token": "c2f1a9d4e3b8...",
  "id": 17,
  "tipo": "aluno",
  "nome": "Ana Lima",
  "email": "ana.lima@al.ibmec.edu.br"
}
```

### Erro

`401 Unauthorized`:

```json
{ "erro": "Credenciais inválidas." }
```

### Exemplo curl

```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "ana.lima@al.ibmec.edu.br", "password": "senha-forte-123"}'
```

## POST /api/auth/logout/

Invalida o token do usuário autenticado, removendo-o da base. O mesmo usuário receberá outro token na próxima chamada a `login` ou `register`.

- **Auth requerida:** sim (`IsAuthenticated`).
- **Header obrigatório:** `Authorization: Token <key>`.

### Resposta de sucesso

`200 OK`:

```json
{ "mensagem": "Logout realizado com sucesso." }
```

A view captura silenciosamente o caso em que o token já foi removido, retornando a mesma mensagem.

### Exemplo curl

```bash
curl -X POST http://localhost:8000/api/auth/logout/ \
  -H "Authorization: Token c2f1a9d4e3b8..."
```

## POST /api/auth/esqueci-senha/

Solicita o envio do link de redefinição de senha por email. Use este endpoint quando o usuário esqueceu a senha e precisa recuperá-la pelo email institucional.

- **Auth requerida:** não (`AllowAny`).
- **Resposta é sempre `200 OK`**, mesmo que o email não exista na base — para não vazar quais emails estão cadastrados (mitigação contra enumeração de usuários).

### Body

```json
{ "email": "ana.lima@al.ibmec.edu.br" }
```

### Resposta

`200 OK`:

```json
{ "mensagem": "Se o email estiver cadastrado, você receberá instruções." }
```

### Comportamento interno

1. Localiza o `Usuario` por `email_institucional`. Se não existir, retorna a mesma mensagem genérica.
2. Gera um token via `django.contrib.auth.tokens.PasswordResetTokenGenerator`. O token é stateless: incorpora `last_login`, hash da senha e timestamp, e expira automaticamente após `PASSWORD_RESET_TIMEOUT` (3 dias por padrão) ou ao primeiro reset bem-sucedido.
3. Monta o link `{FRONTEND_BASE_URL}/redefinir-senha/?uid={user.pk}&token={token}` e envia por `send_mail` com `fail_silently=True` para que falhas de SMTP não vazem o estado da conta.

### Exemplo curl

```bash
curl -X POST http://localhost:8000/api/auth/esqueci-senha/ \
  -H "Content-Type: application/json" \
  -d '{"email": "ana.lima@al.ibmec.edu.br"}'
```

## POST /api/auth/redefinir-senha/

Valida o `uid`+`token` recebidos por email e troca a senha. Encerra o fluxo de "esqueci minha senha".

- **Auth requerida:** não (`AllowAny`).
- O token é invalidado pelo Django assim que a senha é alterada (porque o hash da senha é parte do payload do token).

### Body

| Campo | Tipo | Obrigatório | Observação |
| --- | --- | --- | --- |
| `uid` | int | sim | PK do `Usuario` (vem no link enviado por email) |
| `token` | string | sim | Token gerado por `PasswordResetTokenGenerator` |
| `nova_senha` | string | sim | Mínimo de 6 caracteres |

### Resposta de sucesso

`200 OK`:

```json
{ "mensagem": "Senha redefinida com sucesso." }
```

### Erros comuns

`400 Bad Request`:

```json
{ "erro": "uid, token e nova_senha são obrigatórios." }
```

```json
{ "erro": "Nova senha deve ter ao menos 6 caracteres." }
```

```json
{ "erro": "Token inválido." }
```

```json
{ "erro": "Token inválido ou expirado." }
```

### Exemplo curl

```bash
curl -X POST http://localhost:8000/api/auth/redefinir-senha/ \
  -H "Content-Type: application/json" \
  -d '{
    "uid": 17,
    "token": "c5g-3a8f1c4e9b2a4d6e9b2a",
    "nova_senha": "novasenha-forte-456"
  }'
```

## Usando o token em requests

Toda rota protegida exige o header:

```
Authorization: Token <key>
```

Note o prefixo literal `Token` (com letra maiúscula), seguido de espaço e da chave devolvida pelo `register`/`login`. Não use `Bearer`.

Exemplo de listagem de processos de estágio autenticada como aluno:

```bash
curl -X GET http://localhost:8000/api/processos-estagio/ \
  -H "Authorization: Token c2f1a9d4e3b8..." \
  -H "Accept: application/json"
```

Requisições sem o header (ou com token inválido/inexistente) retornam `401 Unauthorized`. Requisições com token válido mas sem permissão para o recurso retornam `403 Forbidden`.

## Permissões por papel (resumo)

Cada papel tem um conjunto típico de ações autorizadas pelas classes em `app/permissions.py` e pela lógica de `ProcessoEstagioViewSet`. O detalhamento por endpoint está em [`endpoints.md`](endpoints.md).

| Papel | Ações típicas |
| --- | --- |
| Aluno | Cria o próprio processo de estágio, envia documentos, preenche o relatório de estágio dinâmico, avalia a empresa (anonimamente), cancela o próprio processo enquanto estiver em `RASCUNHO`/`PENDENTE`; após `APROVADO`, o cancelamento passa pelo coordenador |
| Coordenador | Lista cursos sob sua coordenação, lista processos dos alunos desses cursos, aprova/rejeita/solicita correção/ativa/encerra esses processos, valida documentos, edita `ModeloFormulario` |
| Supervisor de empresa | Lista processos vinculados à sua `EmpresaConcedente` e consulta documentos desses processos. **Não vê** `respostas_formulario` (campo filtrado no serializer) nem o dashboard de estatísticas/empresas (`403`) — privacidade do estagiário frente à empresa avaliada |
| Perfis administrativos (`secretaria`, `casa`, `reitor`, `pro_reitor`, `carreiras`) | **Visão global read-only**: listam todos os cursos, alunos, empresas, processos e dashboards (`is_visao_global` em `permissions.py`). Qualquer ação de escrita devolve `403 Forbidden` |
| Admin (`is_staff=True`) | Acesso irrestrito a todos os recursos e a qualquer transição da máquina de estados |

## OAuth Microsoft

A carcaça do `django-allauth` (com provider Microsoft) está instalada em `mysite/settings.py` como preparação para integração futura ao Azure AD do IBMEC. Porém o App Registration correspondente não está configurado: não há `client_id`/`client_secret` válidos, nem callback registrado no portal Azure. Por isso, autenticação via conta institucional Microsoft está **fora do escopo desta entrega** — a única autenticação operacional é o fluxo Token Auth descrito acima.

## Autor(es)

| Data | Versão | Descrição | Autor(es) |
| -- | -- | -- | -- |
| 28/05/2026 | 1.0 | Criação do documento | João Gabriel Teodósio |
| 11/06/2026 | 1.1 | Auth migrado para `email_institucional`; documentação de `esqueci-senha` e `redefinir-senha`; 9 tipos de usuário; cadastro pelo SPA desativado | João Gabriel Teodósio |
