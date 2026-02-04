from django.db import migrations

def copy_fk_to_m2m(apps, schema_editor):
    Det = apps.get_model('core', 'DetalhesTratamentoResumo')

    for det in Det.objects.all():
        # garante que funciona mesmo se o campo já tiver sido removido do model atual
        if hasattr(det, "condicao_saude_id") and det.condicao_saude_id:
            det.condicoes_saude.add(det.condicao_saude_id)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0125_detalhestratamentoresumo_condicoes_saude_and_more'),
    ]

    operations = [
        migrations.RunPython(copy_fk_to_m2m, migrations.RunPython.noop)
    ]