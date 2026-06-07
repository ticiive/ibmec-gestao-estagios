"""
Script de população do banco com dados realistas IBMEC.

Modos de execução:
    python3 populate_db.py                        # standalone
    python3 manage.py shell < populate_db.py      # via Django shell
"""
import os
import sys
import random
from datetime import date, timedelta
from decimal import Decimal

# ── Django setup (idempotente — funciona standalone e via shell) ─────────
try:
    from django.apps import apps as _apps
    if not _apps.ready:
        raise RuntimeError('apps not ready')
except Exception:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
    _here = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
    if _here not in sys.path:
        sys.path.insert(0, _here)
    import django
    django.setup()

from app.models import (
    Usuario, Curso, EmpresaConcedente,
    Aluno, Coordenador, SupervisorEmpresa,
    ProcessoEstagio, DocumentoProcesso, LogDocumento,
    ModeloFormulario,
)

random.seed(42)  # determinístico

PASSWORD = 'ibmec2026'

# ── DADOS ───────────────────────────────────────────────────────────────

CURSOS = [
    ('Administração', 'adm'),
    ('Arquitetura e Urbanismo', 'arq'),
    ('Ciência de Dados e Inteligência Artificial', 'cdia'),
    ('Ciências Econômicas', 'eco'),
    ('Publicidade e Propaganda', 'pub'),
    ('Direito', 'dir'),
    ('Engenharia da Computação', 'engc'),
    ('Engenharia de Produção', 'engp'),
    ('Engenharia de Software', 'engs'),
    ('Relações Internacionais', 'ri'),
]

# (curso_idx, username, nome, departamento)
COORDENADORES = [
    (0, 'carlos.almeida',    'Carlos Eduardo Almeida',     'Administração'),
    (1, 'mariana.ribeiro',   'Mariana Santos Ribeiro',     'Arquitetura'),
    (2, 'joao.oliveira',     'João Pedro Oliveira',        'Computação'),
    (3, 'patricia.carvalho', 'Patricia Mendes Carvalho',   'Economia'),
    (4, 'fernando.lima',     'Fernando Augusto Lima',      'Comunicação'),
    (5, 'beatriz.fernandes', 'Beatriz Cardoso Fernandes',  'Direito'),
    (6, 'ricardo.pereira',   'Ricardo Souza Pereira',      'Computação'),
    (7, 'camila.silva',      'Camila Rodrigues Silva',     'Engenharia'),
    (8, 'lucas.costa',       'Lucas Martins Costa',        'Computação'),
    (9, 'adriana.vieira',    'Adriana Pinheiro Vieira',    'Relações Internacionais'),
]

# (curso_idx, username, nome) — 2 por curso
ALUNOS = [
    (0, 'gabriel.silva',     'Gabriel Henrique Silva'),
    (0, 'sofia.andrade',     'Sofia Maria Andrade'),
    (1, 'fernanda.castro',   'Fernanda Oliveira Castro'),
    (1, 'rafael.borges',     'Rafael Lima Borges'),
    (2, 'pedro.reis',        'Pedro Vinícius Reis'),
    (2, 'isabella.nunes',    'Isabella Cristina Nunes'),
    (3, 'bruno.cavalcanti',  'Bruno Sales Cavalcanti'),
    (3, 'larissa.moura',     'Larissa Helena Moura'),
    (4, 'mateus.domingues',  'Mateus Alves Domingues'),
    (4, 'camilla.teixeira',  'Camilla Barbosa Teixeira'),
    (5, 'vinicius.ramos',    'Vinícius Aparecido Ramos'),
    (5, 'julia.couto',       'Júlia Beatriz Couto'),
    (6, 'thiago.pacheco',    'Thiago Mendes Pacheco'),
    (6, 'beatriz.aragao',    'Beatriz Souza Aragão'),
    (7, 'andre.macedo',      'André Costa Macedo'),
    (7, 'mariana.faria',     'Mariana Lucena Faria'),
    (8, 'felipe.brito',      'Felipe Carvalho Brito'),
    (8, 'renata.vieira',     'Renata Lopes Vieira'),
    (9, 'eduardo.monteiro',  'Eduardo Tavares Monteiro'),
    (9, 'manuela.barros',    'Manuela Coelho Barros'),
]

