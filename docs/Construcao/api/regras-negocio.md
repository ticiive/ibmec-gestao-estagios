# Regras de Negócio — Rastreabilidade

Este documento mapeia cada **regra de negócio** (RN) implementada na API IBMEC Estágios ao **código que a aplica** e ao **teste automatizado que prova seu funcionamento**. A filosofia é simples: toda RN levantada na fase de elaboração precisa virar código testado e auditável. Quem ler este documento deve conseguir, em poucos cliques, sair da redação da regra no documento de requisitos, chegar à linha exata do `serializers.py`/`views.py` que a executa e confirmar que existe um teste com nome explícito provando aquela regra. As regras foram derivadas do documento `docs/Elaboracao/Requisitos/Requisitos-Gerais.md`, da Lei 11.788/08 e das normas internas do IBMEC.

> **Renumeração (09/06/2026).** O documento `Requisitos-Gerais.md` foi promovido à versão **1.1**, com a remoção de RN02 (Pré-requisitos PPC) e RN08 antiga (Notificações de atraso) e renumeração subsequente. Este documento adota o **novo numeração** e mantém uma tabela de equivalência abaixo para preservar a rastreabilidade dos commits, comentários no código e mensagens de erro anteriores.

## Equivalência RN antiga → RN nova

| RN antiga (v1.0) | RN nova (v1.1) | Observação |
| ---------------- | -------------- | ---------- |
| RN01 | **RN01** | Mantida — aluno deve estar matriculado em estágio |
| RN02 | — | **Removida** em v1.1: pré-requisitos do PPC ficaram fora do escopo (sem acesso aos PPCs) |
| RN03 | **RN02** | Renumerada — carga horária compatível com o curso |
| RN04 | **RN03** | Renumerada — limites diários e semanais por lei (não implementada plenamente, ver abaixo) |
| RN05 | **RN04** | Renumerada e reinterpretada — "tempo máximo na mesma empresa concedente" é operacionalizado como "1 processo não-`CANCELADO` por aluno", implementação **estrita** |
| RN06 | **RN05** *(parcial)* | Renumerada — NLP de plano de atividades vs curso continua sem implementação; o ID **RN05 na v1.1 ganhou nova redação** ("TCE + apólice válida para Aprovado") |
| RN07 | **RN06** | Renumerada — NLP do plano de atividades vs curso (sem implementação automatizada de NLP) |
| RN08 antiga | — | **Removida** em v1.1: notificações de atraso ficaram fora do escopo |
| RN09 | **RN07** | Renumerada — empresa aprovada pelo IBMEC |
| RN10 | **RN08** | Renumerada — campos obrigatórios da empresa (agora com 8 campos) |
| RF11 (a.k.a. RN11 no código) | **RF11 / RN11** | Mantida — justificativa obrigatória em rejeição. Continua sendo um RF no documento de requisitos, mas o código histórico a referencia como `RN11` |

## Tabela mestre

Legenda de fonte: **Req v1.1** = `Requisitos-Gerais.md` (versão 1.1, 09/06/2026); **Lei** = Lei 11.788/08; **Domínio** = validação básica de domínio.

