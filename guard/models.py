import uuid

from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.utils.translation import gettext_lazy


class CustomUser(AbstractUser):
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    access = models.BooleanField(
        default=False,
        verbose_name='access',
        help_text=gettext_lazy("Autoriser l'utilisateur à se connecter au plateforme.")
    )
    groups = models.ManyToManyField(Group, blank=True, related_name='custom_users')
    user_permissions = models.ManyToManyField(Permission, blank=True, related_name='custom_users')

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = 'Authentification et Sécurité'
        verbose_name_plural = 'Authentification'
