"""
Script de população do banco com dados realistas IBMEC.

Modelo: login por email_institucional. O `username` é derivado automaticamente
do email pelo override de Usuario.save().

Modos de execução:
    python3 populate_db.py                        # standalone
    python3 manage.py shell < populate_db.py      # via Django shell
"""
import os
import sys
import random
from datetime import date, timedelta
from decimal import Decimal

# ── Django setup idempotente ────────────────────────────────────────────
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

random.seed(42)
PASSWORD = 'ibmec2026'


def criar_usuario(email, password, tipo, nome, **kwargs):
    """Helper: cria Usuario via create_user (faz hash da senha corretamente).

    NUNCA usar Usuario.objects.create() — esse método salva a senha em texto
    puro e o login quebra. Sempre create_user (ou create_superuser para admin).
    """
    return Usuario.objects.create_user(
        username=email,                # auto-sincronizado pelo save() do Usuario
        email_institucional=email,
        password=password,             # create_user chama set_password internamente
        tipo=tipo,
        nome=nome,
        **kwargs,
    )


# ── 14 CURSOS ──────────────────────────────────────────────────────────
CURSOS = [
    ('Administração', 'adm'),
    ('Ciências Contábeis', 'ctb'),
    ('Ciências Econômicas', 'eco'),
    ('Direito', 'dir'),
    ('Relações Internacionais', 'ri'),
    ('Comunicação Social – Publicidade e Propaganda', 'pub'),
    ('Arquitetura e Urbanismo', 'arq'),
    ('Engenharia Civil', 'engcv'),
    ('Engenharia de Computação', 'engcc'),
    ('Engenharia Mecânica', 'engmc'),
    ('Engenharia de Produção', 'engp'),
    ('Engenharia de Software', 'engs'),
    ('Análise e Desenvolvimento de Sistemas', 'ads'),
    ('Ciência de Dados e Inteligência Artificial', 'cdia'),
    ('Defesa Cibernética', 'defc'),
]

# ── 8 COORDENADORES (1 coord pode coordenar N cursos) ──────────────────
# (nome, email, lista de slugs de curso)
COORDENADORES = [
    ('Talita de Oliveira Trindade',  'talita.trindade@ibmec.edu.br',    ['adm', 'ctb']),
    ('Gustavo Herkenhoff Moreira',   'gustavo.moreira@ibmec.edu.br',    ['eco']),
    ('Michele Pedrosa Paumgartten',  'michele.paumgartten@ibmec.edu.br',['dir']),
    ('Renato Salgado Mendes',        'renato.mendes@ibmec.edu.br',      ['ri']),
    ('Victor Azevedo',               'victor.azevedo@ibmec.edu.br',     ['pub']),
    ('Ticianne Ribeiro de Souza',    'ticianne.souza@ibmec.edu.br',     ['arq']),
    ('Clayton Jones Alves da Silva', 'clayton.silva@ibmec.edu.br',      ['engcv', 'engcc', 'engmc', 'engp', 'engs']),
    ('Thiago Silva de Souza',        'thiago.souza@ibmec.edu.br',       ['ads', 'cdia', 'defc']),
]

# ── VISÃO GLOBAL ────────────────────────────────────────────────────────
VISAO_GLOBAL_USERS = [
    ('Ana Paula Mendes',         'ana.mendes@ibmec.edu.br',        'secretaria'),
    ('Carlos Eduardo Souza',     'carlos.souza@ibmec.edu.br',      'casa'),
    ('Roberto Figueiredo',       'roberto.figueiredo@ibmec.edu.br','reitor'),
    ('Claudia Amaral',           'claudia.amaral@ibmec.edu.br',    'pro_reitor'),
]