| ID    | Regra (resumo)                                                                                       | Fonte           | Onde é validada                                  | Teste que prova                                          | HTTP |
| ----- | ---------------------------------------------------------------------------------------------------- | --------------- | ------------------------------------------------ | -------------------------------------------------------- | ---- |
| RN01  | Aluno deve estar matriculado em estágio supervisionado                                               | Req v1.1        | `CriarProcessoSerializer.validate`               | `test_aluno_nao_matriculado_400_rn01`                    | 400  |
| RN02  | Jornada compatível com a carga máxima do curso (PPC)                                                 | Req v1.1 + Lei  | `CriarProcessoSerializer.validate`               | `test_horas_excedem_limite_curso_400_rn03`*              | 400  |
| RN03  | Limites diários e semanais por lei                                                                   | Req v1.1 + Lei  | `CriarProcessoSerializer.validate` (parcial)     | `test_horas_acima_limite_legal_30h_400`                  | 400  |
| RN04  | Um único processo não-`CANCELADO` por aluno por vez (implementação estrita)                          | Req v1.1        | `CriarProcessoSerializer.validate`               | `test_aluno_com_processo_vivo_nao_cria_outro_400_rn05`*  | 400  |
| RN05  | `APROVADO→ATIVO` exige TCE aprovado (apólice registrada via `numero_seguro`)                         | Req v1.1        | `ProcessoEstagioViewSet.alterar_status` (passo 3) | `test_aprovado_para_ativo_sem_tce_aprovado_400_rn05`     | 400  |
| RN06  | Análise NLP do plano de atividades vs curso                                                          | Req v1.1        | **Não implementada** (fora do escopo desta entrega) | —                                                    | —    |
| RN07  | Empresa precisa estar aprovada pelo IBMEC                                                            | Req v1.1        | `CriarProcessoSerializer.validate`               | `test_empresa_nao_aprovada_400_rn09`*                    | 400  |
| RN08  | Campos obrigatórios da empresa quando proposta por aluno (8 campos)                                  | Req v1.1        | `EmpresaConcedenteViewSet.create`                | `test_aluno_cadastra_empresa_campos_obrigatorios`        | 400  |
| RF11  | Justificativa obrigatória em rejeição (referenciada como `RN11` no código)                           | Req v1.1        | `AlterarStatusSerializer.validate`               | `test_coord_rejeita_sem_justificativa_400_rn11`          | 400  |
| LEI   | Limite legal de 30h/semana                                                                           | Lei art. 10     | `CriarProcessoSerializer.validate`               | `test_horas_acima_limite_legal_30h_400`                  | 400  |
| DATA  | `data_fim_prevista > data_inicio_prevista`                                                           | Domínio         | `CriarProcessoSerializer.validate`               | `test_data_fim_antes_inicio_400`                         | 400  |

\* Os nomes dos testes preservam o ID **antigo** da RN (`_rn03`, `_rn05`, `_rn09`) porque foram criados antes da renumeração e serão atualizados em PR subsequente. As mensagens de erro também ainda exibem o ID antigo em alguns trechos — a renumeração de identidades visíveis nas APIs é tratada como mudança contratual e será feita em um único commit após sinal verde da equipe de frontend.

## Detalhes por regra

### RN01 — Aluno deve estar matriculado em estágio

**O que diz.** "O sistema só deve permitir que o aluno realize login na plataforma se ele estiver devidamente matriculado na disciplina 'Estágio Supervisionado'." (`Requisitos-Gerais.md` v1.1, RN01.) A implementação atual aplica a regra **na criação do processo** (e não no login), pois o login está aberto a alunos em geral; o que está bloqueado é abrir solicitação de estágio sem matrícula ativa.

**Por que existe.** Garante que apenas alunos com vínculo formal com a disciplina possam iniciar um processo de estágio. Evita estágios "fantasma" e protege a integridade acadêmica da supervisão.

**Onde está implementada.** `djangotutorial/app/serializers.py`, classe `CriarProcessoSerializer`, método `validate`.

```python
# RN01: matriculado em estágio
if not aluno.matriculado_estagio:
    raise serializers.ValidationError({
        'aluno': 'RN01: aluno deve estar com matrícula ativa em estágio supervisionado.'
    })
```

**Teste que prova.** `test_aluno_nao_matriculado_400_rn01` em `djangotutorial/app/tests.py`, classe `CriacaoProcessoTest`.

**Resposta HTTP esperada.** `400 Bad Request`.

```json
{ "aluno": ["RN01: aluno deve estar com matrícula ativa em estágio supervisionado."] }
```

### RN02 — Jornada compatível com o curso

**O que diz.** "O sistema deve impedir a aprovação do estágio caso a carga horária oferecida pela empresa seja incompatível com a quantidade mínima de horas exigida pelo curso do aluno." (`Requisitos-Gerais.md` v1.1, RN02.) Cada curso define `carga_horaria_maxima_diaria` no model `Curso`, e o limite semanal é calculado como `5 × diária`.

**Por que existe.** O Projeto Pedagógico de cada curso define uma carga máxima compatível com a grade acadêmica. Aceitar mais do que isso comprometeria o desempenho acadêmico do aluno.

**Onde está implementada.** `djangotutorial/app/serializers.py`, `CriarProcessoSerializer.validate`.

```python
# RN02 (anteriormente RN03): jornada compatível com o curso
horas = data['horas_semanais']
if aluno.curso is not None and aluno.curso.carga_horaria_maxima_diaria:
    limite_curso = aluno.curso.carga_horaria_maxima_diaria * 5
    if horas > limite_curso:
        raise serializers.ValidationError({
            'horas_semanais': f'RN03: excede o limite do curso ({limite_curso}h/semana).'
        })
```

