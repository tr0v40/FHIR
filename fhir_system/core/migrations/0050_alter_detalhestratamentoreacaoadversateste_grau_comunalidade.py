# Generated by Django 5.1.5 on 2025-06-06 13:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0049_remove_reacaoadversa_grau_comunalidade_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='detalhestratamentoreacaoadversateste',
            name='grau_comunalidade',
            field=models.CharField(choices=[('COMUM', 'COMUM'), ('MUITO_COMUM', 'MUITO COMUM'), ('INCOMUM', 'INCOMUM'), ('RARA', 'RARA'), ('MUITO_RARA', 'MUITO RARA')], default='COMUM', max_length=20),
        ),
    ]