# ── 30 ALUNOS (2 por curso) ─────────────────────────────────────────────
# (nome, email_local, slug_curso, periodo, cr)
ALUNOS_SPEC = [
    # adm
    ('Pedro Henrique Alves',     'pedro.alves',      'adm',   6, 7.80),
    ('Juliana Ferreira Santos',  'juliana.santos',   'adm',   8, 8.50),
    # ctb
    ('Rafael Tavares Lemos',     'rafael.lemos',     'ctb',   5, 7.40),
    ('Beatriz Almeida Soares',   'beatriz.soares',   'ctb',   7, 8.10),
    # eco
    ('Bruno Cavalcanti Lima',    'bruno.cavalcanti', 'eco',   7, 7.20),
    ('Larissa Moura Teixeira',   'larissa.moura',    'eco',   9, 8.90),
    # dir
    ('Rodrigo Nascimento Pinto', 'rodrigo.nascimento','dir', 10, 9.20),
    ('Amanda Cristina Lopes',    'amanda.lopes',     'dir',   8, 8.40),
    # ri
    ('Sophia Marques Duarte',    'sophia.marques',   'ri',    7, 9.00),
    ('André Luis Fonseca',       'andre.fonseca',    'ri',    5, 7.10),
    # pub
    ('Mateus Domingues Faria',   'mateus.domingues', 'pub',   4, 6.90),
    ('Camilla Teixeira Vaz',     'camilla.teixeira', 'pub',   6, 7.60),
    # arq
    ('Fernanda Oliveira Castro', 'fernanda.castro',  'arq',   8, 8.20),
    ('Gabriel Rocha Mendes',     'gabriel.mendes',   'arq',   6, 7.40),
    # engcv
    ('Lucas Pereira Maia',       'lucas.maia',       'engcv', 7, 7.90),
    ('Mariana Borges Ramos',     'mariana.borges',   'engcv', 5, 8.30),
    # engcc
    ('Thiago Martins Andrade',   'thiago.martins',   'engcc', 6, 8.10),
    ('Natália Correia Souza',    'natalia.correia',  'engcc', 8, 7.80),
    # engmc
    ('Eduardo Vieira Campos',    'eduardo.campos',   'engmc', 6, 7.50),
    ('Renata Pinheiro Cardoso',  'renata.cardoso',   'engmc', 9, 8.80),
    # engp
    ('Felipe Augusto Gomes',     'felipe.gomes',     'engp',  5, 7.30),
    ('Bianca Cardoso Nogueira',  'bianca.cardoso',   'engp',  7, 8.60),
    # engs
    ('Diego Henrique Barros',    'diego.barros',     'engs',  4, 8.80),
    ('Letícia Prado Monteiro',   'leticia.monteiro', 'engs',  6, 7.50),
    # ads
    ('Vinicius Souza Antunes',   'vinicius.antunes', 'ads',   3, 7.20),
    ('Camila Ribeiro Faria',     'camila.faria',     'ads',   5, 8.00),
    # cdia
    ('Pedro Vinícius Reis',      'pedro.reis',       'cdia',  3, 9.10),
    ('Isabella Nunes Carvalho',  'isabella.nunes',   'cdia',  5, 8.70),
    # defc
    ('Marcelo Aguiar Brito',     'marcelo.brito',    'defc',  4, 8.40),
    ('Carolina Lima Tavares',    'carolina.lima',    'defc',  6, 7.70),
]

