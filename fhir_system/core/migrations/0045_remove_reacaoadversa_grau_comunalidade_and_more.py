# Generated by Django 5.1.5 on 2025-05-22 19:08

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0044_detalhestratamentoresumo_prazo_efeito_unidade'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='reacaoadversa',
            name='grau_comunalidade',
        ),
        migrations.RemoveField(
            model_name='reacaoadversa',
            name='reacao_max',
        ),
        migrations.RemoveField(
            model_name='reacaoadversa',
            name='reacao_min',
        ),
        migrations.CreateModel(
            name='ReacaoAdversaDetalhe',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('grupo', models.CharField(max_length=50)),
                ('reacao_min', models.DecimalField(decimal_places=2, default=0.0, help_text='Valor mínimo de risco percentual de efeito colateral (0 a 100%)', max_digits=5, verbose_name='Reação Mínima (%)')),
                ('reacao_max', models.DecimalField(decimal_places=2, default=0.0, help_text='Valor máximo de risco percentual de efeito colateral (0 a 100%)', max_digits=5, verbose_name='Reação Máxima (%)')),
                ('grau_comunalidade', models.CharField(choices=[('COMUM', 'COMUM'), ('INCOMUM', 'INCOMUM'), ('RARA', 'RARA'), ('MUITO_RARA', 'MUITO RARA')], default='COMUM', max_length=20, verbose_name='Grau de Comunalidade')),
                ('reacao_adversa', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='detalhes', to='core.reacaoadversa')),
            ],
            options={
                'verbose_name': 'Detalhe da Reação Adversa',
                'verbose_name_plural': 'Detalhes das Reações Adversas',
            },
        ),
    ]