**Teste que prova.** `test_horas_excedem_limite_curso_400_rn03` (nome mantido por compatibilidade).

### RN03 — Limites diários e semanais por lei

**O que diz.** "O sistema deve controlar a jornada de estágio e emitir um alerta/bloqueio se a carga horária informada ultrapassar os limites diários e semanais permitidos por lei." (`Requisitos-Gerais.md` v1.1, RN03.)

**Implementação parcial.** A validação **semanal** (30h, art. 10 da Lei 11.788/08) está pronta — ver linha `LEI` na tabela mestre. A validação **diária** depende do payload incluir `horas_diarias`, o que ainda não está no `CriarProcessoSerializer`. Fica como pendência junto com o redesenho do payload.

### RN04 — Um processo não-`CANCELADO` por aluno (estrita)

**O que diz (texto v1.1).** "O sistema deve restringir e controlar o tempo máximo que um aluno pode estagiar em uma mesma empresa concedente."

**Interpretação operacional.** A implementação adota a leitura **estrita**: enquanto houver qualquer `ProcessoEstagio` para o aluno em **qualquer estado diferente de `CANCELADO`** (inclusive `REJEITADO`, `ENCERRADO`, `ATIVO`, `APROVADO`, `PENDENTE`, `RASCUNHO`, `CORRECAO_SOLICITADA`), ele não pode abrir outro. Para iniciar um novo processo, o aluno precisa **explicitamente cancelar** o anterior — apenas processos no estado terminal `CANCELADO` são desconsiderados.

**Por que essa leitura.** A redação "tempo máximo na mesma empresa" foi normatizada via "1 processo vivo" para evitar a ambiguidade de calcular tempo decorrido com a empresa. A consequência prática é que o aluno fica "preso" ao seu único processo até cancelá-lo — alinhado com a expectativa do coordenador de não receber múltiplas solicitações simultâneas.

**Onde está implementada.** `djangotutorial/app/serializers.py`, `CriarProcessoSerializer.validate`.

```python
# RN04 (anteriormente RN05): 1 processo não-CANCELADO por aluno
existe_processo = ProcessoEstagio.objects.filter(aluno=aluno).exclude(
    status=ProcessoEstagio.Status.CANCELADO,
).exists()
if existe_processo:
    raise serializers.ValidationError(
        'RN05: aluno já possui um processo de estágio em andamento. '
        'Cancele ou aguarde o encerramento antes de abrir outro.'
    )
```

**Teste que prova.** `test_aluno_com_processo_vivo_nao_cria_outro_400_rn05` (nome mantido por compatibilidade).

### RN05 — `APROVADO→ATIVO` exige TCE aprovado

**O que diz.** "O estágio só poderá ter seu status alterado para 'Aprovado' e ser iniciado após a validação de todos os requisitos legais obrigatórios, o que inclui a aprovação do TCE e a anexação de uma Apólice de Seguro válida." (`Requisitos-Gerais.md` v1.1, RN05.)

**Interpretação operacional.** O sistema aplica a validação **na transição `APROVADO → ATIVO`** (ativação do estágio), e não na chegada ao `APROVADO`. A regra exige **apenas a aprovação do TCE** — a apólice de seguro é registrada como dado do processo via campo `ProcessoEstagio.numero_seguro` (preenchido no formulário do aluno) e não bloqueia a transição. Essa escolha simplifica o fluxo: o seguro fica auditável no processo, mas a verificação documental é manual.

**Onde está implementada.** `djangotutorial/app/views.py`, `ProcessoEstagioViewSet.alterar_status`, passo 3 (entre permissão por papel e validação do serializer).

```python
# RN05: APROVADO→ATIVO exige TCE aprovado
if processo.status == APROVADO and novo_status == ATIVO:
    tem_tce_aprovado = DocumentoProcesso.objects.filter(
        processo=processo,
        tipo=DocumentoProcesso.Tipo.TCE,
        status=DocumentoProcesso.StatusDoc.APROVADO,
    ).exists()
    if not tem_tce_aprovado:
        return Response(
            {'detail': 'RN05: é necessário que o TCE assinado esteja aprovado para ativar o estágio.'},
            status=drf_status.HTTP_400_BAD_REQUEST,
        )
```

**Teste que prova.** `test_aprovado_para_ativo_sem_tce_aprovado_400_rn05`.

### RN06 — Análise NLP do plano de atividades vs curso