EMPRESAS = [
    {
        'razao_social': 'Tech Solutions Ltda',
        'cnpj': '12.345.678/0001-90',
        'areas_atuacao': 'Tecnologia · Desenvolvimento de Software · Dados',
        'localizacao': 'Rio de Janeiro, RJ',
        'email_contato': 'contato@techsolutions.com.br',
        'responsavel_legal_nome': 'Roberto Mendes Cardoso',
        'responsavel_legal_cargo': 'Diretor Executivo',
        'descricao': 'Empresa de tecnologia com foco em soluções de software para setores financeiro e educacional.',
    },
    {
        'razao_social': 'Construtora Horizonte S.A.',
        'cnpj': '23.456.789/0001-01',
        'areas_atuacao': 'Construção Civil · Engenharia · Projetos Estruturais',
        'localizacao': 'Rio de Janeiro, RJ',
        'email_contato': 'rh@horizonte.com.br',
        'responsavel_legal_nome': 'Cláudia Lima Vasconcellos',
        'responsavel_legal_cargo': 'Presidente',
        'descricao': 'Construtora atuante em obras residenciais e comerciais no estado do RJ.',
    },
    {
        'razao_social': 'Banco Capital Investimentos',
        'cnpj': '34.567.890/0001-12',
        'areas_atuacao': 'Finanças · Mercado de Capitais · Wealth Management',
        'localizacao': 'São Paulo, SP',
        'email_contato': 'estagio@bancocapital.com.br',
        'responsavel_legal_nome': 'Henrique Sampaio Marques',
        'responsavel_legal_cargo': 'CEO',
        'descricao': 'Banco de investimentos focado em wealth management e operações de M&A.',
    },
    {
        'razao_social': 'Agência Criativa Digital',
        'cnpj': '45.678.901/0001-23',
        'areas_atuacao': 'Marketing · Publicidade · Comunicação Digital',
        'localizacao': 'Rio de Janeiro, RJ',
        'email_contato': 'rh@agcriativa.com.br',
        'responsavel_legal_nome': 'Patrícia Lobo Fernandes',
        'responsavel_legal_cargo': 'CEO',
        'descricao': 'Agência full-service focada em marketing digital e branding.',
    },
    {
        'razao_social': 'Escritório Machado & Associados',
        'cnpj': '56.789.012/0001-34',
        'areas_atuacao': 'Advocacia · Direito Empresarial · Contencioso',
        'localizacao': 'Rio de Janeiro, RJ',
        'email_contato': 'contato@machadoassoc.adv.br',
        'responsavel_legal_nome': 'José Machado Filho',
        'responsavel_legal_cargo': 'Sócio Fundador',
        'descricao': 'Escritório de advocacia full-service com atuação em direito empresarial.',
    },
    {
        'razao_social': 'Global Trade Consultoria',
        'cnpj': '67.890.123/0001-45',
        'areas_atuacao': 'Comércio Exterior · Logística Internacional',
        'localizacao': 'Rio de Janeiro, RJ',
        'email_contato': 'rh@globaltrade.com.br',
        'responsavel_legal_nome': 'Ana Paula Aguiar',
        'responsavel_legal_cargo': 'Diretora de Operações',
        'descricao': 'Consultoria em comércio exterior e estratégias de internacionalização.',
    },
]

# (empresa_idx, username, nome, cargo)
SUPERVISORES = [
    (0, 'marcos.santiago',  'Marcos Vinícius Santiago',   'Diretor de Tecnologia'),
    (1, 'eliana.branco',    'Eliana Cristina Branco',     'Engenheira Sênior'),
    (2, 'antonio.macedo',   'Antonio Carlos Macedo',      'Gerente de Operações'),
    (3, 'daniela.rangel',   'Daniela Souza Rangel',       'Diretora Criativa'),
    (4, 'roberto.pinto',    'Roberto Almeida Pinto',      'Sócio Advogado'),
    (5, 'vanessa.cardoso',  'Vanessa Lima Cardoso',       'Gerente de Comércio Exterior'),
]


def fake_cpf(i):
    return f'{(100 + i):03d}.{(200 + i * 3) % 1000:03d}.{(300 + i * 5) % 1000:03d}-{(10 + i) % 100:02d}'


def fake_rg(i):
    return f'{(10 + i) % 100:02d}.{(100 + i * 2) % 1000:03d}.{(200 + i * 3) % 1000:03d}-{i % 10}'


