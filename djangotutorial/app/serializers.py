from rest_framework import serializers
from .models import (
    Usuario, Curso, Empresa, Aluno, Coordenador, SolicitacaoEstagio,
    TermoCompromisso, ApoliceSeguro, RelatorioEstagio, AssinaturaDigital,
)


class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = '__all__'


class EmpresaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Empresa
        fields = '__all__'


class AlunoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Aluno
        fields = '__all__'


# ── Serializers de Coordenador ────────────────────────────────────────────────

class UsuarioResumoSerializer(serializers.ModelSerializer):
    """Embutido em CoordenadorSerializer — expõe só nome e email."""
    class Meta:
        model = Usuario
        fields = ['nome', 'email_institucional']


class CoordenadorSerializer(serializers.ModelSerializer):
    usuario = UsuarioResumoSerializer(read_only=True)

    class Meta:
        model = Coordenador
        fields = ['id', 'usuario', 'departamento']


# ── Serializers de Curso ──────────────────────────────────────────────────────

class CoordenadorNomeSerializer(serializers.ModelSerializer):
    """Embutido em CursoSerializer — expõe só o nome do coordenador."""
    nome = serializers.CharField(source='usuario.nome', read_only=True)

    class Meta:
        model = Coordenador
        fields = ['id', 'nome']


class CursoSerializer(serializers.ModelSerializer):
    coordenador = CoordenadorNomeSerializer(read_only=True)
    coordenador_id = serializers.PrimaryKeyRelatedField(
        queryset=Coordenador.objects.all(), source='coordenador', write_only=True,
        required=False, allow_null=True,
    )

    class Meta:
        model = Curso
        fields = ['id', 'nome', 'coordenador', 'coordenador_id', 'carga_horaria_maxima_diaria']


# ── AlunoResumoSerializer ─────────────────────────────────────────────────────

class AlunoResumoSerializer(serializers.ModelSerializer):
    nome = serializers.CharField(source='usuario.nome', read_only=True)
    email = serializers.CharField(source='usuario.email_institucional', read_only=True)
    curso_nome = serializers.CharField(source='curso.nome', read_only=True, default=None)
    tem_processo_ativo = serializers.SerializerMethodField()

    class Meta:
        model = Aluno
        fields = ['id', 'nome', 'email', 'curso_nome', 'matriculado_estagio', 'tem_processo_ativo']

    def get_tem_processo_ativo(self, obj):
        status_inativos = {
            SolicitacaoEstagio.Status.REJEITADO,
            SolicitacaoEstagio.Status.ENCERRADO,
            SolicitacaoEstagio.Status.CANCELADO,
        }
        return obj.solicitacoes.exclude(status__in=status_inativos).exists()


# ── ProcessoResumoSerializer ──────────────────────────────────────────────────

class ProcessoResumoSerializer(serializers.ModelSerializer):
    aluno_nome = serializers.CharField(source='aluno.usuario.nome', read_only=True)
    empresa_nome = serializers.CharField(source='empresa.razao_social', read_only=True)
    curso_nome = serializers.CharField(source='aluno.curso.nome', read_only=True, default=None)
    data_inicio = serializers.DateField(source='data_inicio_prevista', read_only=True)

    class Meta:
        model = SolicitacaoEstagio
        fields = ['id', 'aluno_nome', 'empresa_nome', 'curso_nome', 'status', 'data_inicio']


class SolicitacaoEstagioSerializer(serializers.ModelSerializer):
    """Serializer completo — usado somente por admin."""
    class Meta:
        model = SolicitacaoEstagio
        fields = '__all__'


class CriarSolicitacaoSerializer(serializers.ModelSerializer):
    """
    Serializer para criação de solicitação pelo aluno.
    'aluno', 'status' e 'coordenador' são somente-leitura:
    o servidor os define, o cliente não pode enviá-los.
    """
    class Meta:
        model = SolicitacaoEstagio
        fields = [
            'id', 'empresa', 'horas_semanais',
            'data_inicio_prevista', 'data_fim_prevista',
            'aluno', 'status', 'coordenador',
        ]
        read_only_fields = ['aluno', 'status', 'coordenador']


class AlterarStatusSerializer(serializers.ModelSerializer):
    """
    Serializer para mudança de status pelo coordenador.
    Somente 'status' e 'justificativa_rejeicao' são editáveis.
    Rejeição exige justificativa não-vazia.
    """
    class Meta:
        model = SolicitacaoEstagio
        fields = [
            'id', 'aluno', 'empresa', 'horas_semanais',
            'data_inicio_prevista', 'data_fim_prevista',
            'coordenador', 'status', 'justificativa_rejeicao',
        ]
        read_only_fields = [
            'aluno', 'empresa', 'horas_semanais',
            'data_inicio_prevista', 'data_fim_prevista', 'coordenador',
        ]

    def validate_status(self, value):
        status_permitidos = {
            SolicitacaoEstagio.Status.APROVADO,
            SolicitacaoEstagio.Status.REJEITADO,
            SolicitacaoEstagio.Status.RETIFICACAO_SOLICITADA,
            SolicitacaoEstagio.Status.ATIVO,
            SolicitacaoEstagio.Status.ENCERRADO,
        }
        if value not in status_permitidos:
            raise serializers.ValidationError(
                f"Status inválido. Opções permitidas: {', '.join(status_permitidos)}"
            )
        return value

    def validate(self, data):
        if data.get('status') == SolicitacaoEstagio.Status.REJEITADO:
            justificativa = data.get(
                'justificativa_rejeicao',
                self.instance.justificativa_rejeicao if self.instance else '',
            )
            if not justificativa or not justificativa.strip():
                raise serializers.ValidationError(
                    {'justificativa_rejeicao': 'Obrigatório ao rejeitar uma solicitação.'}
                )
        return data


class TermoCompromissoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TermoCompromisso
        fields = '__all__'


class ApoliceSeguroSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApoliceSeguro
        fields = '__all__'


class RelatorioEstagioSerializer(serializers.ModelSerializer):
    class Meta:
        model = RelatorioEstagio
        fields = '__all__'


class AssinaturaDigitalSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssinaturaDigital
        fields = '__all__'
