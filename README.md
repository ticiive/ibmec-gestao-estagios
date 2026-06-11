# PBE_26.1_8002_I — IBMEC Estágios

Projeto da disciplina voltado à gestão e otimização dos **estágios obrigatórios** do IBMEC. A proposta é centralizar a formalização, validação e acompanhamento do estágio em um único fluxo, conectando aluno, empresa concedente e coordenação com rastreabilidade documental, regras acadêmicas por curso e menos dependência de processos manuais.

O repositório contém dois artefatos principais:

- **Backend** Django + DRF em `djangotutorial/` (API REST + SPA estático em `dashboard-ibmec.html`).
- **Documentação** MkDocs (Material) em `docs/`, publicada em GitHub Pages.

## Participantes

- Lucas de Souza Alcantara
- João Gabriel Teodósio de Oliveira Lima
- Roger dos Santos Tavares Pires
- Letícia Rocha Valladão
- Vinícius Dias Lopes Machado Martinez

## Stack

- **Python 3.9+** (testado em 3.11/3.13)
- **Django 4.2 LTS** + **Django REST Framework 3.16**
- **drf-spectacular** (Swagger UI / Redoc / schema OpenAPI 3)
- **django-allauth 65** (carcaça para OAuth Microsoft — opcional)
- **django-cors-headers 4**
- **python-dotenv 1** (carregamento do `.env`)
- **reportlab 4.2** (geração de PDF: TCE, Termo de Realização, relatórios)
- **PyPDF2 3.0** (cálculo de `score_conformidade` no upload de documento)
- **SQLite** (banco padrão; o `settings.py` é compatível com qualquer backend Django)
- **MkDocs** + **Material for MkDocs** + **PlantUML** (documentação)

## Estrutura de pastas

```text
PBE_26.1_8002_I/
├── .github/workflows/         # CI e publicação do MkDocs
├── docs/                      # documentação fonte (MkDocs)
│   ├── Iniciacao/
│   ├── Elaboracao/
│   ├── Construcao/
│   └── Transicao/
├── djangotutorial/            # backend Django + SPA estático
│   ├── manage.py
│   ├── requirements.txt
│   ├── .env.example           # variáveis de ambiente — copie para .env
│   ├── dashboard-ibmec.html   # SPA React (servido como arquivo estático)
│   ├── populate_db.py         # script legado (use seed_completo em vez disso)
│   ├── app/                   # app Django principal
│   │   ├── models.py          # 13 modelos do domínio
│   │   ├── serializers.py
│   │   ├── views.py           # ViewSets + endpoints de auth/PDF/avaliação
│   │   ├── views_dashboard.py # 3 endpoints agregados de dashboard
│   │   ├── api_urls.py        # roteamento DRF
│   │   ├── permissions.py     # is_admin, is_administrativo, has_global_access...
│   │   ├── state_machine.py   # transições válidas de ProcessoEstagio
│   │   ├── pdf_generator.py   # reportlab — TCE / Termo / Relatório
│   │   ├── score_utils.py     # PyPDF2 — score de conformidade
│   │   ├── form_validator.py  # validação das respostas dinâmicas
│   │   ├── dashboard_utils.py # agregações por seção do ModeloFormulario
│   │   ├── tests.py           # 100+ testes
│   │   └── management/commands/seed_completo.py
│   ├── mysite/                # settings.py / urls.py / wsgi.py
│   └── media/                 # uploads (criado automaticamente)
├── mkdocs.yml                 # configuração do site
├── requirements.txt           # dependências do MkDocs (raiz)
└── README.md
```

> Há **dois `requirements.txt`** distintos: o da raiz instala o MkDocs (para gerar a documentação); o de `djangotutorial/` instala o backend.

---

## Backend Django/DRF

### 1. Pré-requisitos

- **Python 3.9+** (`python3 --version`)
- `pip` e `venv` instalados (acompanham a maioria das distribuições Python)
- (opcional) `git` para clonar o repositório

### 2. Clonar o repositório e entrar na pasta do backend

```bash
git clone https://github.com/Projetos-de-Extensao/PBE_26.1_8002_I.git
cd PBE_26.1_8002_I/djangotutorial
```

### 3. Virtualenv e dependências

```bash
# A partir de djangotutorial/
python3 -m venv ../.venv          # cria o venv na raiz do repo
source ../.venv/bin/activate      # Linux/macOS
# ..\.venv\Scripts\activate       # Windows (PowerShell ou cmd)

pip install -r requirements.txt
```

Conteúdo de `requirements.txt`:

```text
Django==4.2.30
djangorestframework==3.16.1
django-allauth[socialaccount]==65.14.3
django-cors-headers==4.9.0
drf-spectacular==0.29.0
python-dotenv==1.0.1
reportlab==4.2.2
PyPDF2==3.0.1
```

### 4. Variáveis de ambiente — `.env`

O `mysite/settings.py` lê o `.env` automaticamente via `python-dotenv`. Copie o exemplo:

```bash
cp .env.example .env
```

Em **dev local**, o arquivo já fornece valores razoáveis e o backend sobe sem alterações. As variáveis suportadas são:

| Variável | Valor padrão | Quando configurar |
| --- | --- | --- |
| `DJANGO_SECRET_KEY` | chave de dev | **Obrigatório em produção** — gere com `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` |
| `DJANGO_DEBUG` | `True` | Defina `False` em produção; ajuste `ALLOWED_HOSTS` no `settings.py` |
| `MICROSOFT_CLIENT_ID`, `MICROSOFT_CLIENT_SECRET`, `MICROSOFT_TENANT_ID` | vazio / `common` | Apenas se for usar login Microsoft (instruções abaixo) |
| `EMAIL_BACKEND` | console | Em prod, troque por `django.core.mail.backends.smtp.EmailBackend` |
| `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL` | Gmail SMTP / vazio | Quando o backend de email for SMTP |
| `FRONTEND_BASE_URL` | `http://localhost:8000` | URL do SPA (usada para montar links de redefinição de senha nos emails) |

### 5. Migrações

```bash
python manage.py migrate
```

Saída esperada: aplica os 18 arquivos de migração em `app/migrations/` (do `0001_initial.py` ao `0018_add_aluno_hash_to_avaliacao.py`).

### 6. Popular com dados de demonstração (recomendado)

O comando de seed cria um cenário completo (7 cursos × 10 alunos = 70 alunos, 6 empresas, 7 coordenadores, processos em estados variados, documentos e respostas de formulário) com senha padrão `senha123` para todos os usuários:

```bash
python manage.py seed_completo --force
```

> Sem `--force`, o comando pede confirmação interativa. Use `--force` em scripts.

Alternativa: criar apenas um superusuário (sem dados de demo):

```bash
python manage.py createsuperuser
```

### 7. Subir o servidor

```bash
python manage.py runserver
```

Acessos:

| URL | O quê |
| --- | --- |
| `http://127.0.0.1:8000/` | Redirect para o SPA |
| `http://127.0.0.1:8000/dashboard-ibmec.html` | SPA React (login + dashboards) |
| `http://127.0.0.1:8000/api/` | Raiz da API REST (browsable, exige login) |
| `http://127.0.0.1:8000/api/docs/` | **Swagger UI** — referência interativa |
| `http://127.0.0.1:8000/api/redoc/` | Documentação Redoc |
| `http://127.0.0.1:8000/api/schema/` | Schema OpenAPI 3 (JSON) |
| `http://127.0.0.1:8000/admin/` | Django Admin |

Após o seed, faça login no SPA com qualquer usuário gerado — por exemplo:

| Tipo | Email | Senha |
| --- | --- | --- |
| Coordenador | `joao.oliveira@ibmec.edu.br` | `senha123` |
| Aluno | ver `app/management/commands/seed_completo.py` ou Admin | `senha123` |

### 8. Endpoints rápidos

| Método | URL | Descrição |
| --- | --- | --- |
| POST | `/api/auth/register/` | Cria usuário + perfil (8 tipos), retorna token DRF |
| POST | `/api/auth/login/` | Autentica `email`/`password`, retorna token + dados básicos |
| POST | `/api/auth/logout/` | Invalida o token |
| POST | `/api/auth/esqueci-senha/` | Envia link de reset para o email |
| POST | `/api/auth/redefinir-senha/` | Valida `uid`+`token` e troca a senha |

Exemplo de login:

```bash
curl -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"joao.oliveira@ibmec.edu.br","password":"senha123"}'
```

A documentação completa de endpoints está em **`docs/Construcao/api/endpoints.md`** (renderizada em `mkdocs serve`) e no **Swagger UI** em `/api/docs/`.

### 9. Rodar a suíte de testes

```bash
python manage.py test app
```

Esperado: `Ran 102 tests in ~2min — OK (skipped=1)`.

---

## Login Microsoft (OAuth) — opcional

A carcaça do `django-allauth` com provider Microsoft já está instalada. **Sem configurar nada, o app continua funcionando** — apenas o botão "Entrar com Microsoft" no SPA não tem efeito. Para ativar:

### 1. Criar o App Registration no Azure

1. Acesse [portal.azure.com](https://portal.azure.com) com a conta institucional.
2. Vá em **Azure Active Directory → App registrations → New registration**.
3. Nome: `IBMEC Estágios`.
4. Tipos de conta: *Accounts in this organizational directory only* (ou *multi-tenant*, se necessário).
5. Redirect URI (Web): `http://127.0.0.1:8000/accounts/microsoft/login/callback/`.
6. **Register**.

### 2. Coletar credenciais

- **Client ID**: campo *Application (client) ID* na página do app.
- **Tenant ID**: campo *Directory (tenant) ID*.
- **Client Secret**: *Certificates & secrets → New client secret*, copie o **Value** logo após criar (não fica visível depois).

### 3. Preencher o `.env`

```env
MICROSOFT_CLIENT_ID=seu-client-id-aqui
MICROSOFT_CLIENT_SECRET=seu-client-secret-aqui
MICROSOFT_TENANT_ID=seu-tenant-id-aqui
```

Reinicie o `runserver` e o fluxo OAuth passa a funcionar.

---

## Documentação (MkDocs)

A documentação técnica e de processo do projeto vive em `docs/` e é renderizada com MkDocs + Material.

```bash
# A partir da raiz do repositório:
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt   # requirements.txt da raiz instala o MkDocs
mkdocs serve
```

Acesse `http://127.0.0.1:8000/` enquanto o `mkdocs serve` estiver rodando.

> Atenção ao **conflito de porta**: o `runserver` do Django e o `mkdocs serve` usam a porta 8000 por padrão. Rode um de cada vez ou passe `--addr` em um deles (`mkdocs serve -a 127.0.0.1:8001`).

A documentação publicada está em GitHub Pages — veja `mkdocs.yml` e os workflows em `.github/workflows/`.
