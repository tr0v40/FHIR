# Generated by Django 5.1.5 on 2025-05-01 14:41

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0024_remove_reacaoadversa_risco_reacao_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='evidenciasclinicas',
            name='estudo_publicado',
        ),
    ]
