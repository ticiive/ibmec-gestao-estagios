# API IBMEC Estágios — Visão Geral

A API IBMEC Estágios é o back-end REST que sustenta o Sistema de Gestão e Mediação de Estágios Obrigatórios do IBMEC. Construída em Django + Django REST Framework, ela expõe os recursos necessários para que alunos, coordenadores, supervisores de empresa e administradores conduzam todo o ciclo de vida do estágio obrigatório — da abertura da solicitação ao encerramento — com regras de negócio acadêmicas centralizadas, controle de acesso por papel e documentação OpenAPI gerada automaticamente a partir do código.

## Stack tecnológica

| Componente | Versão | Função no projeto |
| -- | -- | -- |
| Python | 3.9+ | Linguagem base do back-end |
| Django | 4.2.30 LTS | Framework web, ORM e administração |
| djangorestframework | 3.16.1 | Camada REST (ViewSets, Serializers, Routers, Token Auth) |
| drf-spectacular | 0.29.0 | Geração de schema OpenAPI 3 e Swagger/Redoc |
| django-cors-headers | 4.9.0 | CORS controlado para o front-end consumir a API |
| python-dotenv | 1.0.1 | Carrega variáveis de ambiente do `.env` em desenvolvimento |
| reportlab | 4.2.2 | Geração de PDFs (TCE, Termo de Realização, Relatório de Estágio) |
| PyPDF2 | 3.0.1 | Score de conformidade de documentos enviados |
| django-allauth | 65.14.3 | Carcaça OAuth Microsoft (fora do escopo desta entrega) |
| SQLite | embarcado | Banco de desenvolvimento local |
| MySQL | 8.x | Banco relacional alvo em produção (definido no DAS) |

## Arquitetura em camadas

O fluxo de uma requisição HTTP percorre uma sequência clara de camadas, cada uma com responsabilidade única:

```text
+--------------------------------------------------------------+
|                      Cliente HTTP                            |
|   (Swagger UI, Postman, front-end React, scripts)            |
+--------------------------------------------------------------+
                              |
                              v
+--------------------------------------------------------------+
|       Routing — djangotutorial/app/api_urls.py               |
|   DefaultRouter registra 10 ViewSets + 6 endpoints diretos   |
|   (3 auth básicos + esqueci/redefinir senha + avaliar empresa)|
|   e mais 7 rotas dedicadas (PDFs, formulário e dashboards).  |
+--------------------------------------------------------------+
                              |
                              v
+--------------------------------------------------------------+
|       Permissions — djangotutorial/app/permissions.py        |
|   IsAuthenticated, IsAdminOrReadOnly, IsAluno,               |
|   IsCoordenador, IsSupervisorEmpresa, IsDonoDoProcesso;      |
|   helpers is_admin / is_administrativo / has_global_access   |
|   cobrem os 4 tipos administrativos (reitor, pro_reitor,     |
|   secretaria, casa, carreiras) com visão global read-only.   |
+--------------------------------------------------------------+
                              |
                              v
+--------------------------------------------------------------+
|       ViewSet — djangotutorial/app/views.py                  |
|   get_queryset() filtra por papel; @action customiza ações;  |
|   perform_create() injeta dono/coordenador automaticamente   |
+--------------------------------------------------------------+
                              |
              +---------------+---------------+
              v                               v
+----------------------------+   +------------------------------+
|  Serializer (DRF)          |   |  State Machine               |
|  app/serializers.py        |   |  app/state_machine.py        |
|  Valida payload, expõe DTO |   |  Mapa puro de transições     |
+----------------------------+   +------------------------------+
              |                               |
              +---------------+---------------+
                              v
+--------------------------------------------------------------+
|       Models / ORM — djangotutorial/app/models.py            |
|   Núcleo de atores e domínio:                                |
|     Usuario, Curso, EmpresaConcedente, Aluno, Coordenador,   |
|     SupervisorEmpresa, ProcessoEstagio, DocumentoProcesso    |
|   Auditoria, formulário dinâmico e avaliação:                |
|     LogDocumento, ModeloFormulario, AvaliacaoEmpresa,        |
|     HistoricoStatusProcesso, TemplateDocumento               |
+--------------------------------------------------------------+
                              |
                              v
+--------------------------------------------------------------+
|       Banco de dados (SQLite em dev, MySQL em produção)      |
+--------------------------------------------------------------+
```

