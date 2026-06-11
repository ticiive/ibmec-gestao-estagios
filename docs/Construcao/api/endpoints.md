# Endpoints da API

A API IBMEC Estágios expõe atualmente **10 ViewSets REST** registrados no `DefaultRouter` (cursos, empresas, alunos, coordenadores, supervisores-empresa, documentos, processos-estagio, modelos-formulario, avaliacoes-empresa, templates-documentos) somados a **14 endpoints diretos** (5 de auth, 2 de avaliação anônima, 4 de geração de documentos por processo, 3 de dashboard agregado). Este documento traz a referência tabular consolidada da API entregue até a data desta atualização; para os contratos de payload exatos, **a fonte de verdade é o Swagger UI em `/api/docs/`**, gerado pelo `drf-spectacular` a partir dos serializers do código.

> **Atalhos `meu_perfil/` foram descartados.** Cada papel obtém seu próprio cadastro pela listagem filtrada do ViewSet correspondente: por exemplo, `GET /api/alunos/` chamado por um aluno retorna apenas o próprio registro (filtro de queryset por papel); o mesmo vale para `coordenadores`, `supervisores-empresa` e `empresas` (via supervisor). Não há `/meu_perfil/`.

## Tabela mestre

Legenda de status: `✓ pronto` = funcional e coberto por testes · `⚠ parcial` = caminho feliz pronto, faltam validações secundárias · `✗ não implementado` = previsto para entregas futuras.

### Autenticação

| Método | URL | Quem pode | Descrição | Status |
| -- | -- | -- | -- | -- |
| POST | `/api/auth/register/` | Anônimo | Cria `Usuario` + perfil (8 tipos válidos) e devolve token DRF | ✓ pronto |
| POST | `/api/auth/login/` | Anônimo | Autentica `email`/`password`, retorna token + dados básicos | ✓ pronto |
| POST | `/api/auth/logout/` | Autenticado | Invalida o token do usuário corrente | ✓ pronto |
| POST | `/api/auth/esqueci-senha/` | Anônimo | Envia link de redefinição para o email institucional | ✓ pronto |
| POST | `/api/auth/redefinir-senha/` | Anônimo | Valida `uid`+`token` e troca a senha (mín. 6 caracteres) | ✓ pronto |

### Cursos

| Método | URL | Quem pode | Descrição | Status |
| -- | -- | -- | -- | -- |
| GET | `/api/cursos/` | Autenticado | Lista cursos (coord vê só os seus, perfis administrativos veem todos) | ✓ pronto |
| POST | `/api/cursos/` | Admin | Cria curso | ✓ pronto |
| GET | `/api/cursos/{id}/` | Autenticado | Detalha curso | ✓ pronto |
| PUT/PATCH | `/api/cursos/{id}/` | Admin | Atualiza curso | ✓ pronto |
| DELETE | `/api/cursos/{id}/` | Admin | Remove curso | ✓ pronto |

### Empresas concedentes

| Método | URL | Quem pode | Descrição | Status |
| -- | -- | -- | -- | -- |
| GET | `/api/empresas/` | Autenticado | Lista empresas (filtros `?aprovada=` e `?busca=`) | ✓ pronto |
| POST | `/api/empresas/` | Autenticado | Aluno também pode propor: cria `EmpresaConcedente` + `SupervisorEmpresa` automático + envia email com link de definição de senha para o gestor | ✓ pronto |
| GET | `/api/empresas/{id}/` | Autenticado | Detalha empresa | ✓ pronto |
| PUT/PATCH | `/api/empresas/{id}/` | Admin / Coord | Atualiza empresa | ✓ pronto |
| DELETE | `/api/empresas/{id}/` | Admin | Remove empresa | ✓ pronto |

### Cadastros (alunos, coordenadores, supervisores)

| Método | URL | Quem pode | Descrição | Status |
| -- | -- | -- | -- | -- |
| GET/POST | `/api/alunos/` | Autenticado (isolado) | Lista/cria alunos com escopo por papel; `retrieve` usa `AlunoDetailSerializer` (com CPF/RG) apenas para admin ou para o próprio aluno | ✓ pronto |
| GET/PUT/PATCH/DELETE | `/api/alunos/{id}/` | Autenticado (isolado) | CRUD por ID, respeitando isolamento | ✓ pronto |
| GET/POST | `/api/coordenadores/` | Autenticado (isolado) | Lista/cria coordenadores | ✓ pronto |
| GET/PUT/PATCH/DELETE | `/api/coordenadores/{id}/` | Autenticado (isolado) | CRUD por ID | ✓ pronto |
| GET/POST | `/api/supervisores-empresa/` | Autenticado (isolado) | Lista/cria supervisores | ✓ pronto |
| GET/PUT/PATCH/DELETE | `/api/supervisores-empresa/{id}/` | Autenticado (isolado) | CRUD por ID | ✓ pronto |

