# Generated by Django 5.1.5 on 2025-03-09 20:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0019_detalhestratamentoresumo_risco'),
    ]

    operations = [
        migrations.AddField(
            model_name='evidenciasclinicas',
            name='reacoes_adversas',
            field=models.TextField(blank=True, null=True),
        ),
    ]