- **Cliente HTTP** — qualquer consumidor que fale JSON sobre HTTP. Durante o desenvolvimento, o Swagger UI hospedado pelo próprio Django já cobre a maioria dos testes manuais.
- **Routing** — o `DefaultRouter` do DRF traduz URLs em ações de ViewSet (`list`, `retrieve`, `create`, `update`, `destroy`) e expõe `@action` extras como `alterar_status` e `documentos`.
- **Permissions** — antes de qualquer linha de lógica rodar, as classes de permissão garantem que o usuário está autenticado e que tem o papel adequado para o método HTTP solicitado.
- **ViewSet** — orquestra a operação. Filtra o queryset conforme o papel (RBAC implícito no `get_queryset`), escolhe o serializer adequado e injeta campos derivados em `perform_create`.
- **Serializer** — atua como DTO de entrada e saída: valida campos, aplica regras de negócio declarativas (ex.: justificativa obrigatória ao rejeitar, RN11) e serializa modelos em JSON.
- **State Machine** — módulo Python puro com o mapa de transições válidas. Não conhece Django; é importado pelo ViewSet/Serializer para garantir que mudanças de status sigam o fluxo desenhado.
- **Models / ORM** — define as entidades persistentes e os relacionamentos. O ORM do Django funciona como um repositório implícito.
- **Banco de dados** — SQLite em desenvolvimento local; o DAS prevê MySQL relacional em produção.

## Padrões aplicados

1. **MVT (Model–View–Template) adaptado para API** — variação Django do MVC clássico. A camada de "Template" é substituída pelo Serializer, que transforma os Models em representações JSON consumidas pelos clientes.
2. **DTO via Serializers DRF** — cada recurso tem um serializer dedicado (`ProcessoEstagioSerializer`, `CriarProcessoSerializer`, `AlterarStatusSerializer`) que define explicitamente os campos expostos, isolando o modelo de domínio do contrato externo.
3. **State Machine pattern** — o módulo `state_machine.py` mantém o mapa de transições válidas como dado puro. O ViewSet consulta `transicoes_validas(status_atual)` antes de qualquer mudança, evitando estados ilegais.
4. **RBAC (Role-Based Access Control)** — três papéis operacionais (`aluno`, `coordenador`, `supervisor_empresa`), um perfil técnico (`admin` via `is_staff`/`is_superuser`) e quatro perfis administrativos com visão global read-only (`reitor`, `pro_reitor`, `secretaria`, `casa`, `carreiras`) determinam o que cada usuário vê e pode fazer. As classes em `permissions.py`, os helpers `is_administrativo` / `has_global_access` e os filtros em `get_queryset` aplicam essa política em toda chamada.
5. **Repository implícito via ORM do Django** — em vez de uma camada de repositório explícita, o `QuerySet` do Django atua como repositório, com `select_related` reduzindo o N+1 nas leituras compostas.
6. **Defensive programming (fail-fast, negação por default)** — quando o `get_queryset` não consegue identificar o papel do usuário, o retorno é `.none()` em vez de `.all()`. Em caso de dúvida, a API nega o acesso.
7. **Separation of Concerns** — modelagem fica em `models.py`, validação em `serializers.py`, autorização em `permissions.py`, orquestração em `views.py` e regras de transição em `state_machine.py`. Cada arquivo tem um motivo único para mudar.

## Documentação automática

A API descreve a si mesma graças ao `drf-spectacular`. Três endpoints são gerados automaticamente a partir dos ViewSets, Serializers e docstrings do código — não há schema mantido à mão:

| Endpoint | O que entrega |
| -- | -- |
| `/api/docs/` | Swagger UI interativo — explorar e testar requisições direto do navegador |
| `/api/redoc/` | Redoc — leitura linear, ótimo para consumo por terceiros |
| `/api/schema/` | JSON OpenAPI 3 bruto — fonte para gerar clientes em outras linguagens |

Sempre que um campo de serializer ou uma docstring de ViewSet muda, os três endpoints refletem a alteração no próximo request. **A documentação interativa é a fonte de verdade dos schemas**; este conjunto de Markdown explica o "porquê" e o "como", não substitui o Swagger.

## Convenções da API

Algumas convenções valem para todos os recursos e ajudam a entender as respostas:

- **Formato** — todos os corpos de requisição e resposta usam JSON com `Content-Type: application/json`. Uploads de arquivo usam `multipart/form-data`.
- **Autenticação** — token DRF no header `Authorization: Token <chave>`. Sem token, qualquer rota protegida responde `401 Unauthorized`.
- **Datas** — formato ISO 8601 (`YYYY-MM-DD` para datas simples, `YYYY-MM-DDTHH:MM:SSZ` para timestamps em UTC).
- **Paginação** — listagens seguem o padrão DRF com `count`, `next`, `previous` e `results`. O cliente passa `?page=N` para navegar.
- **Status codes** — `200` para leitura, `201` para criação, `204` para `DELETE`, `400` para erro de validação, `401` sem auth, `403` sem papel, `404` quando o recurso não está visível ao usuário.
- **Identificadores** — todos os recursos usam `id` numérico autoincrementado pelo banco.

## Status atual da entrega

A documentação reflete o estado do backend após a consolidação de várias PRs (núcleo do `ProcessoEstagio`, autenticação por email, documentos, formulário dinâmico, dashboard, avaliação anônima, fluxo de senha por email). A fonte de verdade dos schemas de payload continua sendo o Swagger UI em `/api/docs/`, gerado automaticamente.

Pronto nesta entrega:

