# Generated by Django 5.1.5 on 2025-05-01 15:01

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0026_remove_detalhestratamentoresumo_adesao'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='detalhestratamentoresumo',
            name='confiabilidade_pesquisa',
        ),
        migrations.RemoveField(
            model_name='detalhestratamentoresumo',
            name='funciona_para_todos',
        ),
    ]
