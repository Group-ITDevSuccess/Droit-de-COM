import uuid

from django.db import models


# Create your models here.
class Connexion(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    server = models.CharField(verbose_name='Server', max_length=150)
    login = models.CharField(verbose_name='Identifiant', max_length=50, null=True, default='reader')
    password = models.CharField(verbose_name='Mot de Passe', max_length=500, default='m1234')

    def __str__(self):
        return f"{self.server}"


class Societe(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150, unique=True)
    value = models.CharField(max_length=150)
    base = models.CharField(max_length=150)
    table = models.CharField(max_length=150, null=True, default='')
    active = models.BooleanField(default=False)
    type = models.CharField(choices=(('X3', 'X3'), ('SAGE100', 'SAGE100')), default='X3', max_length=10, null=True)
    connexion = models.ForeignKey(Connexion, on_delete=models.CASCADE, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class History(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    societe = models.CharField(max_length=100)
    target = models.CharField(max_length=100, null=True)
    destinataire = models.TextField()
    copie = models.TextField(blank=True, null=True)
    status = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    message = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.societe
