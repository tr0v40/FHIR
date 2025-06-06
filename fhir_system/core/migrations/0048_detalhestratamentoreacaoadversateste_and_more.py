# Generated by Django 5.1.5 on 2025-05-23 13:48

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0047_detalhestratamentoreacaoadversa'),
    ]

    operations = [
        migrations.CreateModel(
            name='DetalhesTratamentoReacaoAdversaTeste',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('grau_comunalidade', models.CharField(choices=[('COMUM', 'COMUM'), ('INCOMUM', 'INCOMUM'), ('RARA', 'RARA'), ('MUITO_RARA', 'MUITO RARA')], default='COMUM', max_length=20)),
                ('reacao_min', models.DecimalField(decimal_places=2, default=0.0, max_digits=5, verbose_name='Reação Mínima (%)')),
                ('reacao_max', models.DecimalField(decimal_places=2, default=0.0, max_digits=5, verbose_name='Reação Máxima (%)')),
                ('reacao_adversa', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.reacaoadversa')),
                ('tratamento', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reacoes_adversas_teste_detalhes', to='core.detalhestratamentoresumo')),
            ],
        ),
        migrations.AddField(
            model_name='detalhestratamentoresumo',
            name='reacoes_adversas_teste',
            field=models.ManyToManyField(related_name='tratamentos_com_reacao_teste', through='core.DetalhesTratamentoReacaoAdversaTeste', to='core.reacaoadversa'),
        ),
    ]
