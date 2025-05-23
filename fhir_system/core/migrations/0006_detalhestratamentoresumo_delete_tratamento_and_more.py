# Generated by Django 5.1.5 on 2025-02-16 17:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_tratamento'),
    ]

    operations = [
        migrations.CreateModel(
            name='DetalhesTratamentoResumo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=100)),
                ('fabricante', models.CharField(max_length=200)),
                ('principio_ativo', models.CharField(max_length=200)),
                ('descricao', models.TextField()),
                ('eficacia', models.CharField(max_length=50)),
                ('grau_evidencia', models.CharField(blank=True, max_length=100, null=True)),
                ('funciona_para_todos', models.CharField(blank=True, max_length=100, null=True)),
                ('adesao', models.CharField(max_length=200)),
                ('quando_tomar', models.TextField()),
                ('imagem', models.ImageField(blank=True, null=True, upload_to='tratamentos/')),
                ('prazo_efeito_min', models.CharField(blank=True, max_length=50, null=True)),
                ('prazo_efeito_max', models.CharField(blank=True, max_length=50, null=True)),
                ('realizar_tratamento_quando', models.TextField(blank=True, null=True)),
                ('custo_medicamento', models.DecimalField(blank=True, decimal_places=2, max_digits=7, null=True)),
                ('links_externos', models.TextField(blank=True, null=True)),
                ('alertas', models.TextField(blank=True, null=True)),
                ('indicado_criancas', models.CharField(choices=[('SIM', 'Sim'), ('NÃO', 'Não')], default='NÃO', max_length=100)),
                ('motivo_criancas', models.TextField(blank=True, null=True)),
                ('indicado_adolescentes', models.CharField(choices=[('SIM', 'Sim'), ('NÃO', 'Não')], default='NÃO', max_length=100)),
                ('motivo_adolescentes', models.TextField(blank=True, null=True)),
                ('indicado_idosos', models.CharField(choices=[('SIM', 'Sim'), ('NÃO', 'Não')], default='NÃO', max_length=100)),
                ('motivo_idosos', models.TextField(blank=True, null=True)),
                ('indicado_adultos', models.CharField(choices=[('SIM', 'Sim'), ('NÃO', 'Não')], default='SIM', max_length=100)),
                ('motivo_adultos', models.TextField(blank=True, null=True)),
                ('uso_lactantes', models.CharField(choices=[('A', 'A'), ('B', 'B'), ('C', 'C')], default='C', max_length=100)),
                ('motivo_lactantes', models.TextField(blank=True, null=True)),
                ('uso_gravidez', models.CharField(choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D'), ('X', 'X')], default='D', max_length=100)),
                ('motivo_gravidez', models.TextField(blank=True, null=True)),
                ('contraindicado_hipersensibilidade', models.TextField()),
                ('motivo_hipersensibilidade', models.TextField(blank=True, null=True)),
                ('contraindicado_insuficiencia_renal', models.TextField()),
                ('motivo_insuficiencia_renal', models.TextField(blank=True, null=True)),
                ('contraindicado_insuficiencia_hepatica', models.TextField()),
                ('motivo_insuficiencia_hepatica', models.TextField(blank=True, null=True)),
                ('contraindicado_hipertensao', models.TextField()),
                ('motivo_hipertensao', models.TextField(blank=True, null=True)),
                ('reacoes_adversas', models.TextField(blank=True, null=True)),
                ('opiniao_medica', models.TextField(blank=True, null=True)),
                ('imagem_reacao', models.ImageField(blank=True, null=True, upload_to='reacoes_adversas/')),
            ],
            options={
                'verbose_name': 'Detalhes Tratamentos - Resumo',
                'verbose_name_plural': 'Detalhes Tratamentos - Resumo',
            },
        ),
        migrations.DeleteModel(
            name='Tratamento',
        ),
        migrations.AlterModelOptions(
            name='tratamentos',
            options={'verbose_name': 'Tratamento Resumo', 'verbose_name_plural': 'Tratamentos - Resumo'},
        ),
    ]