# ── 8 EMPRESAS ──────────────────────────────────────────────────────────
EMPRESAS = [
    {
        'razao_social': 'Tech Solutions Ltda', 'cnpj': '12.345.678/0001-90',
        'areas_atuacao': 'Tecnologia · Desenvolvimento de Software · Dados',
        'localizacao': 'Rio de Janeiro, RJ', 'email_contato': 'contato@techsolutions.com.br',
        'responsavel_legal_nome': 'Roberto Mendes Cardoso', 'responsavel_legal_cargo': 'Diretor Executivo',
        'descricao': 'Empresa de tecnologia com foco em soluções de software.',
    },
    {
        'razao_social': 'Construtora Horizonte S.A.', 'cnpj': '23.456.789/0001-01',
        'areas_atuacao': 'Construção Civil · Engenharia · Projetos Estruturais',
        'localizacao': 'Rio de Janeiro, RJ', 'email_contato': 'rh@horizonte.com.br',
        'responsavel_legal_nome': 'Cláudia Lima Vasconcellos', 'responsavel_legal_cargo': 'Presidente',
        'descricao': 'Construtora atuante em obras residenciais e comerciais.',
    },
    {
        'razao_social': 'Banco Capital Investimentos', 'cnpj': '34.567.890/0001-12',
        'areas_atuacao': 'Finanças · Mercado de Capitais · Wealth Management',
        'localizacao': 'São Paulo, SP', 'email_contato': 'estagio@bancocapital.com.br',
        'responsavel_legal_nome': 'Henrique Sampaio Marques', 'responsavel_legal_cargo': 'CEO',
        'descricao': 'Banco de investimentos focado em wealth management e M&A.',
    },
    {
        'razao_social': 'Agência Criativa Digital', 'cnpj': '45.678.901/0001-23',
        'areas_atuacao': 'Marketing · Publicidade · Comunicação Digital',
        'localizacao': 'Rio de Janeiro, RJ', 'email_contato': 'rh@agcriativa.com.br',
        'responsavel_legal_nome': 'Patrícia Lobo Fernandes', 'responsavel_legal_cargo': 'CEO',
        'descricao': 'Agência full-service de marketing digital e branding.',
    },
    {
        'razao_social': 'Escritório Machado & Associados', 'cnpj': '56.789.012/0001-34',
        'areas_atuacao': 'Advocacia · Direito Empresarial · Contencioso',
        'localizacao': 'Rio de Janeiro, RJ', 'email_contato': 'contato@machadoassoc.adv.br',
        'responsavel_legal_nome': 'José Machado Filho', 'responsavel_legal_cargo': 'Sócio Fundador',
        'descricao': 'Escritório de advocacia full-service.',
    },
    {
        'razao_social': 'Global Trade Consultoria', 'cnpj': '67.890.123/0001-45',
        'areas_atuacao': 'Comércio Exterior · Logística Internacional',
        'localizacao': 'Rio de Janeiro, RJ', 'email_contato': 'rh@globaltrade.com.br',
        'responsavel_legal_nome': 'Ana Paula Aguiar', 'responsavel_legal_cargo': 'Diretora de Operações',
        'descricao': 'Consultoria em comércio exterior e internacionalização.',
    },
    {
        'razao_social': 'Indústria Metalúrgica Aço Forte', 'cnpj': '78.901.234/0001-56',
        'areas_atuacao': 'Engenharia · Metalurgia · Fabricação Industrial',
        'localizacao': 'Rio de Janeiro, RJ', 'email_contato': 'rh@acoforte.ind.br',
        'responsavel_legal_nome': 'Marcos Henrique Pereira', 'responsavel_legal_cargo': 'Diretor Industrial',
        'descricao': 'Indústria metalúrgica com operações de transformação e usinagem.',
    },
    {
        'razao_social': 'DataMind Analytics', 'cnpj': '89.012.345/0001-67',
        'areas_atuacao': 'Dados · Inteligência Artificial · BI',
        'localizacao': 'Rio de Janeiro, RJ', 'email_contato': 'rh@datamind.ai',
        'responsavel_legal_nome': 'Letícia Sampaio Furtado', 'responsavel_legal_cargo': 'CEO',
        'descricao': 'Consultoria em ciência de dados e modelos de IA aplicada.',
    },
]

# ── 8 SUPERVISORES (1 por empresa) ──────────────────────────────────────
# (nome, email, empresa_idx, cargo)
SUPERVISORES = [
    ('Marcos Vinícius Santiago', 'marcos.santiago@techsolutions.com.br', 0, 'Diretor de Tecnologia'),
    ('Eliana Cristina Branco',   'eliana.branco@horizonte.com.br',       1, 'Engenheira Sênior'),
    ('Antonio Carlos Macedo',    'antonio.macedo@bancocapital.com.br',   2, 'Gerente de Operações'),
    ('Daniela Souza Rangel',     'daniela.rangel@agcriativa.com.br',     3, 'Diretora Criativa'),
    ('Roberto Almeida Pinto',    'roberto.pinto@machadoassoc.adv.br',    4, 'Sócio Advogado'),
    ('Vanessa Lima Cardoso',     'vanessa.cardoso@globaltrade.com.br',   5, 'Gerente de Comex'),
    ('Paulo Roberto Magalhães',  'paulo.magalhaes@acoforte.ind.br',      6, 'Coordenador de Engenharia'),
    ('Mariana Tavares Coelho',   'mariana.tavares@datamind.ai',          7, 'Líder de Data Science'),
]


# ── CPFs/RGs fictícios determinísticos ──────────────────────────────────
def fake_cpf(i):
    return f'{(100+i):03d}.{(200+i*3) % 1000:03d}.{(300+i*5) % 1000:03d}-{(10+i) % 100:02d}'


def fake_rg(i):
    return f'{(10+i) % 100:02d}.{(100+i*2) % 1000:03d}.{(200+i*3) % 1000:03d}-{i % 10}'


def fake_matricula(i):
    return f'2023{(100000 + i*137) % 1000000:06d}'