def ferramentas_por_curso(slug):
    return {
        'adm':  ['Excel', 'SAP', 'Power BI', 'Word', 'PowerPoint'],
        'arq':  ['AutoCAD', 'SketchUp', 'Revit', 'Photoshop', 'Illustrator'],
        'cdia': ['Python', 'SQL', 'Git', 'Power BI', 'Tableau'],
        'eco':  ['Excel', 'R', 'Stata', 'Bloomberg', 'Power BI'],
        'pub':  ['Photoshop', 'Illustrator', 'After Effects', 'Premiere', 'Figma'],
        'dir':  ['Processo Eletrônico', 'JusBrasil', 'LexML', 'Word', 'Excel'],
        'engc': ['Python', 'Java', 'Git', 'Linux', 'Docker'],
        'engp': ['Excel', 'MS Project', 'Lean Six Sigma', 'Power BI', 'SAP'],
        'engs': ['Python', 'JavaScript', 'Git', 'Docker', 'Kubernetes'],
        'ri':   ['Excel', 'Bloomberg', 'PowerPoint', 'Word', 'Inglês avançado'],
    }.get(slug, ['Excel', 'Word', 'PowerPoint', 'Outlook', 'Teams'])


def aplicacao_por_curso(slug):
    return {
        'adm':  ['Gestão de Pessoas', 'Finanças', 'Marketing', 'Estratégia', 'Operações'],
        'arq':  ['Desenho técnico', 'Modelagem 3D', 'Urbanismo', 'Conforto ambiental', 'Estruturas'],
        'cdia': ['Estatística', 'Machine Learning', 'Banco de Dados', 'Visualização', 'Metodologia Ágil'],
        'eco':  ['Macroeconomia', 'Microeconomia', 'Econometria', 'Finanças', 'Pesquisa Operacional'],
        'pub':  ['Branding', 'Copywriting', 'Mídia paga', 'Conteúdo', 'Métricas digitais'],
        'dir':  ['Pesquisa jurisprudencial', 'Redação de peças', 'Atendimento ao cliente', 'Análise contratual', 'Negociação'],
        'engc': ['Algoritmos', 'Redes', 'Sistemas Operacionais', 'Segurança', 'Cloud'],
        'engp': ['Lean', 'PCP', 'Qualidade', 'Logística', 'Custos'],
        'engs': ['Programação', 'Arquitetura de Software', 'Testes', 'DevOps', 'UX/UI'],
        'ri':   ['Negociação internacional', 'Política externa', 'Geopolítica', 'Comércio Exterior', 'Diplomacia'],
    }.get(slug, ['Item 1', 'Item 2', 'Item 3', 'Item 4', 'Item 5'])


ITENS_COMPORTAMENTAIS = ['Visão', 'Adaptabilidade', 'Empatia', 'Liderança', 'Comunicação']
ITENS_EXPERIENCIA = [
    'Orientação do supervisor', 'Feedback recebido',
    'Condições de trabalho', 'Remuneração vs mercado',
    'Atividades vs formação',
]


def gerar_modelo_secoes(slug):
    return [
        {
            'id': 'comportamental', 'tipo': 'escala_1_4',
            'titulo': 'Inteligência Comportamental',
            'itens': ITENS_COMPORTAMENTAIS,
            'grafico': 'radar',
        },
        {
            'id': 'ferramentas', 'tipo': 'escala_1_4_multi',
            'titulo': 'Ferramentas e Softwares',
            'itens': ferramentas_por_curso(slug),
            'colunas': ['Empresa usa', 'Você usou'],
            'grafico': 'barras_agrupadas',
        },
        {
            'id': 'aplicacao', 'tipo': 'escala_1_4',
            'titulo': 'Aplicação do Conhecimento',
            'itens': aplicacao_por_curso(slug),
            'grafico': 'radar',
        },
        {
            'id': 'experiencia', 'tipo': 'escala_3',
            'titulo': 'Avaliação da Experiência',
            'itens': ITENS_EXPERIENCIA,
            'opcoes': ['Suficiente', 'Insuficiente', 'Não utilizado'],
            'grafico': 'barras',
        },
        {
            'id': 'comentarios', 'tipo': 'texto_livre',
            'titulo': 'Comentários Gerais',
            'grafico': 'nenhum',
        },
    ]