### Documentos

| Método | URL | Quem pode | Descrição | Status |
| -- | -- | -- | -- | -- |
| GET/POST | `/api/documentos/` | Autenticado (isolado) | Lista/cria documentos. Upload calcula `score_conformidade` via `score_utils.py` (PyPDF2); ≥0.8 → auto-`APROVADO` + log `APROVADO` automático | ✓ pronto |
| GET/PUT/PATCH/DELETE | `/api/documentos/{id}/` | Autenticado (isolado) | CRUD por ID | ⚠ parcial |
| POST | `/api/documentos/{id}/validar/` | Coordenador / Admin | Aprova ou rejeita documento manualmente; registra `LogDocumento` correspondente | ✓ pronto |
| GET | `/api/documentos/{id}/logs/` | Autenticado (isolado) | Histórico de ações do documento (upload, aprovação, rejeição, gerado) | ✓ pronto |

### Modelos de formulário, avaliações, templates

| Método | URL | Quem pode | Descrição | Status |
| -- | -- | -- | -- | -- |
| GET/POST | `/api/modelos-formulario/` | Coord / Admin escrevem; aluno e supervisor leem ativos | CRUD do `ModeloFormulario` por curso (JSONField `secoes` com estrutura dinâmica) | ✓ pronto |
| GET/PUT/PATCH/DELETE | `/api/modelos-formulario/{id}/` | Coord / Admin | Atualiza ou remove modelo (coord só pode editar o do próprio curso) | ✓ pronto |
| GET/POST | `/api/avaliacoes-empresa/` | Aluno cria (vinculada); coord/supervisor/administrativo leem em escopo | CRUD de `AvaliacaoEmpresa` **vinculada** (com aluno e processo). Não confundir com a avaliação anônima abaixo | ✓ pronto |
| GET/PUT/PATCH | `/api/avaliacoes-empresa/{id}/` | Autor da avaliação / leitura por escopo | Apenas o aluno autor pode editar | ✓ pronto |
| POST | `/api/avaliar-empresa/` | Aluno com processo `APROVADO`/`ATIVO`/`ENCERRADO` | **Avaliação anônima**: cria `AvaliacaoEmpresa` com `aluno=None` e `processo=None`, identidade preservada apenas via `aluno_hash` (SHA-256 com `SECRET_KEY`). Limite de 1 por aluno por empresa | ✓ pronto |
| GET | `/api/avaliar-empresa/ja-avaliei/?empresa={id}` | Aluno | Retorna `{ "ja_avaliou": bool }` para a empresa indicada | ✓ pronto |
| GET/POST | `/api/templates-documentos/` | Coord / Admin escrevem; demais leem ativos | CRUD do `TemplateDocumento` (modelo de TCE/Termo por curso) | ✓ pronto |
| GET/PUT/PATCH/DELETE | `/api/templates-documentos/{id}/` | Coord / Admin | Atualiza ou remove template | ✓ pronto |

### Processos de estágio