# ── Especialização por curso para seções do formulário ──────────────────
AREAS_POR_CURSO = {
    'arq':   ['Interiores residenciais', 'Interiores comerciais', 'Edificações residenciais', 'Edificações comerciais', 'Restauração/patrimônio', 'Paisagismo', 'Projetos complementares'],
    'cdia':  ['Análise exploratória', 'ML supervisionado', 'ML não supervisionado', 'NLP', 'Computer Vision', 'BI/visualização', 'Engenharia de dados'],
    'engs':  ['Backend / APIs', 'Frontend web', 'Mobile', 'DevOps / CI/CD', 'Banco de dados', 'Cloud', 'QA / testes'],
    'engcc': ['Sistemas embarcados', 'Redes', 'Sistemas operacionais', 'Segurança', 'IoT', 'Cloud', 'IA'],
    'engcv': ['Estruturas', 'Geotecnia', 'Hidráulica', 'Saneamento', 'Construção', 'Orçamento'],
    'engmc': ['Projeto mecânico', 'Manufatura', 'Manutenção', 'Termodinâmica', 'Materiais', 'Automação'],
    'engp':  ['PCP', 'Qualidade', 'Lean', 'Logística', 'Custos', 'Gestão de projetos'],
    'ads':   ['Backend', 'Frontend', 'Banco de dados', 'DevOps', 'Cloud', 'Testes'],
    'defc':  ['Pentest', 'SOC / monitoramento', 'Resposta a incidentes', 'Criptografia', 'Hardening', 'Compliance / LGPD'],
    'adm':   ['Gestão de pessoas', 'Finanças', 'Marketing', 'Operações', 'Estratégia', 'Logística'],
    'ctb':   ['Contabilidade societária', 'Tributária', 'Auditoria', 'Custos', 'Controladoria', 'Análise de balanços'],
    'eco':   ['Macroeconomia', 'Microeconomia', 'Econometria', 'Mercado financeiro', 'Análise de risco', 'Setor público'],
    'pub':   ['Planejamento de campanha', 'Criação', 'Redação', 'Mídia paga', 'Branding', 'Métricas'],
    'dir':   ['Civil', 'Empresarial', 'Trabalhista', 'Tributário', 'Contencioso', 'Consultivo'],
    'ri':    ['Política externa', 'Comércio exterior', 'Cooperação internacional', 'Diplomacia', 'Análise de cenários'],
}

DISCIPLINAS_POR_CURSO = {
    'arq':   ['Projeto', 'Teoria e História', 'Estruturas', 'Conforto/Materiais', 'Instalações', 'Desenho a mão'],
    'cdia':  ['Estatística', 'Cálculo', 'Programação', 'Banco de Dados', 'Machine Learning', 'Visualização'],
    'engs':  ['Algoritmos', 'Engenharia de Software', 'Banco de Dados', 'Redes', 'Sistemas Distribuídos'],
    'engcc': ['Algoritmos', 'Programação', 'Sistemas Digitais', 'Redes', 'Eletrônica', 'Cálculo'],
    'engcv': ['Cálculo', 'Mecânica', 'Estruturas', 'Hidráulica', 'Topografia', 'Materiais'],
    'engmc': ['Cálculo', 'Termodinâmica', 'Mecânica dos Fluidos', 'Mecanismos', 'Materiais', 'Manufatura'],
    'engp':  ['Pesquisa Operacional', 'Estatística e Qualidade', 'PCP', 'Logística', 'Gestão de Projetos'],
    'ads':   ['Algoritmos', 'Programação', 'Banco de Dados', 'Web', 'Redes', 'Gestão de Projetos'],
    'defc':  ['Redes', 'Sistemas Operacionais', 'Criptografia', 'Programação', 'Computação Forense', 'Hardening'],
    'adm':   ['Gestão de Pessoas', 'Finanças', 'Marketing', 'Contabilidade', 'Estratégia', 'Operações'],
    'ctb':   ['Contabilidade Geral', 'Custos', 'Tributária', 'Societária', 'Auditoria', 'Controladoria'],
    'eco':   ['Macroeconomia', 'Microeconomia', 'Econometria', 'Estatística', 'Cálculo', 'Finanças'],
    'pub':   ['Teoria da Comunicação', 'Redação Publicitária', 'Mídia', 'Branding', 'Pesquisa de Mercado'],
    'dir':   ['Civil', 'Empresarial', 'Trabalhista', 'Constitucional', 'Processual', 'Tributário'],
    'ri':    ['Teoria das RI', 'Política Externa Brasileira', 'Economia Internacional', 'Direito Internacional'],
}

