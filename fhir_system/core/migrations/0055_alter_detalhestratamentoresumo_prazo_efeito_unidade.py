# Generated by Django 5.1.5 on 2025-06-26 14:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0054_alter_detalhestratamentoreacaoadversa_grau_comunalidade'),
    ]

    operations = [
        migrations.AlterField(
            model_name='detalhestratamentoresumo',
            name='prazo_efeito_unidade',
            field=models.CharField(choices=[('minuto', 'Minuto'), ('hora', 'Hora'), ('dia', 'Dia'), ('sessao', 'Sessão'), ('segundo', 'Segundo'), ('semana', 'Semanas')], default='minuto', max_length=10),
        ),
    ]