**Status: não implementada.** Requer NLP/análise textual do `plano_atividades` ou taxonomia formal de áreas no `Curso`. Fica como follow-up de longo prazo (ligado a RF08 — análise automatizada). Hoje, o sistema substitui o NLP por uma heurística baseada em **score de conformidade do PDF** (PyPDF2 + regras por tipo de documento), aplicada no upload do documento — ver `app/score_utils.py:calcular_score_conformidade`.

### RN07 — Empresa aprovada pelo IBMEC

**O que diz.** "O aluno não pode prosseguir com a formalização do estágio em uma empresa que não tenha sido previamente aprovada/homologada pela faculdade no sistema." (`Requisitos-Gerais.md` v1.1, RN07.)

**Onde está implementada.** `djangotutorial/app/serializers.py`, `CriarProcessoSerializer.validate`.

```python
# RN07 (anteriormente RN09): empresa aprovada pelo IBMEC
empresa = data['empresa']
if not empresa.aprovada_ibmec:
    raise serializers.ValidationError({
        'empresa': 'RN09: empresa não está aprovada pelo IBMEC.'
    })
```

**Teste que prova.** `test_empresa_nao_aprovada_400_rn09` (nome mantido por compatibilidade).

### RN08 — Campos obrigatórios da empresa (quando proposta por aluno)

**O que diz.** "Toda empresa cadastrada deve possuir, obrigatoriamente, os dados: CNPJ, Razão Social, Áreas com vagas disponíveis e Localização." (`Requisitos-Gerais.md` v1.1, RN08.) A implementação **amplia o conjunto** quando o cadastro é feito por aluno, exigindo 8 campos:

- `cnpj`
- `razao_social`
- `areas_atuacao`
- `localizacao`
- `email_contato` *(usado para criar o usuário do gestor)*
- `descricao`
- `responsavel_legal_nome`
- `responsavel_legal_cargo`

**Por que existe.** Quando o cadastro é feito por aluno (fluxo do onboarding da empresa do próprio estágio), o sistema cria automaticamente um `Usuario` + `SupervisorEmpresa` para o gestor e envia email com link de definição de senha. Para que esse fluxo funcione, todos os 8 campos são imprescindíveis.

**Onde está implementada.** `djangotutorial/app/views.py`, `EmpresaConcedenteViewSet.create` (validação de campos faltando) e `perform_create` (criação do supervisor e envio do email).

```python
_CAMPOS_OBRIGATORIOS_EMPRESA = [
    'cnpj', 'razao_social', 'areas_atuacao', 'localizacao',
    'email_contato', 'descricao',
    'responsavel_legal_nome', 'responsavel_legal_cargo',
]
```

**Resposta HTTP esperada.** `400 Bad Request`.

```json
{
  "erro": "Todos os campos da empresa são obrigatórios.",
  "campos_faltando": ["responsavel_legal_nome", "responsavel_legal_cargo"]
}
```

### LEI — Lei 11.788/08, art. 10 (30h/semana)

Veja a versão original do texto em `docs/Iniciacao/pesquisa-detalhes/legislacao_trabalhista.md`. O ceiling de 30h/semana é aplicado logo após o RN02 no `CriarProcessoSerializer.validate` e é coberto pelo teste `test_horas_acima_limite_legal_30h_400`.

```python
# Ceiling legal (Lei 11.788/08)
if horas > 30:
    raise serializers.ValidationError({
        'horas_semanais': 'Limite legal de 30h semanais (Lei 11.788/08).'
    })
```

### DATA — `data_fim_prevista > data_inicio_prevista`

Validação básica de domínio. É a primeira verificação no `validate` e é coberta por `test_data_fim_antes_inicio_400`.

```python
if data['data_fim_prevista'] <= data['data_inicio_prevista']:
    raise serializers.ValidationError({
        'data_fim_prevista': 'Deve ser posterior à data de início.'
    })
```

### RF11 / "RN11" — Justificativa obrigatória em rejeição

**O que diz.** "O sistema deve exigir justificativa em caso de rejeição." (`Requisitos-Gerais.md` v1.1, **RF11**.) A convenção do time mantém o identificador `RN11` no código, em mensagens de erro e em nomes de testes.

**Onde está implementada.** `djangotutorial/app/serializers.py`, classe `AlterarStatusSerializer`, método `validate`.