SOFTWARES_POR_CURSO = {
    'arq':   ['Word', 'Excel', 'AutoCAD', 'SketchUp', 'Revit', 'Photoshop', 'VRay'],
    'cdia':  ['Python básico', 'Python avançado', 'SQL', 'R', 'Power BI', 'Git', 'Docker'],
    'engs':  ['Python', 'JavaScript', 'Java', 'SQL', 'Git', 'Docker', 'Kubernetes'],
    'engcc': ['C/C++', 'Python', 'Java', 'SQL', 'Linux', 'Wireshark', 'Git'],
    'engcv': ['Excel', 'AutoCAD', 'Revit', 'SAP2000', 'Eberick', 'Project'],
    'engmc': ['SolidWorks', 'AutoCAD', 'Inventor', 'Matlab', 'Ansys', 'Excel'],
    'engp':  ['Excel', 'Power BI', 'MS Project', 'SAP', 'Minitab', 'Python'],
    'ads':   ['Python', 'JavaScript', 'SQL', 'Git', 'Docker', 'Linux'],
    'defc':  ['Linux', 'Wireshark', 'Nmap', 'Burp Suite', 'Python', 'Splunk'],
    'adm':   ['Excel', 'Power BI', 'SAP', 'Word', 'PowerPoint', 'CRM'],
    'ctb':   ['Excel avançado', 'SAP', 'Sistema Contábil', 'eSocial', 'SPED'],
    'eco':   ['Excel', 'R', 'Stata', 'Python', 'Bloomberg', 'Power BI'],
    'pub':   ['Photoshop', 'Illustrator', 'InDesign', 'After Effects', 'Premiere', 'Figma'],
    'dir':   ['PJe', 'JusBrasil', 'LexML', 'Word', 'Excel'],
    'ri':    ['Excel', 'Word', 'PowerPoint', 'Bloomberg', 'Inglês avançado'],
}

ITENS_COMPORTAMENTAIS_DETALHADOS = [
    {'nome': 'Visão',         'descricao': 'Olhar estratégico, leitura de cenários, compreensão das circunstâncias e interpretação de regras e sistemas.'},
    {'nome': 'Adaptabilidade','descricao': 'Capacidade de aprendizagem, abertura para inovar, coragem de explorar novos processos.'},
    {'nome': 'Centralidade',  'descricao': 'Autoconhecimento, controle emocional, resiliência e autoestima.'},
    {'nome': 'Empatia',       'descricao': 'Interação em grupos, comunicação efetiva, respeito mútuo e honestidade.'},
]
ITENS_COMPORTAMENTAIS = [d['nome'] for d in ITENS_COMPORTAMENTAIS_DETALHADOS]

ITENS_EXPERIENCIA = [
    'Atividades vs formação acadêmica', 'Orientação do supervisor', 'Feedback do supervisor',
    'Condições de trabalho', 'Remuneração vs mercado', 'Relacionamento com equipe',
    'Sua produtividade', 'Indicaria a empresa',
]


