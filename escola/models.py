# core/models.py

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

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
    disciplina = models.ForeignKey(Disciplina, on_delete=models.CASCADE, related_name='registro_aulas')
    data = models.DateField()
    conteudo = models.TextField()

    def __str__(self):
        return f"Aula de {self.disciplina.nome} em {self.data}"

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