def gerar_respostas(slug, qualidade='alta'):
    """Gera respostas plausíveis baseadas no curso e qualidade."""
    base = 3 if qualidade == 'alta' else 2

    def nota():
        return max(1, min(4, base + random.randint(-1, 1)))

    sec_comp = {it: nota() for it in ITENS_COMPORTAMENTAIS}
    sec_ferr = {
        it: {'Empresa usa': nota(), 'Você usou': nota()}
        for it in ferramentas_por_curso(slug)
    }
    sec_apl = {it: nota() for it in aplicacao_por_curso(slug)}
    sec_exp = {
        it: random.choice(['Suficiente', 'Suficiente', 'Suficiente', 'Insuficiente', 'Não utilizado'])
        for it in ITENS_EXPERIENCIA
    }
    sec_com = (
        'Experiência muito positiva. Pude colocar em prática conhecimentos da graduação '
        'e tive bons feedbacks do supervisor ao longo do período.'
        if qualidade == 'alta' else
        'Estágio razoável. Algumas atividades pouco aderentes à formação, '
        'mas ambiente de trabalho colaborativo.'
    )
    return {
        'preenchido_em': date.today().isoformat(),
        'tipo_relatorio': 'parcial',
        'secoes': {
            'comportamental': sec_comp,
            'ferramentas': sec_ferr,
            'aplicacao': sec_apl,
            'experiencia': sec_exp,
            'comentarios': sec_com,
        }
    }


# ── EXECUÇÃO ────────────────────────────────────────────────────────────

print('🧹 Limpando dados existentes…')
LogDocumento.objects.all().delete()
DocumentoProcesso.objects.all().delete()
ProcessoEstagio.objects.all().delete()
ModeloFormulario.objects.all().delete()
Aluno.objects.all().delete()
SupervisorEmpresa.objects.all().delete()
# Coordenadores precisam ser desvinculados dos cursos antes (FK PROTECT no Curso? Não, SET_NULL)
Curso.objects.update(coordenador=None)
Coordenador.objects.all().delete()
EmpresaConcedente.objects.all().delete()
Curso.objects.all().delete()
Usuario.objects.filter(is_superuser=False).delete()

print('👑 Garantindo superuser admin/admin…')
admin, _ = Usuario.objects.get_or_create(username='admin')
admin.is_superuser = True
admin.is_staff = True
admin.email = 'admin@ibmec.edu.br'
admin.tipo = 'coordenador'
admin.nome = 'Administrador IBMEC'
admin.email_institucional = 'admin@ibmec.edu.br'
admin.set_password('admin')
admin.save()

print('🎓 Criando cursos…')
cursos = []
for nome, _ in CURSOS:
    cursos.append(Curso.objects.create(
        nome=nome,
        carga_horaria_minima_total=300,
        carga_horaria_maxima_diaria=6,
    ))

print('👔 Criando coordenadores e vinculando aos cursos…')
coordenadores = []
for curso_idx, username, nome, departamento in COORDENADORES:
    u = Usuario.objects.create_user(
        username=username, password=PASSWORD, tipo='coordenador',
        nome=nome, email_institucional=f'{username}@ibmec.edu.br',
    )
    c = Coordenador.objects.create(usuario=u, departamento=departamento)
    cursos[curso_idx].coordenador = c
    cursos[curso_idx].save(update_fields=['coordenador'])
    coordenadores.append(c)

print('👨‍🎓 Criando alunos…')
alunos = []
for idx, (curso_idx, username, nome) in enumerate(ALUNOS):
    u = Usuario.objects.create_user(
        username=username, password=PASSWORD, tipo='aluno',
        nome=nome, email_institucional=f'{username}@aluno.ibmec.edu.br',
    )
    a = Aluno.objects.create(
        usuario=u,
        cpf=fake_cpf(idx), rg=fake_rg(idx),
        coeficiente_rendimento=Decimal(str(round(random.uniform(5.0, 9.5), 2))),
        curso=cursos[curso_idx],
        periodo_atual=random.randint(3, 10),
        matriculado_estagio=True,
    )
    alunos.append(a)

print('🏢 Criando empresas…')
empresas = []
for d in EMPRESAS:
    e = EmpresaConcedente.objects.create(aprovada_ibmec=True, **d)
    empresas.append(e)

print('🧑‍💼 Criando supervisores de empresa…')
supervisores = []
for emp_idx, username, nome, cargo in SUPERVISORES:
    u = Usuario.objects.create_user(
        username=username, password=PASSWORD, tipo='supervisor_empresa',
        nome=nome, email_institucional=f'{username}@empresa.com.br',
    )
    s = SupervisorEmpresa.objects.create(usuario=u, empresa=empresas[emp_idx], cargo=cargo)
    supervisores.append(s)

print('📝 Criando modelos de formulário (um por curso)…')
modelos = []
for ci, curso in enumerate(cursos):
    nome, slug = CURSOS[ci]
    m = ModeloFormulario.objects.create(
        curso=curso,
        criado_por=coordenadores[ci],
        titulo=f'Avaliação de Estágio — {nome}',
        secoes=gerar_modelo_secoes(slug),
        ativo=True,
    )
    modelos.append(m)