def gerar_modelo_secoes(slug):
    """Modelo de formulário alinhado ao docx oficial — 7 seções."""
    return [
        {
            'id': 'estagiario', 'tipo': 'auto', 'titulo': '1. Estagiário / Aluno',
            'itens': ['Nome', 'Matrícula', 'Curso', 'Semestre atual', 'Data de entrada', 'Data de saída',
                      'Horas/semana', 'Semanas trabalhadas', 'Horas totais', 'Remuneração média mensal'],
            'grafico': 'nenhum',
        },
        {
            'id': 'empresa', 'tipo': 'auto', 'titulo': '2. Concedente / Empresa',
            'itens': ['Empresa', 'Telefone', 'Website', 'Gestor direto', 'Email do gestor'],
            'grafico': 'nenhum',
        },
        {
            'id': 'area_atuacao', 'tipo': 'checkbox_duplo', 'titulo': '3. Área de Atuação',
            'itens': AREAS_POR_CURSO.get(slug, AREAS_POR_CURSO['adm']),
            'colunas': ['Atuação da empresa: Obra', 'Atuação da empresa: Projeto', 'Sua atuação: Obra', 'Sua atuação: Projeto'],
            'grafico': 'barras_agrupadas',
            'campo_texto': 'Descreva as principais atividades desenvolvidas no seu estágio',
        },
        {
            'id': 'aplicacao_conhecimento', 'tipo': 'escala_3',
            'titulo': '4. Avaliação da Aplicação do Conhecimento',
            'descricao': 'Escolha se foi: Suficiente, Insuficiente ou Não utilizado',
            'itens': DISCIPLINAS_POR_CURSO.get(slug, DISCIPLINAS_POR_CURSO['adm']),
            'opcoes': ['Suficiente', 'Insuficiente', 'Não utilizado'],
            'grafico': 'barras',
            'campo_texto': 'Comentário sobre a aplicabilidade do conhecimento acadêmico',
        },
        {
            'id': 'softwares', 'tipo': 'escala_1_4_multi',
            'titulo': '5. Utilização de Softwares',
            'descricao': '1-muito; 2-médio; 3-pouco; 4-nada',
            'itens': SOFTWARES_POR_CURSO.get(slug, SOFTWARES_POR_CURSO['adm']),
            'colunas': ['Pela empresa', 'Por você', 'Se sentiu apto'],
            'grafico': 'barras_agrupadas',
            'campo_texto': 'Descreva sua experiência com o uso de softwares no estágio',
        },
        {
            'id': 'comportamental', 'tipo': 'escala_1_4',
            'titulo': '6. Inteligência Comportamental',
            'descricao': '1-ruim; 2-regular; 3-bom; 4-ótimo',
            'itens_detalhados': ITENS_COMPORTAMENTAIS_DETALHADOS,
            'itens': ITENS_COMPORTAMENTAIS,
            'grafico': 'radar',
        },
        {
            'id': 'experiencia', 'tipo': 'escala_1_4',
            'titulo': '7. Avaliação da Experiência',
            'descricao': '1-ruim; 2-regular; 3-bom; 4-ótimo',
            'itens': ITENS_EXPERIENCIA,
            'grafico': 'barras',
            'campo_efetivacao': True,
            'campo_texto_positivo': 'Pontos positivos sobre sua experiência',
            'campo_texto_negativo': 'Pontos negativos sobre sua experiência',
        },
    ]


def gerar_respostas(slug, qualidade='alta'):
    base = 3 if qualidade == 'alta' else 2
    nota = lambda: max(1, min(4, base + random.randint(-1, 1)))

    cols_area = ['Atuação da empresa: Obra', 'Atuação da empresa: Projeto', 'Sua atuação: Obra', 'Sua atuação: Projeto']
    areas = AREAS_POR_CURSO.get(slug, [])
    sec_areas = {}
    for it in random.sample(areas, k=min(4, len(areas))):
        sec_areas[it] = random.sample(cols_area, k=random.randint(1, 3))

    return {
        'preenchido_em': date.today().isoformat(),
        'tipo_relatorio': 'parcial',
        'secoes': {
            'area_atuacao': sec_areas,
            'area_atuacao_texto': 'Trabalhei em projetos diversificados com foco em entregas reais.',
            'aplicacao_conhecimento': {it: random.choice(['Suficiente', 'Suficiente', 'Insuficiente', 'Não utilizado'])
                                       for it in DISCIPLINAS_POR_CURSO.get(slug, [])},
            'aplicacao_conhecimento_texto': 'A base teórica foi muito útil durante o estágio.',
            'softwares': {it: {'Pela empresa': nota(), 'Por você': nota(), 'Se sentiu apto': nota()}
                          for it in random.sample(SOFTWARES_POR_CURSO.get(slug, []),
                                                  k=min(5, len(SOFTWARES_POR_CURSO.get(slug, []))))},
            'softwares_texto': 'Aprofundei o uso das ferramentas principais.',
            'comportamental': {it: nota() for it in ITENS_COMPORTAMENTAIS},
            'experiencia': {it: nota() for it in ITENS_EXPERIENCIA},
            'experiencia_efetivacao': random.choice(['Sim', 'Não']),
            'experiencia_texto_positivo': 'Equipe acolhedora e bom acompanhamento.',
            'experiencia_texto_negativo': 'Carga eventualmente intensa em períodos de pico.',
        }
    }


# ════════════════════════════════════════════════════════════════════════
#  EXECUÇÃO
# ════════════════════════════════════════════════════════════════════════
print('🧹 Limpando dados existentes…')
LogDocumento.objects.all().delete()
DocumentoProcesso.objects.all().delete()
ProcessoEstagio.objects.all().delete()
ModeloFormulario.objects.all().delete()
Aluno.objects.all().delete()
SupervisorEmpresa.objects.all().delete()
Curso.objects.update(coordenador=None)
Coordenador.objects.all().delete()
EmpresaConcedente.objects.all().delete()
Curso.objects.all().delete()
Usuario.objects.all().delete()  # inclui superusers — vamos recriar admin abaixo

