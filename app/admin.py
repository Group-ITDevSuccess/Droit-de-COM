from django.contrib import admin

from app.models import Connexion, Societe


@admin.register(Societe)
class SocieteAdmin(admin.ModelAdmin):
    list_display = ('name', 'value', 'base', 'active', 'created_at', 'updated_at')
    list_filter = ('active', 'created_at', 'updated_at')
    search_fields = ('name', 'value', 'base')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Connexion)
class ConnexionAdmin(admin.ModelAdmin):
    list_display = ('uid', 'server', 'login', 'password')
    search_fields = ('server', 'login')
    readonly_fields = ('uid',)