print('📋 Criando processos de estágio…')
# (aluno_idx, empresa_idx, status, qualidade_avaliacao_ou_None)
PROCESSOS_SPEC = [
    # 3 ativos (com avaliação)
    (4,  0, 'ATIVO',     'alta'),   # Pedro Reis (CDIA)    → Tech Solutions
    (12, 0, 'ATIVO',     'alta'),   # Thiago Pacheco (ENGC) → Tech Solutions
    (16, 0, 'ATIVO',     'media'),  # Felipe Brito (ENGS)  → Tech Solutions
    # 2 pendentes
    (5,  2, 'PENDENTE',  None),     # Isabella Nunes (CDIA) → Banco Capital
    (8,  3, 'PENDENTE',  None),     # Mateus Domingues (PUB) → Agência Criativa
    # 2 aprovados
    (0,  0, 'APROVADO',  None),     # Gabriel Silva (ADM)  → Tech Solutions
    (2,  1, 'APROVADO',  None),     # Fernanda Castro (ARQ) → Construtora
    # 1 encerrado (com avaliação)
    (10, 4, 'ENCERRADO', 'alta'),   # Vinícius Ramos (DIR) → Machado & Associados
    # 1 cancelado
    (14, 1, 'CANCELADO', None),     # André Macedo (ENGP)  → Construtora
    # 1 rejeitado
    (6,  2, 'REJEITADO', None),     # Bruno Cavalcanti (ECO) → Banco Capital
]

processos = []
for aluno_idx, emp_idx, status, qualidade in PROCESSOS_SPEC:
    aluno = alunos[aluno_idx]
    empresa = empresas[emp_idx]
    supervisor = supervisores[emp_idx]
    curso_idx = ALUNOS[aluno_idx][0]
    coord = cursos[curso_idx].coordenador
    modelo = modelos[curso_idx]
    slug = CURSOS[curso_idx][1]

    meses_offset = random.choice([-12, -8, -6, -3, 0, 3])
    inicio = date(2025, 1, 15) + timedelta(days=meses_offset * 30 + random.randint(0, 60))
    fim = inicio + timedelta(days=180)
    horas = random.choice([20, 30])
    valor_bolsa = Decimal(str(random.choice([1200, 1500, 1800, 2000, 2500, 3000])))
    valor_aux = Decimal('200') if random.random() > 0.5 else Decimal('0')

    respostas = gerar_respostas(slug, qualidade) if qualidade else None

    p = ProcessoEstagio.objects.create(
        aluno=aluno,
        empresa=empresa,
        supervisor=supervisor,
        coordenador=coord,
        status=status,
        horas_semanais=horas,
        data_inicio_prevista=inicio,
        data_fim_prevista=fim,
        plano_atividades=(
            f'Atuação em projetos da área de {empresa.areas_atuacao.split(chr(0x00B7))[0].strip()} '
            f'sob supervisão da equipe. Atividades incluem análise, execução e relatórios periódicos '
            f'alinhados ao plano pedagógico do curso de {CURSOS[curso_idx][0]}.'
        ),
        valor_bolsa=valor_bolsa,
        valor_auxilio_transporte=valor_aux,
        modelo_formulario=modelo,
        respostas_formulario=respostas,
        data_inicio_real=inicio if status in ('ATIVO', 'ENCERRADO') else None,
        data_fim_real=fim if status == 'ENCERRADO' else None,
        justificativa_rejeicao=(
            'Documentação incompleta — falta TCE assinado pelo responsável legal.'
            if status == 'REJEITADO' else ''
        ),
    )
    processos.append(p)

print()
print('✅ Banco populado com sucesso!')
print(f'  Cursos:              {Curso.objects.count()}')
print(f'  Coordenadores:       {Coordenador.objects.count()}')
print(f'  Alunos:              {Aluno.objects.count()}')
print(f'  Empresas:            {EmpresaConcedente.objects.count()}')
print(f'  Supervisores:        {SupervisorEmpresa.objects.count()}')
print(f'  Modelos formulário:  {ModeloFormulario.objects.count()}')
print(f'  Processos:           {ProcessoEstagio.objects.count()}')
por_status = {}
for p in ProcessoEstagio.objects.all():
    por_status[p.status] = por_status.get(p.status, 0) + 1
print(f'  Por status:          {por_status}')
print()
print('🔑 Credenciais:')
print('  admin / admin                          (superuser)')
print(f'  <username> / {PASSWORD}                (demais usuários)')
print('  Ex: pedro.reis, fernanda.castro, joao.oliveira, marcos.santiago, …')