- **13 models** persistentes — núcleo (`Usuario`, `Curso`, `EmpresaConcedente`, `Aluno`, `Coordenador`, `SupervisorEmpresa`, `ProcessoEstagio`, `DocumentoProcesso`) + auditoria/dinâmico (`LogDocumento`, `ModeloFormulario`, `AvaliacaoEmpresa`, `HistoricoStatusProcesso`, `TemplateDocumento`).
- **Autenticação por token DRF com email institucional** (`USERNAME_FIELD = email_institucional`). Endpoints: `register`, `login`, `logout`, `esqueci-senha`, `redefinir-senha`. O cadastro pelo SPA está desativado — usuários são criados via seed/admin/registro programático.
- **9 tipos de usuário** no campo `Usuario.tipo`: `aluno`, `coordenador`, `supervisor_empresa`, `secretaria`, `casa`, `reitor`, `pro_reitor`, `carreiras` (os cinco últimos têm visão global read-only via `is_administrativo`/`has_global_access`). `admin` continua sendo `is_staff=True` / `is_superuser=True`, fora do campo `tipo`.
- **10 ViewSets ModelViewSet** expostos via `DefaultRouter`, com filtros por papel em `get_queryset`: cursos, empresas, alunos (List/Detail com proteção LGPD para CPF/RG), coordenadores, supervisores, documentos, processos-estagio, modelos-formulario, avaliacoes-empresa, templates-documentos.
- **Máquina de estados pura** cobrindo 8 status e suas transições válidas, com `HistoricoStatusProcesso` gravado a cada `alterar_status`.
- **Endpoints de PDF** — `gerar-tce`, `gerar-termo-realizacao`, `gerar-relatorio` (todos via `reportlab`).
- **Avaliação dinâmica do estágio pelo aluno** — `preencher-formulario` (gera PDF a partir das respostas + `ModeloFormulario` configurável pelo coordenador).
- **Dashboard agregado** — `/api/dashboard/processos/`, `/api/dashboard/estatisticas/` (gráficos por seção do formulário) e `/api/dashboard/empresas/` (média de estrelas, top comentários anônimos).
- **Avaliação anônima de empresa** — `POST /api/avaliar-empresa/` registra `AvaliacaoEmpresa` com `aluno=None`/`processo=None`.
- **Reset de senha por email** — `esqueci-senha` envia link com token (`PasswordResetTokenGenerator`); deep link `/redefinir-senha/?uid=&token=` serve o SPA.
- **CORS configurado** e Swagger UI / Redoc / schema OpenAPI 3 servidos automaticamente.

Fora do escopo desta entrega: integração OAuth Microsoft (Azure AD), implementação de `RN06` (análise NLP de atividades vs curso), implementação de `RN04` (controle de tempo máximo em uma mesma empresa) e atalhos `meu_perfil/` para aluno/supervisor — esses perfis usam a listagem filtrada por papel em `/api/alunos/` e `/api/supervisores-empresa/`. A lista completa está em [Endpoints](endpoints.md#fora-do-escopo-desta-entrega).

## Como rodar localmente

Para subir a API em desenvolvimento, a partir da raiz do repositório:

```bash
cd djangotutorial
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # opcional — só se quiser SECRET_KEY próprio ou SMTP
python manage.py migrate
python manage.py seed_completo --force   # popula 70 alunos + 7 cursos + 6 empresas
python manage.py runserver
```

Com o servidor de pé em `http://localhost:8000`, o Swagger UI fica em `http://localhost:8000/api/docs/` e o admin Django em `http://localhost:8000/admin/`. O banco SQLite (`db.sqlite3`) é criado automaticamente no primeiro `migrate`. Para popular o ambiente com dados de teste há duas opções:

- **`python manage.py seed_completo --force`** — comando management que cria 70 alunos distribuídos por 7 cursos, 6 empresas com supervisores, 70 processos com status variados e 210 documentos. Cada aluno tem senha `senha123` e email `<slug>@aluno.ibmec.edu.br`. O superuser fica em `admin@ibmec.edu.br` / `admin`.
- **`python3 populate_db.py`** — script standalone equivalente, mais antigo, mantido por compatibilidade.

Detalhes completos de instalação (incluindo variáveis de ambiente para SMTP em produção e como rodar a suíte de testes) estão no `README.md` na raiz do repositório.

## Navegação da subseção

- [Autenticação](autenticacao.md) — fluxo de registro, login e uso do token DRF.
- [Endpoints](endpoints.md) — referência tabular completa dos recursos REST.
- [Regras de Negócio](regras-negocio.md) — onde cada RN está implementada no código.
- [Máquina de Estados](state-machine.md) — diagrama e tabela das transições do `ProcessoEstagio`.
- [Exemplos de Uso](exemplos.md) — fluxos completos com `curl` e payloads reais.
- [Códigos de Erro](erros.md) — catálogo de respostas 4xx/5xx e como tratá-las.

## Autor(es)

| Data | Versão | Descrição | Autor(es) |
| -- | -- | -- | -- |
| 28/05/2026 | 1.0 | Criação do documento | João Gabriel Teodósio |
