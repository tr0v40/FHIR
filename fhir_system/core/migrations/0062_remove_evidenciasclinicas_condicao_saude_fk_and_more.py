from django.db import migrations

def forward(apps, schema_editor):
    CondicaoSaude = apps.get_model('core', 'CondicaoSaude')
    EvidenciasClinicas = apps.get_model('core', 'EvidenciasClinicas')

    for ev in EvidenciasClinicas.objects.all():
        nome = (ev.condicao_saude or "").strip()
        if not nome:
            continue
        cs, _ = CondicaoSaude.objects.get_or_create(nome=nome)
        ev.condicao_saude_fk_id = cs.id
        ev.save(update_fields=['condicao_saude_fk'])

def backward(apps, schema_editor):
    EvidenciasClinicas = apps.get_model('core', 'EvidenciasClinicas')
    for ev in EvidenciasClinicas.objects.select_related('condicao_saude_fk'):
        if ev.condicao_saude_fk_id:
            ev.condicao_saude = ev.condicao_saude_fk.nome
            ev.save(update_fields=['condicao_saude'])

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0061_migrate_condicao_saude_texto_para_fk')  # coloque aqui a MIGRAÇÃO REAL que adicionou o FK
    ]
    operations = [migrations.RunPython(forward, backward)]