```python
def validate(self, data):
    if data.get('status') == ProcessoEstagio.Status.REJEITADO:
        justif = data.get(
            'justificativa_rejeicao',
            self.instance.justificativa_rejeicao if self.instance else '',
        )
        if not justif or not justif.strip():
            raise serializers.ValidationError({
                'justificativa_rejeicao': 'RN11: justificativa obrigatória ao rejeitar uma solicitação.'
            })
    return data
```

**Teste que prova.** `test_coord_rejeita_sem_justificativa_400_rn11`.

## Validação de transições de status (state machine)

Não é uma "RN" do documento de requisitos, mas é uma regra **crítica de domínio**: o status de um processo só pode mudar seguindo o mapa de transições definido em `djangotutorial/app/state_machine.py`. Por exemplo, um processo em estado terminal (`REJEITADO`, `ENCERRADO`, `CANCELADO`) não pode mais transitar para nenhum outro estado.

**Onde está implementada.** `djangotutorial/app/views.py`, `ProcessoEstagioViewSet.alterar_status`, passo 1.

```python
validas = transicoes_validas(processo.status)
if novo_status not in validas:
    return Response({
        'status': f'Transição inválida: {processo.status} → {novo_status}.',
        'estado_atual': processo.status,
        'transicoes_validas': sorted(validas) if validas else [],
    }, status=drf_status.HTTP_400_BAD_REQUEST)
```

**Teste que prova.** `test_transicao_invalida_400_lista_validas` (classe `AlterarStatusTest`).

Veja [state-machine.md](state-machine.md) para o diagrama completo do fluxo, a tabela de transições válidas e o registro automático em `HistoricoStatusProcesso` a cada `alterar_status`.

## RBAC: permissão por papel

Também não é uma "RN" listada nos requisitos, mas é uma regra **crítica de segurança**. A API impõe permissão por papel em duas camadas complementares:

**1. Queryset filtrado por papel** (`get_queryset` de cada ViewSet). Cada papel só "enxerga" um subconjunto. Em particular, no `ProcessoEstagioViewSet`:

- **Admin (`is_staff`) ou perfis administrativos** (`is_administrativo`: secretaria, casa, reitor, pro_reitor, carreiras) — `has_global_access`, visão de todos os processos (read-only para perfis administrativos).
- **Aluno** — apenas os próprios processos (`base.filter(aluno=aluno)`).
- **Supervisor de empresa** — apenas processos da sua empresa (`base.filter(empresa=supervisor.empresa)`), e o campo `respostas_formulario` é **anulado** no payload antes da resposta (privacidade da avaliação do aluno).
- **Coordenador** — apenas processos de alunos dos cursos que coordena (`base.filter(aluno__curso__coordenador=coord)`).

**2. Validação de quem dispara qual transição** (`alterar_status`, passo 2). Aluno só pode `RASCUNHO → PENDENTE` ou cancelar processos em `RASCUNHO`/`PENDENTE`. A partir de `APROVADO`, o cancelamento é via coordenador. Coordenador só pode emitir `APROVADO`, `REJEITADO`, `CORRECAO_SOLICITADA`, `ATIVO`, `ENCERRADO` e apenas em processos do seu escopo.

