# Generated by Django 5.1.5 on 2025-05-22 19:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0045_remove_reacaoadversa_grau_comunalidade_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='reacaoadversa',
            name='grau_comunalidade',
            field=models.CharField(choices=[('COMUM', 'COMUM'), ('INCOMUM', 'INCOMUM'), ('RARA', 'RARA'), ('MUITO_RARA', 'MUITO RARA')], default='COMUM', max_length=20, verbose_name='Grau de Comunalidade'),
        ),
        migrations.AddField(
            model_name='reacaoadversa',
            name='reacao_max',
            field=models.DecimalField(decimal_places=2, default=0.0, help_text='Valor mánimo de risco percentual de efeito colateral (0 a 100%)', max_digits=5, verbose_name='Reação Máxima (%)'),
        ),
        migrations.AddField(
            model_name='reacaoadversa',
            name='reacao_min',
            field=models.DecimalField(decimal_places=2, default=0.0, help_text='Valor mínimo de risco percentual de efeito colateral (0 a 100%)', max_digits=5, verbose_name='Reação Mínima (%)'),
        ),
        migrations.DeleteModel(
            name='ReacaoAdversaDetalhe',
        ),
    ]