| Método | URL | Quem pode | Descrição | Status |
| -- | -- | -- | -- | -- |
| GET | `/api/processos-estagio/` | Autenticado (isolado) | Lista processos visíveis ao usuário; **filtra `respostas_formulario`** quando o requisitor é supervisor da empresa | ✓ pronto |
| POST | `/api/processos-estagio/` | Aluno | Abre processo (`status=PENDENTE`, coord automático pelo curso do aluno) | ✓ pronto |
| GET | `/api/processos-estagio/{id}/` | Dono / Coord / Supervisor / Admin / Administrativo | Detalha processo (também filtra `respostas_formulario` para supervisor) | ✓ pronto |
| PUT/PATCH | `/api/processos-estagio/{id}/` | Dono / Admin | Atualiza dados livres do processo | ✓ pronto |
| DELETE | `/api/processos-estagio/{id}/` | Admin | Remove processo | ✓ pronto |
| POST | `/api/processos-estagio/{id}/alterar_status/` | Conforme transição | Transição validada pela state machine + RN05 (TCE aprovado para `APROVADO→ATIVO`) + registro em `HistoricoStatusProcesso` | ✓ pronto |
| GET | `/api/processos-estagio/{id}/documentos/` | Autenticado (isolado) | Lista documentos do processo | ✓ pronto |
| GET | `/api/processos-estagio/{id}/historico/` | Autenticado (isolado) | Lista os registros de `HistoricoStatusProcesso` do processo, em ordem cronológica | ✓ pronto |
| GET | `/api/processos-estagio/{id}/gerar-tce/` | Dono / Coord / Supervisor / Admin | Gera PDF do Termo de Compromisso de Estágio (reportlab) e devolve `application/pdf` | ✓ pronto |
| GET | `/api/processos-estagio/{id}/gerar-termo-realizacao/` | Dono / Coord / Supervisor / Admin | Gera PDF do Termo de Realização | ✓ pronto |
| POST | `/api/processos-estagio/{id}/gerar-relatorio/` | Aluno (dono) | Gera PDF do relatório de estágio (parcial/final) a partir de body livre; salva como `DocumentoProcesso` salvo `preview=true` | ✓ pronto |
| POST | `/api/processos-estagio/{id}/preencher-formulario/` | Aluno (dono) | Valida respostas contra `ModeloFormulario`, salva em `respostas_formulario`, gera PDF e cria `DocumentoProcesso` | ✓ pronto |

### Dashboards agregados

| Método | URL | Quem pode | Descrição | Status |
| -- | -- | -- | -- | -- |
| GET | `/api/dashboard/processos/` | Coord / Admin / Administrativo / Supervisor | Lista processos com métricas pré-calculadas (semestre, horas totais estimadas, score médio dos documentos). Aceita filtros `?empresa=`, `?semestre=`, `?status=`, `?curso=`, `?com_respostas=` | ✓ pronto |
| GET | `/api/dashboard/estatisticas/` | Coord / Admin / Administrativo | Estatísticas agregadas: total, % com respostas, médias de remuneração/horas, distribuição por status/semestre/empresa, e — para o coordenador — agregação por seção do `ModeloFormulario`. **Bloqueado para supervisor** (`403`) | ✓ pronto |
| GET | `/api/dashboard/empresas/` | Coord / Admin / Administrativo | Estatísticas por empresa: total de estagiários, média de avaliação anônima (1-5), comentários recentes. **Bloqueado para supervisor** (`403`) | ✓ pronto |

## Autenticação

A camada de autenticação usa token DRF (`rest_framework.authtoken`). Detalhes do header `Authorization: Token <chave>`, ciclo de vida do token e estrutura dos payloads de cadastro estão em [Autenticação](autenticacao.md).

### POST `/api/auth/register/`

