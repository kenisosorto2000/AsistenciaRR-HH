# marcaje/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import *


@receiver(post_save, sender=Empleado)
def desactivar_usuario_si_deja_de_ser_encargado(sender, instance, **kwargs):
    if instance.user:
        if not instance.es_encargado and instance.user.is_active:
            instance.user.is_active = False
            instance.user.save()
        elif instance.es_encargado and not instance.user.is_active:
            instance.user.is_active = True  # Lo reactiva si vuelve a ser encargado
            instance.user.save()

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)