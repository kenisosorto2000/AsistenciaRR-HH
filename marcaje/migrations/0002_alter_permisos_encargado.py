# Generated by Django 5.0.14 on 2025-07-02 22:19

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('marcaje', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='permisos',
            name='encargado',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='solicitudes_enviadas', to='marcaje.empleado'),
        ),
    ]