Veja a seção [Resumo de permissões por papel](endpoints.md#resumo-de-permissoes-por-papel) em `endpoints.md` para a matriz papel × verbo completa.

## Regras adicionais implementadas (não previstas em `Requisitos-Gerais.md`)

Estas regras nasceram do código, em resposta a casos descobertos durante o desenvolvimento. Estão prontas e testadas, mas não constam no documento de requisitos — ficam aqui para rastreabilidade.

### Filtragem de `respostas_formulario` para supervisor

O supervisor da empresa **não pode ver** as respostas que o aluno deu no formulário avaliativo da própria empresa. A `ProcessoEstagioViewSet._filtrar_respostas_se_supervisor` anula o campo no payload de `list` e `retrieve` quando o requisitante é supervisor. Justificativa: privacidade do aluno frente à empresa que ele está avaliando.

### Visão global read-only dos perfis administrativos

Os tipos `secretaria`, `casa`, `reitor`, `pro_reitor` e `carreiras` são reconhecidos por `is_administrativo` em `permissions.py` e, junto com `is_admin`, compõem `has_global_access`. Esses perfis veem **todos** os recursos em leitura, mas qualquer ação de escrita devolve `403 Forbidden`. Justificativa: setores administrativos do IBMEC precisam acompanhar os estágios em painéis sem poder alterar o pipeline.

### Cadastro de empresa por aluno cria `SupervisorEmpresa` + email

Detalhado no RN08. Quando um aluno cria uma empresa, o sistema:

1. Valida os 8 campos obrigatórios.
2. Persiste a empresa.
3. Cria `Usuario` (tipo `supervisor_empresa`) + `SupervisorEmpresa` para o gestor.
4. Gera token via `PasswordResetTokenGenerator` e envia email com o link `{FRONTEND_BASE_URL}/redefinir-senha/?uid=...&token=...`.
5. Falhas de SMTP são silenciosas (`fail_silently=True`).

### Avaliação anônima de empresa

O endpoint `POST /api/avaliar-empresa/` cria um `AvaliacaoEmpresa` com `aluno=None` e `processo=None`. A identidade do aluno fica preservada apenas via `aluno_hash = SHA256(aluno_pk:empresa_pk:SECRET_KEY)`, suficiente para impedir avaliações duplicadas mas não permite recuperar o aluno a partir do hash. Validações:

- Apenas alunos com processo `APROVADO`/`ATIVO`/`ENCERRADO`.
- Empresa avaliada deve ser a do processo do aluno.
- Limite de 1 avaliação por aluno por empresa.
- Nota entre 1 e 5.

### Score de conformidade do documento (auto-aprovação)

No upload de um `DocumentoProcesso`, o ViewSet chama `score_utils.calcular_score_conformidade` (PyPDF2 + heurísticas por tipo de documento). Se `score >= 0.8`, o documento é marcado automaticamente como `APROVADO` e um `LogDocumento` adicional registra a auto-aprovação. Isso é a **versão pragmática** da análise automatizada prevista no RF08; substitui o NLP do RN06 pela leitura estrutural do PDF.

## Cobertura de testes

Total: **102 testes** (101 passando + 1 marcado como `skipped` por se referir a fluxo legado), organizados em `djangotutorial/app/tests.py`. Para rodar:

```bash
cd djangotutorial
../.venv/bin/python manage.py test app -v 2
```

Convenção dos nomes: sempre que o teste cobre uma regra com ID, o ID aparece no nome (`_rn01`, `_rn03`, `_rn05`, `_rn09`, `_rn11`). Os nomes mantêm os **IDs antigos** para preservar o histórico de PRs — a renumeração dos nomes de teste será feita em commit dedicado.

## Regras NÃO implementadas (fora do escopo desta entrega)

- **RN03 (limite diário).** O limite **semanal** legal (30h) e o limite **semanal** do curso (RN02) estão prontos; falta validar a jornada **diária** declarada. Hoje o payload aceita só `horas_semanais`. Follow-up junto com o redesenho do payload.
- **RN06 — NLP do plano de atividades.** Requer modelo de NLP ou taxonomia formal das áreas do curso. Follow-up de longo prazo. A heurística por score de conformidade do PDF cobre parcialmente o RF08.
- **Apólice de seguro como bloqueio formal de RN05.** Hoje o seguro é registrado via `numero_seguro` no processo e fica auditável, mas a transição `APROVADO→ATIVO` exige apenas o TCE aprovado. Promover a apólice a bloqueio explícito está no roadmap.
- **RF16 — Abertura formal por escolha de vaga.** Hoje o aluno descreve a oportunidade no `plano_atividades`, sem model `Vaga`. Quando entrar o catálogo de vagas, o `CriarProcessoSerializer` passa a vincular processo a vaga.

### Removidos do escopo em v1.1

- **RN02 antiga (Pré-requisitos PPC).** Removida — sem acesso aos PPCs dos cursos.
- **RN08 antiga (Notificações de atraso).** Removida junto com RF12 (Notificações): requer infra de jobs (Celery/cron) fora do escopo.
- **RF17 antigo (Assinatura digital).** Removido — a assinatura dos documentos é feita por fora do sistema.

## Autor(es)

| Data       | Versão | Descrição              | Autor(es)               |
| ---------- | ------ | ---------------------- | ----------------------- |
| 28/05/2026 | 1.0    | Criação do documento   | João Gabriel Teodósio   |
| 11/06/2026 | 1.1    | Renumeração para Req v1.1 com tabela de equivalência; documentação do RN04 estrito, do RN05 (TCE) e do RN08 com 8 campos; novas regras implementadas (filtragem de `respostas_formulario`, visão global, cadastro de empresa por aluno, avaliação anônima, score auto-aprovação) | João Gabriel Teodósio   |
