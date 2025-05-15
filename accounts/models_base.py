from django.db import models
from django.utils.translation import gettext_lazy as _


class BaseMetadataModel(models.Model):
    """
    Abstrakcyjny model bazowy dla wszystkich modeli w systemie.
    Zawiera pola metadanych do śledzenia tworzenia, aktualizacji i usuwania.
    """

    """ Kto utworzył rekord"""
    created_by_admin = models.BooleanField(_("Utworzone przez administratora"), default=False)

    """ Adresy IP """
    created_ip = models.GenericIPAddressField(_("Adresy IP utworzenia"), blank=True, null=True)
    updated_ip = models.GenericIPAddressField(_("Adresy IP aktualizacji"), blank=True, null=True)

    """ Daty """
    created_at = models.DateTimeField(_("Data utworzenia"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Data aktualizacji"), auto_now=True)

    class Meta:
        abstract = True