print('👑 Criando superuser admin@ibmec.edu.br / admin…')
admin_user = Usuario.objects.create_superuser(
    username='admin@ibmec.edu.br',
    email_institucional='admin@ibmec.edu.br',
    password='admin',
    tipo='coordenador',
    nome='Administrador IBMEC',
)

print('🏛  Criando perfis de visão global (Secretaria, CASA, Reitor, Pró-Reitor)…')
for nome, email, tipo in VISAO_GLOBAL_USERS:
    criar_usuario(email, PASSWORD, tipo, nome)

print('🎓 Criando 14 cursos…')
cursos_by_slug = {}
for nome, slug in CURSOS:
    c = Curso.objects.create(
        nome=nome,
        carga_horaria_minima_total=300,
        carga_horaria_maxima_diaria=6,
    )
    cursos_by_slug[slug] = c

print('👔 Criando 8 coordenadores e vinculando cursos…')
coords_by_email = {}
for nome, email, slugs in COORDENADORES:
    u = criar_usuario(email, PASSWORD, 'coordenador', nome)
    c = Coordenador.objects.create(usuario=u, departamento=', '.join(s.upper() for s in slugs))
    coords_by_email[email] = c
    for slug in slugs:
        cursos_by_slug[slug].coordenador = c
        cursos_by_slug[slug].save(update_fields=['coordenador'])

print('👨‍🎓 Criando 30 alunos (2 por curso)…')
alunos_by_email = {}
for idx, (nome, email_local, slug, periodo, cr) in enumerate(ALUNOS_SPEC):
    email = f'{email_local}@aluno.ibmec.edu.br'
    u = criar_usuario(email, PASSWORD, 'aluno', nome)
    a = Aluno.objects.create(
        usuario=u,
        cpf=fake_cpf(idx),
        rg=fake_rg(idx),
        coeficiente_rendimento=Decimal(str(cr)),
        curso=cursos_by_slug[slug],
        periodo_atual=periodo,
        matriculado_estagio=True,
    )
    # Matrícula → username herda do email; mantemos username = email
    alunos_by_email[email] = a

print('🏢 Criando 8 empresas…')
empresas = []
for d in EMPRESAS:
    e = EmpresaConcedente.objects.create(aprovada_ibmec=True, **d)
    empresas.append(e)

print('🧑‍💼 Criando 8 supervisores de empresa…')
supervisores = []
for nome, email, emp_idx, cargo in SUPERVISORES:
    u = criar_usuario(email, PASSWORD, 'supervisor_empresa', nome)
    s = SupervisorEmpresa.objects.create(usuario=u, empresa=empresas[emp_idx], cargo=cargo)
    supervisores.append(s)

print('📝 Criando 14 modelos de formulário (1 por curso)…')
modelos_by_slug = {}
for nome, slug in CURSOS:
    c = cursos_by_slug[slug]
    m = ModeloFormulario.objects.create(
        curso=c,
        criado_por=c.coordenador,
        titulo=f'Avaliação de Estágio — {nome}',
        secoes=gerar_modelo_secoes(slug),
        ativo=True,
    )
    modelos_by_slug[slug] = m

print('📋 Criando 15 processos de estágio com status variados…')
# (email_aluno, empresa_idx, status, qualidade ou None)
PROCESSOS_SPEC = [
    # 4 ATIVO (com respostas)
    ('pedro.reis@aluno.ibmec.edu.br',         7, 'ATIVO',     'alta'),   # CDIA → DataMind
    ('isabella.nunes@aluno.ibmec.edu.br',     0, 'ATIVO',     'alta'),   # CDIA → Tech
    ('diego.barros@aluno.ibmec.edu.br',       0, 'ATIVO',     'media'),  # ENGS → Tech
    ('fernanda.castro@aluno.ibmec.edu.br',    1, 'ATIVO',     'alta'),   # ARQ → Construtora
    # 3 PENDENTE
    ('thiago.martins@aluno.ibmec.edu.br',     0, 'PENDENTE',  None),     # ENGCC → Tech
    ('mateus.domingues@aluno.ibmec.edu.br',   3, 'PENDENTE',  None),     # PUB → Agência
    ('amanda.lopes@aluno.ibmec.edu.br',       4, 'PENDENTE',  None),     # DIR → Machado
    # 3 APROVADO
    ('pedro.alves@aluno.ibmec.edu.br',        0, 'APROVADO',  None),     # ADM → Tech
    ('lucas.maia@aluno.ibmec.edu.br',         1, 'APROVADO',  None),     # ENGCV → Construtora
    ('felipe.gomes@aluno.ibmec.edu.br',       6, 'APROVADO',  None),     # ENGP → Metalúrgica
    # 2 ENCERRADO (com respostas)
    ('rodrigo.nascimento@aluno.ibmec.edu.br', 4, 'ENCERRADO', 'alta'),   # DIR → Machado
    ('larissa.moura@aluno.ibmec.edu.br',      2, 'ENCERRADO', 'alta'),   # ECO → Banco
    # 2 CANCELADO
    ('eduardo.campos@aluno.ibmec.edu.br',     6, 'CANCELADO', None),     # ENGMC → Metalúrgica
    ('andre.fonseca@aluno.ibmec.edu.br',      5, 'CANCELADO', None),     # RI → Global Trade
    # 1 REJEITADO
    ('bruno.cavalcanti@aluno.ibmec.edu.br',   2, 'REJEITADO', None),     # ECO → Banco
]

