# Generated by Django 5.1.5 on 2025-02-18 10:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0014_delete_contraindicacoes_delete_reacaoadversa_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='evidenciasclinicas',
            name='eficacia_max',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='evidenciasclinicas',
            name='eficacia_min',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5),
            preserve_default=False,
        ),
    ]