Cria um `Usuario` + perfil vinculado conforme o campo `tipo` (`aluno`, `coordenador`, `supervisor_empresa` ou um dos 5 perfis administrativos — `secretaria`, `casa`, `reitor`, `pro_reitor`, `carreiras`). Devolve token DRF pronto pra usar. Body comum: `tipo`, `email`, `password`, `nome`. Campos extras variam por tipo (CPF para aluno, departamento para coordenador, empresa_id para supervisor; perfis administrativos não exigem campos extras). Veja [Autenticação](autenticacao.md#post-apiauthregister).

### POST `/api/auth/login/`

Autentica `email` + `password` via `django.contrib.auth.authenticate` e devolve `{token, id, tipo, nome, email}`. Falha com `401 Unauthorized` se as credenciais não baterem. Veja [Autenticação](autenticacao.md#post-apiauthlogin).

### POST `/api/auth/logout/`

Apaga o token DRF do usuário corrente. Próximas requisições com aquele token retornam `401`. Veja [Autenticação](autenticacao.md#post-apiauthlogout).

### POST `/api/auth/esqueci-senha/` / POST `/api/auth/redefinir-senha/`

Fluxo de redefinição por email institucional. O primeiro envia um link contendo `uid` e `token` (via `PasswordResetTokenGenerator`) e responde sempre `200 OK` para não vazar quais emails existem. O segundo valida o `token` e troca a senha (mínimo 6 caracteres). Detalhes completos em [Autenticação](autenticacao.md#post-apiauthesqueci-senha).

## Processos de Estágio (foco da PR #47)

Recurso central da entrega. `ProcessoEstagioViewSet` aplica RBAC no `get_queryset` (cada papel só enxerga o que lhe pertence), troca de serializer conforme a ação e expõe duas `@action` customizadas.

### GET `/api/processos-estagio/`

Lista paginada dos processos visíveis ao usuário. O filtro implícito por papel é:

- **Aluno** — somente os próprios processos (`filter(aluno=aluno)`).
- **Supervisor de empresa** — processos da empresa em que está vinculado (`filter(empresa=supervisor.empresa)`); `respostas_formulario` é anulado no payload (privacidade da avaliação).
- **Coordenador** — processos de alunos dos cursos que coordena (`filter(aluno__curso__coordenador=coord)`).
- **Admin / perfis administrativos** (`has_global_access`) — todos.
- **Qualquer outro caso** — `.none()` (negação por default).

Permissões: `IsAuthenticated`. Os filtros de papel acontecem no queryset, não nas permissions.

### POST `/api/processos-estagio/`

Cria um processo. Apenas alunos podem chamar — se o usuário não tem perfil `Aluno`, o `perform_create` levanta `PermissionDenied`. O ViewSet seta automaticamente `aluno` = aluno logado, `status` = `PENDENTE` e `coordenador` = coordenador do curso do aluno (quando existir).

Payload de exemplo:

```json
{
  "empresa": 4,
  "supervisor": 7,
  "horas_semanais": 20,
  "data_inicio_prevista": "2026-06-15",
  "data_fim_prevista": "2026-12-15",
  "plano_atividades": "Desenvolvimento de microserviços em Python."
}
```

Resposta `201 Created`:

```json
{
  "id": 12,
  "aluno": 3,
  "empresa": 4,
  "supervisor": 7,
  "coordenador": 2,
  "status": "PENDENTE",
  "horas_semanais": 20,
  "data_inicio_prevista": "2026-06-15",
  "data_fim_prevista": "2026-12-15",
  "plano_atividades": "Desenvolvimento de microserviços em Python.",
  "justificativa_rejeicao": ""
}
```

Permissões: `IsAuthenticated` + perfil `Aluno` verificado em `perform_create`.

### GET `/api/processos-estagio/{id}/`

Detalha um processo. O acesso é validado duplamente: pelo queryset (papel) e pelo `get_object` (existência). Se o ID não está no queryset filtrado, o DRF responde `404 Not Found` — não vaza a existência de processos alheios.

Resposta `200 OK` traz o mesmo formato do `POST`, com os relacionamentos resolvidos por `select_related`.

### POST `/api/processos-estagio/{id}/alterar_status/`

Endpoint mais delicado da entrega. Executa **cinco checagens em ordem** antes de persistir:

1. **Transição válida** pelo mapa em `state_machine.py` (`transicoes_validas(processo.status)`).
2. **Permissão por papel** — aluno só pode `RASCUNHO→PENDENTE` ou cancelar processos com status `RASCUNHO`/`PENDENTE`; a partir de `APROVADO` o cancelamento passa pelo coordenador. Coordenador só pode emitir `APROVADO`, `REJEITADO`, `CORRECAO_SOLICITADA`, `ATIVO` ou `ENCERRADO`.
3. **RN05 (TCE aprovado)** — quando `processo.status=APROVADO` e `novo_status=ATIVO`, o sistema exige um `DocumentoProcesso` do tipo `TCE` com `status=APROVADO`. Sem isso, devolve `400 Bad Request` com a mensagem `RN05: é necessário que o TCE assinado esteja aprovado para ativar o estágio.`
4. **Validação do serializer** `AlterarStatusSerializer` — exige `justificativa_rejeicao` quando `novo_status=REJEITADO` (RN06).
5. **Persistência** + criação do registro em `HistoricoStatusProcesso` (`status_anterior`, `status_novo`, `usuario`, `observacao`) + refresh + retorno do processo serializado por inteiro.

Payload mínimo:

```json
{
  "status": "APROVADO"
}
```

Payload de rejeição (justificativa obrigatória):

```json
{
  "status": "REJEITADO",
  "justificativa_rejeicao": "Plano de atividades não condiz com o curso do aluno."
}
```

Resposta de erro em transição inválida (`400 Bad Request`):

```json
{
  "status": "Transição inválida: APROVADO → RASCUNHO.",
  "estado_atual": "APROVADO",
  "transicoes_validas": ["ATIVO", "CANCELADO", "REJEITADO"]
}
```

Veja o mapa completo em [Máquina de Estados](state-machine.md) e a lista de regras de negócio aplicadas em [Regras de Negócio](regras-negocio.md).

### GET `/api/processos-estagio/{id}/documentos/`

Lista todos os `DocumentoProcesso` vinculados ao processo, ordenados por `-data_upload`. Reutiliza o `DocumentoProcessoSerializer`. Permissões: o `get_object` aplica o filtro de papel; quem não tem visão do processo recebe `404`.

Resposta `200 OK`:

```json
[
  {
    "id": 18,
    "processo": 12,
    "tipo": "TCE",
    "arquivo": "/media/documentos/tce_12.pdf",
    "enviado_por": 5,
    "data_upload": "2026-05-27T14:32:11Z",
    "status": "PENDENTE",
    "versao": 1
  }
]
```

## Cursos

CRUD básico via `CursoViewSet`. Escrita (`POST`/`PUT`/`PATCH`/`DELETE`) exige `IsAdminOrReadOnly`; leitura é liberada para autenticados, mas o `get_queryset` filtra: coordenador vê apenas cursos onde é responsável (`filter(coordenador=coordenador)`), perfis administrativos e admin veem tudo (`has_global_access`).

> A relação `Curso ↔ Coordenador` é **1:N**: um coordenador pode coordenar vários cursos. No modelo, `Curso.coordenador` é FK para `Coordenador` com `related_name='cursos'`.

Campos do modelo (referência rápida):

```python
nome: CharField
coordenador: ForeignKey(Coordenador, null=True, related_name='cursos')
carga_horaria_minima_total: PositiveIntegerField
carga_horaria_maxima_diaria: PositiveIntegerField (default=6)
```

Permissões resumidas:

| Ação | Aluno | Coordenador | Supervisor | Administrativo | Admin |
| -- | -- | -- | -- | -- | -- |
| Listar/detalhar | ✓ (todos) | ✓ (só os seus) | ✓ (todos) | ✓ (todos) | ✓ |
| Criar/editar/remover | ✗ | ✗ | ✗ | ✗ | ✓ |

## Empresas Concedentes

`EmpresaConcedenteViewSet` é o caso onde a permissão depende da **ação**: leitura/escrita seguem `IsAdminOrReadOnly`, **exceto `create`**, que aceita qualquer autenticado — o aluno pode propor o cadastro da empresa do próprio estágio (RN do fluxo onboarding).

Suporta **dois filtros via query string**:

| Parâmetro | Tipo | Comportamento |
| -- | -- | -- |
| `?aprovada=true` ou `?aprovada=false` | bool (aceita `true`/`1`) | Filtra por `aprovada_ibmec` |
| `?busca=texto` | string | `razao_social__icontains=texto` |

Exemplo combinando filtros:

```bash
GET /api/empresas/?aprovada=true&busca=tecnologia
```

Campos persistidos:

```python
cnpj: CharField unique
razao_social: CharField
areas_atuacao: TextField
localizacao: CharField
email_contato: EmailField
descricao: TextField
responsavel_legal_nome: CharField
responsavel_legal_cargo: CharField
aprovada_ibmec: BooleanField (default=False)
```

> **Cadastro pelo aluno dispara um efeito colateral.** Quando o `create` é feito por um aluno, todos os 8 campos acima são obrigatórios (validação adicional retorna `400` com `campos_faltando`). Após salvar, o `perform_create` cria automaticamente um `Usuario` + `SupervisorEmpresa` para o gestor (`email_contato`), gera um token via `PasswordResetTokenGenerator` e envia email com o link `{FRONTEND_BASE_URL}/redefinir-senha/?uid=...&token=...` para que o gestor defina a senha. Falhas de SMTP são silenciosas (`fail_silently=True`).

## Alunos

`AlunoViewSet` aplica isolamento por papel no `get_queryset`:

- **Admin / perfis administrativos** (`has_global_access`) — todos os alunos.
- **Aluno** — apenas o próprio registro (`filter(pk=aluno.pk)`).
- **Coordenador** — alunos dos cursos que coordena (`filter(curso__coordenador=coord)`).
- **Outros casos** — `.none()`.

A leitura usa `select_related('usuario', 'curso')` para evitar N+1 ao montar a listagem.

> **Dois serializers convivem.** `AlunoListSerializer` (sem CPF/RG) é usado em todas as listagens e nas visões de coordenador. `AlunoDetailSerializer` (com dados sensíveis) só é entregue em `retrieve`/`update`/`partial_update` para admin/administrativo ou quando o próprio aluno acessa o próprio registro — o `get_serializer_class` faz essa escolha.

Resposta de exemplo (`GET /api/alunos/{id}/`):

```json
{
  "id": 3,
  "usuario": {
    "id": 11,
    "username": "joao.silva",
    "nome": "João Silva",
    "email_institucional": "joao.silva@ibmec.edu.br",
    "tipo": "aluno"
  },
  "cpf": "123.456.789-00",
  "rg": "12.345.678-9",
  "coeficiente_rendimento": "8.50",
  "curso": 2,
  "matriculado_estagio": true
}
```

## Coordenadores

`CoordenadorViewSet` segue o mesmo padrão: admin/administrativo veem todos, coordenador vê só a si mesmo, outros papéis recebem `.none()`. Útil para coordenadores conferirem seu próprio cadastro e a secretaria/CASA/reitoria auditarem a equipe acadêmica.

## Supervisores de Empresa

`SupervisorEmpresaViewSet` com a mesma estrutura: admin/administrativo veem todos, supervisor vê só a si mesmo, demais recebem `.none()`. O `select_related('usuario', 'empresa')` traz a empresa vinculada em uma query.

## Documentos

`DocumentoProcessoViewSet` gerencia os arquivos vinculados aos processos (`TCE`, `APOLICE`, `RELATORIO_PARCIAL`, `RELATORIO_FINAL`, `AVALIACAO_EMPRESA`, `TERMO_REALIZACAO`, `OUTRO`).

Isolamento por papel no queryset:

- **Aluno** — documentos dos próprios processos.
- **Supervisor de empresa** — documentos dos processos da empresa em que atua.
- **Coordenador** — documentos dos processos de alunos dos cursos sob coordenação.
- **Admin / perfis administrativos** (`has_global_access`) — todos.

Filtros via query string: `?processo=<id>`, `?tipo=<TCE|...>`, `?status=<PENDENTE|...>`.

No `perform_create`, o ViewSet:

1. Seta `enviado_por = request.user` automaticamente, garantindo trilha de auditoria sem confiar em campo do cliente.
2. Calcula o `score_conformidade` via `score_utils.calcular_score_conformidade` (usa `PyPDF2` para ler o PDF e extrair sinais por tipo de documento).
3. Se `score >= 0.8`, promove o documento para `APROVADO` automaticamente.
4. Registra um `LogDocumento` de `UPLOAD` (e outro de `APROVADO` automático, quando aplicável).

### POST `/api/documentos/{id}/validar/`

Aprovação/rejeição manual por coordenador ou admin. Body:

```json
{ "status": "APROVADO" }
```

ou

```json
{ "status": "REJEITADO", "comentario": "Assinatura digital ilegível." }
```

Persiste em `DocumentoProcesso.status`, escreve o `comentario` em `observacoes` (quando enviado) e registra um `LogDocumento` com a ação correspondente. Retorna `403` para quem não é coordenador ou admin; retorna `400` se `status` não for `APROVADO`/`REJEITADO`.

### GET `/api/documentos/{id}/logs/`

Lista o histórico de ações (`LogDocumento`) do documento, ordenado cronologicamente. Útil para a tela de auditoria.

### Comportamento de filtros combinados

Quando o usuário tem mais de um perfil ativo (caso raro em produção, mas suportado pelo modelo), o `get_queryset` resolve a precedência nesta ordem em cada ViewSet:

1. `has_global_access(user)` — admin (`is_staff`) ou perfil administrativo (`is_administrativo`): retorna tudo.
2. `get_aluno(user)` — se houver perfil `Aluno`, filtra para o próprio aluno.
3. `get_supervisor(user)` — se houver perfil `SupervisorEmpresa`, filtra pela empresa.
4. `get_coordenador(user)` — se houver perfil `Coordenador`, filtra pelos cursos coordenados.
5. Nada bateu → `.none()`.

Ou seja, a ordem é: visão global > aluno > supervisor > coordenador. Em produção, cada `Usuario` deve ter apenas um perfil — o admin Django facilita auditar inconsistências.

## Resumo de permissões por papel

Tabela cruzada para consulta rápida. Marcador `R` = leitura, `W` = escrita (criar/atualizar/remover), `–` = sem acesso. **Administrativo** abrange `secretaria`, `casa`, `reitor`, `pro_reitor` e `carreiras` (visão global read-only).

| Recurso | Aluno | Coordenador | Supervisor | Administrativo | Admin |
| -- | -- | -- | -- | -- | -- |
| `/api/cursos/` | R | R (só seus) | R | R | R+W |
| `/api/empresas/` | R + criar | R + W (edit/delete só admin) | R | R | R+W |
| `/api/alunos/` | R (si) | R (alunos dos seus cursos) + W limitado | – | R | R+W |
| `/api/coordenadores/` | – | R (si) | – | R | R+W |
| `/api/supervisores-empresa/` | – | – | R (si) | R | R+W |
| `/api/documentos/` | R+W (próprios) | R (escopo) + `validar`/`logs` | R+W (escopo) | R | R+W |
| `/api/processos-estagio/` | R (próprios) + criar | R (escopo) + transições | R (escopo, sem respostas) | R | R+W |
| `/api/modelos-formulario/` | R (ativo do próprio curso) | R+W (do próprio curso) | R (ativos) | R | R+W |
| `/api/avaliacoes-empresa/` (vinc.) | R+W (próprias) | R (escopo) | R (empresa) | R | R+W |
| `/api/avaliar-empresa/` (anônimo) | escrita restrita | – | – | – | – |
| `/api/templates-documentos/` | R (ativos) | R+W | R (ativos) | R | R+W |
| `/api/dashboard/*` | – | R (escopo) | R só `processos/` | R | R |

A coluna "escopo" significa: documentos/processos do círculo de cursos (coordenador) ou da empresa (supervisor), nunca de terceiros. **Supervisor não acessa** `/api/dashboard/estatisticas/` nem `/api/dashboard/empresas/` (retorna `403`) — esses agregados expõem médias de avaliação anônima e dados de outras empresas que não devem ser apresentados ao supervisor avaliado.

## Documentação interativa

Para explorar payloads exatos, testar requisições com um botão "Try it out" e inspecionar o JSON OpenAPI bruto, acesse a documentação interativa servida pelo `drf-spectacular`:

- Swagger UI — [`/api/docs/`](http://localhost:8000/api/docs/)
- Redoc — [`/api/redoc/`](http://localhost:8000/api/redoc/)
- Schema OpenAPI 3 (JSON) — [`/api/schema/`](http://localhost:8000/api/schema/)

Tudo é gerado a partir dos ViewSets, Serializers e docstrings do código. Mudou o serializer? Recarregue o Swagger.

## Fora do escopo desta entrega

Os itens abaixo **não existem** na API atual:

- `GET /api/cursos/meus_alunos/` e `GET /api/cursos/processos_pendentes/` — descartados; coordenadores usam `/api/dashboard/processos/` com filtros para a mesma necessidade.
- `GET /api/alunos/meu_perfil/`, `GET /api/coordenadores/meu_perfil/`, `GET /api/empresas/meu_perfil/` — descartados; cada papel obtém o próprio perfil pela listagem filtrada do ViewSet (`GET /api/alunos/` retorna apenas o próprio registro quando chamado por um aluno).
- Login via conta institucional Microsoft (OAuth) — a carcaça do `django-allauth` está instalada, mas o App Registration no Azure AD não foi configurado. O fluxo operacional é Token Auth.
- Validação de MIME/tamanho no upload em `/api/documentos/` — o upload aceita PDFs (e calcula `score_conformidade`), mas a restrição estrita de MIME/limite de tamanho é parte das tarefas pendentes.
- Análise por NLP do plano de atividades (RN avaliação semântica) — manteve-se a heurística por score de conformidade do PDF; NLP avançado fica para uma entrega futura.

## Autor(es)

| Data | Versão | Descrição | Autor(es) |
| -- | -- | -- | -- |
| 28/05/2026 | 1.0 | Criação do documento | João Gabriel Teodósio |
| 11/06/2026 | 1.1 | Documenta 10 ViewSets, endpoints diretos (dashboard, avaliação anônima, geração de PDFs, validação de documentos), 9 tipos de usuário e remove atalhos `meu_perfil/` / `meus_alunos` descartados | João Gabriel Teodósio |
