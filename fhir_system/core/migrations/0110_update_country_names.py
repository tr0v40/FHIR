from django.db import migrations

# Dicionário de tradução dos países
COUNTRY_TRANSLATION = {
    'Brazil': 'Brasil',
    'Argentina': 'Argentina',
    'Colombia': 'Colômbia',
    'Mexico': 'México',
    'Chile': 'Chile',
    'United States': 'Estados Unidos',
    'France': 'França',
    'Germany': 'Alemanha',
    'United Kingdom': 'Reino Unido',
    'Italy': 'Itália',
    'Spain': 'Espanha',
    'China': 'China',
    'Japan': 'Japão',
    'India': 'Índia',
    'South Korea': 'Coreia do Sul',
    'Australia': 'Austrália',
    'New Zealand': 'Nova Zelândia',
    'South Africa': 'África do Sul',
    'Egypt': 'Egito',
    'Nigeria': 'Nigéria',
    'Zimbabwe': 'Zimbábue',
    'Multiple countries in the Americas': 'Vários países da América',
    'Multiple countries in Europe': 'Vários países da Europa',
    'Multiple countries in Asia': 'Vários países da Ásia',
    'Multiple countries in Africa': 'Vários países da África',
    'Multiple countries from more than one continent': 'Vários países de mais de um continente',
}

def update_country_names(apps, schema_editor):
    EvidenciasClinicas = apps.get_model('core', 'EvidenciasClinicas')

    for old_country, new_country in COUNTRY_TRANSLATION.items():
        # Atualiza os países nos campos 'pais' e 'country'
        EvidenciasClinicas.objects.filter(country=old_country).update(country=new_country)
        EvidenciasClinicas.objects.filter(pais=old_country).update(pais=new_country)

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0109_alter_evidenciasclinicas_country_and_more'),  # Substitua com a migração anterior
    ]

    operations = [
        migrations.RunPython(update_country_names),
    ]
