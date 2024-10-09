# escola/admin.py

from django.contrib import admin
from .models import CustomUser, Escola, Diretor, Secretario, Professor, Disciplina, Aluno, TipoTurma, Turma, RegistroAula, RegistroFalta, RegistroNota
from .models import CalendarioEscolar

# Registro dos modelos

class CalendarioEscolarAdmin(admin.ModelAdmin):
    list_display = ('ano', 'inicio_ano_letivo', 'fim_ano_letivo')
    search_fields = ('ano',)
    list_filter = ('ano',)

admin.site.register(CalendarioEscolar, CalendarioEscolarAdmin)

admin.site.register(CustomUser)
admin.site.register(Escola)
admin.site.register(Diretor)
admin.site.register(Secretario)
admin.site.register(Professor)
admin.site.register(Disciplina)
admin.site.register(Aluno)
admin.site.register(TipoTurma)
admin.site.register(Turma)
admin.site.register(RegistroAula)
admin.site.register(RegistroFalta)
admin.site.register(RegistroNota)