slug_by_aluno_email = {f'{e[1]}@aluno.ibmec.edu.br': e[2] for e in ALUNOS_SPEC}

for email_aluno, emp_idx, status, qualidade in PROCESSOS_SPEC:
    aluno = alunos_by_email[email_aluno]
    slug = slug_by_aluno_email[email_aluno]
    empresa = empresas[emp_idx]
    supervisor = supervisores[emp_idx]
    coord = cursos_by_slug[slug].coordenador
    modelo = modelos_by_slug[slug]

    meses_offset = random.choice([-14, -10, -6, -3, 0, 3])
    inicio = date(2025, 1, 15) + timedelta(days=meses_offset * 30 + random.randint(0, 60))
    fim = inicio + timedelta(days=180)
    horas = random.choice([20, 30])
    valor_bolsa = Decimal(str(random.choice([1200, 1500, 1800, 2000, 2500, 3000])))
    valor_aux = Decimal('200') if random.random() > 0.5 else Decimal('0')

    respostas = gerar_respostas(slug, qualidade) if qualidade else None

    ProcessoEstagio.objects.create(
        aluno=aluno, empresa=empresa, supervisor=supervisor, coordenador=coord,
        status=status,
        horas_semanais=horas,
        data_inicio_prevista=inicio,
        data_fim_prevista=fim,
        plano_atividades=(
            f'Atuação em projetos de {empresa.areas_atuacao.split(chr(0x00B7))[0].strip()} '
            f'sob supervisão da equipe.'
        ),
        valor_bolsa=valor_bolsa,
        valor_auxilio_transporte=valor_aux,
        modelo_formulario=modelo,
        respostas_formulario=respostas,
        data_inicio_real=inicio if status in ('ATIVO', 'ENCERRADO') else None,
        data_fim_real=fim if status == 'ENCERRADO' else None,
        justificativa_rejeicao=('Documentação incompleta — falta TCE assinado.' if status == 'REJEITADO' else ''),
    )

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
print('═' * 72)
print('LOGINS DE TESTE (email + senha)')
print('═' * 72)
print()
print('ADMIN:')
print('  admin@ibmec.edu.br                          | admin')
print()
print('COORDENADORES:')
for nome, email, slugs in COORDENADORES:
    cursos_str = ', '.join(slug.upper() for slug in slugs)
    print(f'  {email:<43} | {PASSWORD} | {cursos_str}')
print()
print('VISÃO GLOBAL:')
for nome, email, tipo in VISAO_GLOBAL_USERS:
    print(f'  {email:<43} | {PASSWORD} | {tipo}')
print()
print('ALUNOS (amostra de 6 — todos com senha ' + PASSWORD + '):')
amostra = ['pedro.reis', 'isabella.nunes', 'fernanda.castro', 'rodrigo.nascimento', 'diego.barros', 'sophia.marques']
for local in amostra:
    spec = next(s for s in ALUNOS_SPEC if s[1] == local)
    nome, _, slug, periodo, cr = spec
    nome_curso = dict(CURSOS).get(next(n for n, sl in CURSOS if sl == slug)) if False else next(n for n, sl in CURSOS if sl == slug)
    print(f'  {local}@aluno.ibmec.edu.br'.ljust(45) + f' | {PASSWORD} | {nome_curso}')
print()
print('SUPERVISORES (todos com senha ' + PASSWORD + '):')
for nome, email, emp_idx, cargo in SUPERVISORES:
    print(f'  {email:<43} | {PASSWORD} | {empresas[emp_idx].razao_social[:30]}')
print('═' * 72)
