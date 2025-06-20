# Generated by Django 5.2 on 2025-06-12 15:09

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('marcaje', '0012_tipopermisos_cod_color'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='empleado',
            name='user',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='empleado_marcaje', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='gestionfechacorte',
            name='mes',
            field=models.CharField(max_length=20),
        ),
    ]
