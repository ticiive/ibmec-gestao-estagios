from django.db import models
from django.contrib.auth.models import AbstractUser


class Curso(models.Model):
    nome = models.CharField(max_length=200)
    carga_horaria_minima_total = models.PositiveIntegerField(
        help_text='Carga horária mínima total exigida para integralização (horas)'
    )
    carga_horaria_maxima_diaria = models.PositiveIntegerField(
        help_text='Limite diário de horas permitido pela legislação/PPC'
    )

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = 'Curso'
        verbose_name_plural = 'Cursos'


class Empresa(models.Model):
    cnpj = models.CharField(max_length=18, unique=True)
    razao_social = models.CharField(max_length=200)
    areas_atuacao = models.TextField(
        help_text='Áreas de atuação da empresa (texto livre)'
    )
    localizacao = models.CharField(max_length=300)
    email_contato = models.EmailField()
    aprovada_ibmec = models.BooleanField(
        default=False,
        help_text='Empresa verificada e aprovada pela coordenação do IBMEC'
    )

    def __str__(self):
        return self.razao_social

    class Meta:
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'


class Usuario(AbstractUser):
    """
    Usuário base do sistema. AbstractUser já fornece username, password (com hash),
    is_active, is_staff, date_joined, etc. Não adicione campo 'senha' manualmente.
    Aluno e Coordenador herdam deste model via multi-table inheritance.
    """
    nome = models.CharField(max_length=200)
    email_institucional = models.EmailField(unique=True, blank=True, default='')

    def __str__(self):
        return self.nome or self.username

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'


class Aluno(Usuario):
    matricula = models.CharField(max_length=20, unique=True)
    cpf = models.CharField(max_length=14, unique=True)
    rg = models.CharField(max_length=20)
    coeficiente_rendimento = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    curso = models.ForeignKey(
        Curso, on_delete=models.PROTECT, related_name='alunos', null=True, blank=True
    )

    def __str__(self):
        return f'{self.nome} ({self.matricula})'

    class Meta:
        verbose_name = 'Aluno'
        verbose_name_plural = 'Alunos'


class Coordenador(Usuario):
    departamento = models.CharField(max_length=200)

    def __str__(self):
        return f'{self.nome} — {self.departamento}'

    class Meta:
        verbose_name = 'Coordenador'
        verbose_name_plural = 'Coordenadores'


class SolicitacaoEstagio(models.Model):
    class Status(models.TextChoices):
        PENDENTE = 'PENDENTE', 'Pendente'
        APROVADO = 'APROVADO', 'Aprovado'
        REJEITADO = 'REJEITADO', 'Rejeitado'
        RETIFICACAO_SOLICITADA = 'RETIFICACAO_SOLICITADA', 'Retificação Solicitada'
        ATIVO = 'ATIVO', 'Ativo'
        ENCERRADO = 'ENCERRADO', 'Encerrado'

    aluno = models.ForeignKey(
        Aluno, on_delete=models.PROTECT, related_name='solicitacoes'
    )
    empresa = models.ForeignKey(
        Empresa, on_delete=models.PROTECT, related_name='solicitacoes'
    )
    # nullable: coordenador é atribuído quando avalia a solicitação
    coordenador = models.ForeignKey(
        Coordenador, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='solicitacoes'
    )
    status = models.CharField(
        max_length=30, choices=Status.choices, default=Status.PENDENTE
    )
    horas_semanais = models.PositiveIntegerField()
    data_inicio_prevista = models.DateField()
    data_fim_prevista = models.DateField()
    justificativa_rejeicao = models.TextField(blank=True, default='')

    def __str__(self):
        return f'Solicitação #{self.pk} — {self.aluno} @ {self.empresa} [{self.status}]'

    class Meta:
        verbose_name = 'Solicitação de Estágio'
        verbose_name_plural = 'Solicitações de Estágio'


class Documento(models.Model):
    """
    Base abstrata para todos os documentos do processo de estágio.
    Não gera tabela própria no banco — cada subclasse tem a sua.
    """
    class StatusDocumento(models.TextChoices):
        PENDENTE = 'PENDENTE', 'Pendente'
        APROVADO = 'APROVADO', 'Aprovado'
        REJEITADO = 'REJEITADO', 'Rejeitado'

    arquivo = models.FileField(upload_to='documentos/')
    status = models.CharField(
        max_length=20, choices=StatusDocumento.choices, default=StatusDocumento.PENDENTE
    )
    versao = models.PositiveIntegerField(default=1)
    data_upload = models.DateTimeField(auto_now_add=True)
    solicitacao = models.ForeignKey(
        SolicitacaoEstagio,
        on_delete=models.CASCADE,
        related_name='%(class)s_set',
    )

    class Meta:
        abstract = True


class TermoCompromisso(Documento):
    # O plano de atividades fica dentro do TCE, conforme Brainstorming
    plano_atividades = models.TextField()

    def __str__(self):
        return f'TCE — Solicitação #{self.solicitacao_id} (v{self.versao})'

    class Meta:
        verbose_name = 'Termo de Compromisso'
        verbose_name_plural = 'Termos de Compromisso'


class ApoliceSeguro(Documento):
    # Obrigatória antes da aprovação final do estágio
    data_vencimento = models.DateField()

    def __str__(self):
        return f'Apólice — Solicitação #{self.solicitacao_id} (v{self.versao})'

    class Meta:
        verbose_name = 'Apólice de Seguro'
        verbose_name_plural = 'Apólices de Seguro'


class RelatorioEstagio(Documento):
    # Ex.: "Fevereiro/2026" ou "2026-02"
    periodo_referencia = models.CharField(max_length=50)

    def __str__(self):
        return f'Relatório {self.periodo_referencia} — Solicitação #{self.solicitacao_id}'

    class Meta:
        verbose_name = 'Relatório de Estágio'
        verbose_name_plural = 'Relatórios de Estágio'


class AssinaturaDigital(models.Model):
    class Perfil(models.TextChoices):
        ALUNO = 'ALUNO', 'Aluno'
        COORDENADOR = 'COORDENADOR', 'Coordenador'
        EMPRESA = 'EMPRESA', 'Empresa'

    signatario_nome = models.CharField(max_length=200)
    signatario_perfil = models.CharField(max_length=20, choices=Perfil.choices)
    ip_address = models.GenericIPAddressField()
    data_assinatura = models.DateTimeField(auto_now_add=True)

    # Apenas uma das três FKs abaixo é preenchida por registro
    termo_compromisso = models.ForeignKey(
        TermoCompromisso, on_delete=models.CASCADE,
        null=True, blank=True, related_name='assinaturas'
    )
    apolice_seguro = models.ForeignKey(
        ApoliceSeguro, on_delete=models.CASCADE,
        null=True, blank=True, related_name='assinaturas'
    )
    relatorio_estagio = models.ForeignKey(
        RelatorioEstagio, on_delete=models.CASCADE,
        null=True, blank=True, related_name='assinaturas'
    )

    def __str__(self):
        return f'{self.signatario_nome} ({self.signatario_perfil}) — {self.data_assinatura}'

    class Meta:
        verbose_name = 'Assinatura Digital'
        verbose_name_plural = 'Assinaturas Digitais'
