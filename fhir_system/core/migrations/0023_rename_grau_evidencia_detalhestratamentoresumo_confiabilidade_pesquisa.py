# Generated by Django 5.1.5 on 2025-03-15 19:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0022_reacaoadversa_risco_reacao'),
    ]

    operations = [
        migrations.RenameField(
            model_name='detalhestratamentoresumo',
            old_name='grau_evidencia',
            new_name='confiabilidade_pesquisa',
        ),
    ]
