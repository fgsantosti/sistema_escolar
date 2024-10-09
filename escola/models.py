# core/models.py

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.db import models
from django.forms import ValidationError
from django.utils import timezone

class CalendarioEscolar(models.Model):
    ano = models.PositiveIntegerField()
    inicio_ano_letivo = models.DateField()
    fim_ano_letivo = models.DateField()
    feriados = models.JSONField(help_text="Lista de feriados no formato ['YYYY-MM-DD', 'YYYY-MM-DD', ...]")
    ferias_inicio = models.DateField()
    ferias_fim = models.DateField()

    def __str__(self):
        return f"Calendário Escolar {self.ano}"

    def is_data_permitida(self, data):
        # Verifica se a data está dentro do ano letivo, fora do período de férias e não é feriado
        if not (self.inicio_ano_letivo <= data <= self.fim_ano_letivo):
            return False  # Fora do ano letivo
        if self.ferias_inicio <= data <= self.ferias_fim:
            return False  # Durante as férias
        if data.strftime('%Y-%m-%d') in self.feriados:
            return False  # Feriado
        return True  # Data permitida


class CustomUserManager(BaseUserManager):
    def create_user(self, username, email, password=None, user_type=4, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, user_type=user_type, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('user_type', 1)

        return self.create_user(username, email, password, **extra_fields)

class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        (1, 'Diretor'),
        (2, 'Secretário'),
        (3, 'Professor'),
        (4, 'Aluno'),
    )
    user_type = models.PositiveSmallIntegerField(choices=USER_TYPE_CHOICES, default=4)

    objects = CustomUserManager()


class Escola(models.Model):
    ESCOLA_TIPO_CHOICES = (
        ('Infantil', 'Escola Infantil'),
        ('Fundamental', 'Escola Fundamental'),
        ('Medio', 'Escola de Ensino Médio'),
    )
    nome = models.CharField(max_length=255)
    endereco = models.CharField(max_length=255)
    tipo = models.CharField(max_length=50, choices=ESCOLA_TIPO_CHOICES)
    diretor = models.OneToOneField('Diretor', on_delete=models.SET_NULL, null=True, blank=True, related_name='escola_diretor')
    calendario_escolar = models.OneToOneField(CalendarioEscolar, on_delete=models.SET_NULL, null=True, blank=True)

class Diretor(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    escola = models.OneToOneField(Escola, on_delete=models.CASCADE, related_name='diretor_escola')

class Secretario(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    escola = models.ForeignKey(Escola, on_delete=models.CASCADE, related_name='secretarios')

class Professor(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    escola = models.ForeignKey(Escola, on_delete=models.CASCADE, related_name='professores')

class Disciplina(models.Model):
    TURNO_CHOICES = (
        ('Manhã', 'Manhã'),
        ('Tarde', 'Tarde'),
        ('Noite', 'Noite'),
    )
    nome = models.CharField(max_length=255)
    professores = models.ManyToManyField(Professor, related_name='disciplinas')
    escola = models.ForeignKey(Escola, on_delete=models.CASCADE, related_name='disciplinas')
    alunos = models.ManyToManyField('Aluno', related_name='disciplinas')
    turno = models.CharField(max_length=10, choices=TURNO_CHOICES)
    carga_horaria = models.PositiveIntegerField()
    quantidade_aulas_dadas = models.PositiveIntegerField(default=0)
    ano = models.PositiveIntegerField()
    codigo = models.CharField(max_length=20)

    def quantidade_alunos(self):
        return self.alunos.count()

    def carga_horaria_restante(self):
        return self.carga_horaria - self.quantidade_aulas_dadas

class Aluno(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    escola = models.ForeignKey(Escola, on_delete=models.CASCADE, related_name='alunos')

class TipoTurma(models.Model):
    nome = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.nome

class Turma(models.Model):
    tipo_turma = models.ForeignKey(TipoTurma, on_delete=models.CASCADE, related_name='turmas')
    escola = models.ForeignKey(Escola, on_delete=models.CASCADE, related_name='turmas')
    alunos = models.ManyToManyField(Aluno, related_name='turmas')
    disciplinas = models.ManyToManyField(Disciplina, related_name='turmas')
    ano = models.PositiveIntegerField()
    codigo = models.CharField(max_length=20, unique=True)

    def quantidade_alunos(self):
        return self.alunos.count()

class RegistroAula(models.Model):
    disciplina = models.ForeignKey(Disciplina, on_delete=models.CASCADE)
    data = models.DateField()
    conteudo = models.TextField()

    def clean(self):
        # Verifica se a data da aula é permitida pelo calendário da escola
        escola = self.disciplina.turma.escola
        if escola and escola.calendario_escolar:
            if not escola.calendario_escolar.is_data_permitida(self.data):
                raise ValidationError("A data da aula está em um período não permitido (feriado ou férias).")
    
    def __str__(self):
        return f"Aula de {self.disciplina} em {self.data}"


class RegistroFalta(models.Model):
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE, related_name='registro_faltas')
    disciplina = models.ForeignKey(Disciplina, on_delete=models.CASCADE, related_name='registro_faltas')
    data = models.DateField()

    def __str__(self):
        return f"Falta de {self.aluno.user.username} em {self.disciplina.nome} no dia {self.data}"

class RegistroNota(models.Model):
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE, related_name='registro_notas')
    disciplina = models.ForeignKey(Disciplina, on_delete=models.CASCADE, related_name='registro_notas')
    nota = models.DecimalField(max_digits=5, decimal_places=2)
    data = models.DateField()

    def __str__(self):
        return f"Nota de {self.aluno.user.username} em {self.disciplina.nome}: {self.nota}"
