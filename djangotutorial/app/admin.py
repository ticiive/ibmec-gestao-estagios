from django.contrib import admin
from .models import (
    Curso, Empresa,
    Usuario, Aluno, Coordenador,
    SolicitacaoEstagio,
    TermoCompromisso, ApoliceSeguro, RelatorioEstagio,
    AssinaturaDigital,
)

admin.site.register(Curso)
admin.site.register(Empresa)
admin.site.register(Usuario)   # entrada separada para o usuário base
admin.site.register(Aluno)
admin.site.register(Coordenador)
admin.site.register(SolicitacaoEstagio)
admin.site.register(TermoCompromisso)
admin.site.register(ApoliceSeguro)
admin.site.register(RelatorioEstagio)
admin.site.register(AssinaturaDigital)
