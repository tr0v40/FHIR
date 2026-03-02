
  # ==================== IMPORTS SESSIONS ==================== #

from django.db import models
from django.utils.text import slugify
import pycountry


  # ==================== IMPORTS SESSIONS ==================== #

class Organization(models.Model):
    name = models.CharField(max_length=255)
    address = models.TextField(blank=True, null=True)
    contact_info = models.TextField(blank=True, null=True)
    identifier = models.CharField(max_length=255, blank=True, null=True)


class SubstanceDefinition(models.Model):
    name = models.CharField(max_length=255)
    molecular_formula = models.CharField(max_length=255, blank=True, null=True)
    molecular_weight = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    manufacturer = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="substances"
    )


class Ingredient(models.Model):
    substance = models.ForeignKey(
        SubstanceDefinition, on_delete=models.CASCADE, related_name="ingredients"
    )
    role = models.CharField(max_length=255)
    strength = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )


class ManufacturedItemDefinition(models.Model):
    name = models.CharField(max_length=255)
    form = models.CharField(max_length=255)
    ingredients = models.ManyToManyField(Ingredient, related_name="manufactured_items")


class PackagedProductDefinition(models.Model):
    package_type = models.CharField(max_length=255)
    quantity = models.IntegerField()
    manufactured_item = models.ForeignKey(
        ManufacturedItemDefinition,
        on_delete=models.CASCADE,
        related_name="packaged_products",
    )


class AdministrableProductDefinition(models.Model):
    route_of_administration = models.CharField(max_length=255)
    dosage_form = models.CharField(max_length=255)
    packaged_product = models.ForeignKey(
        PackagedProductDefinition,
        on_delete=models.CASCADE,
        related_name="administrable_products",
    )


class MedicinalProductDefinition(models.Model):
    name = models.CharField(max_length=255)
    administrable_product = models.ForeignKey(
        AdministrableProductDefinition,
        on_delete=models.CASCADE,
        related_name="medicinal_products",
    )
    manufacturer = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="medicinal_products"
    )


class RegulatedAuthorization(models.Model):
    authorization_number = models.CharField(max_length=255)
    status = models.CharField(max_length=255)
    date_issued = models.DateField()
    holder = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="authorizations"
    )
    medicinal_product = models.ForeignKey(
        MedicinalProductDefinition,
        on_delete=models.CASCADE,
        related_name="authorizations",
    )


class ClinicalUseDefinition(models.Model):
    medicinal_product = models.ForeignKey(
        MedicinalProductDefinition,
        on_delete=models.CASCADE,
        related_name="clinical_uses",
    )
    contraindications = models.TextField(blank=True, null=True)
    indications = models.TextField(blank=True, null=True)
    interactions = models.TextField(blank=True, null=True)
    adverse_effects = models.TextField(blank=True, null=True)


class Composition(models.Model):
    title = models.CharField(max_length=255)
    date = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="compositions"
    )
    medicinal_product = models.ForeignKey(
        MedicinalProductDefinition,
        on_delete=models.CASCADE,
        related_name="compositions",
    )
    section_text = models.TextField()


class Binary(models.Model):
    content_type = models.CharField(max_length=100)
    data = models.BinaryField()
    medicinal_product = models.ForeignKey(
        MedicinalProductDefinition, on_delete=models.CASCADE, related_name="binaries"
    )


class ResourceStudyReport(models.Model):
    element_id = models.CharField(max_length=255)
    effectiveness = models.DecimalField(max_digits=6, decimal_places=3)
    effect_time = models.CharField(max_length=127)
    reason = models.CharField(max_length=255, blank=True)
    symptom_disease = models.CharField(max_length=255, blank=True)
    field_of_study = models.DateField(blank=True, null=True)
    description = models.CharField(max_length=255, blank=True)
    authors = models.CharField(max_length=255, blank=True)
    organization = models.CharField(max_length=255, blank=True)
    CID = models.CharField(
        max_length=50, default="CID-NÃO-ESPECIFICADO", blank=True, null=True
    )
    not_indicated = models.BooleanField(
        default=False, verbose_name="Não Indicado para Uso"
    )

    def is_indicated(self):
        """Retorna se o item é indicado para uso"""
        return not self.not_indicated

    def __str__(self):
        return f"{self.element_id} - Indicado para Uso: {'Sim' if self.is_indicated() else 'Não'}"


class StudyGroup(models.Model):
    FAIXA_IDADE = (
        ("0-10", "0 a 10 anos"),
        ("11-20", "11 a 20 anos"),
        ("21-30", "21 a 30 anos"),
        ("31-60", "31 a 60 anos"),
        ("61-70", "61 a 70 anos"),
        ("71-80", "71 a 80 anos"),
        ("81+", "81 anos ou mais"),
        ("gravidez", "Gravidez"),
        ("lactante", "Lactante"),
    )
    element_id = models.CharField(max_length=20, primary_key=True, unique=True)
    study_group_idade = models.CharField(
        max_length=20, choices=FAIXA_IDADE, verbose_name="Faixa Etária"
    )

    def __str__(self):
        return f"Grupo {self.element_id} - {self.study_group_idade}"


class Tratamentos(models.Model):
    nome = models.CharField(max_length=200)
    descricao = models.TextField()
    categoria = models.CharField(max_length=100)
    evidencia_clinica = models.TextField()
    principio_ativo = models.CharField(max_length=200)
    fabricante = models.CharField(max_length=200)
    avaliacao = models.DecimalField(max_digits=3, decimal_places=2)
    eficacia_min = models.DecimalField(max_digits=5, decimal_places=2,null=True, blank=True)
    eficacia_max = models.DecimalField(max_digits=5, decimal_places=2,null=True, blank=True)
    prazo_efeito_min = models.CharField(max_length=50)
    prazo_efeito_max = models.CharField(max_length=50)
    imagem = models.ImageField(upload_to="medicamentos/", blank=True, null=True)

    class Meta:
        verbose_name = "Tratamento Resumo"
        verbose_name_plural = "Tratamentos - Resumo"

    def __str__(self):
        return self.nome


class Contraindicacao(models.Model):
    nome = models.CharField(max_length=200)
    descricao = models.TextField()
    imagem = models.ImageField(upload_to="contraindicacoes/", blank=True, null=True)

    
    contraindication_name = models.CharField(
        max_length=255,
        verbose_name="ClinicalUseDefinition.contraindication-name",
        blank=True,
        null=True
    )
    contraindication_description = models.TextField(
        verbose_name="ClinicalUseDefinition.contraindication-description",
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = "Contraindicação"
        verbose_name_plural = "Contraindicações"

    def __str__(self):
        return self.nome



class ReacaoAdversa(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField()

    imagem = models.ImageField(upload_to='reacoes_adversas/', blank=True, null=True)

    # Novos campos
    undesirable_effect_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="ClinicalUseDefinition.undesirableEffect-name"
    )
    undesirable_effect_description = models.TextField(
        blank=True,
        null=True,
        verbose_name="ClinicalUseDefinition.undesirableEffect-description"
    )

    class Meta:
        verbose_name = "Reação Adversa"
        verbose_name_plural = "Reações Adversas"

    def __str__(self):
        return self.nome

    

class DetalhesTratamentoReacaoAdversa(models.Model):
    tratamento = models.ForeignKey(
        'DetalhesTratamentoResumo',
        on_delete=models.CASCADE,
        related_name='reacoes_adversas_detalhes'
    )
    reacao_adversa = models.ForeignKey(ReacaoAdversa, on_delete=models.CASCADE)
    grau_comunalidade = models.CharField(
        max_length=20,
        choices=[
            ('COMUM', 'COMUM'),
            ('MUITO_COMUM', 'MUITO COMUM'),
            ('INCOMUM', 'INCOMUM'),
            ('RARA', 'RARA'),
            ('MUITO_RARA', 'MUITO RARA'),
            ('NENHUMA', 'NENHUMA'),
        ],
        default='COMUM'
    )
    reacao_min = models.DecimalField("Reação Mínima (%)", max_digits=5, decimal_places=2, default=0.0)
    reacao_max = models.DecimalField("Reação Máxima (%)", max_digits=5, decimal_places=2, default=0.0)

    class Meta:
        verbose_name = "Detalhe Reação Adversa"
        verbose_name_plural = "Detalhes Reações Adversas"

    def __str__(self):
        return f"{self.tratamento.nome} - {self.reacao_adversa.nome}"


class TipoTratamento(models.Model):
    nome = models.CharField(max_length=200)

    # Novo campo
    careplan_type = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="CarePlan.type"
    )

    class Meta:
        verbose_name = "Tipo de Tratamento"
        verbose_name_plural = "Tipos de Tratamento"

    def __str__(self):
        return self.nome



class DetalhesTratamentoReacaoAdversaTeste(models.Model):
    tratamento = models.ForeignKey(
        'DetalhesTratamentoResumo',
        on_delete=models.CASCADE,
        related_name='reacoes_adversas_teste_detalhes'
    )
    reacao_adversa = models.ForeignKey(ReacaoAdversa, on_delete=models.CASCADE)
    grau_comunalidade = models.CharField(
        max_length=20,
        choices=[
            ('COMUM', 'COMUM'),
            ('MUITO_COMUM', 'MUITO COMUM'),
            ('INCOMUM', 'INCOMUM'),
            ('RARA', 'RARA'),
            ('MUITO_RARA', 'MUITO RARA'),
            ('NENHUMA', 'NENHUMA'),

        ],
        default='COMUM'
    )
    reacao_min = models.DecimalField("Reação Mínima (%)", max_digits=5, decimal_places=2, default=0.0)
    reacao_max = models.DecimalField("Reação Máxima (%)", max_digits=5, decimal_places=2, default=0.0)

    def __str__(self):
        return f"{self.tratamento.nome} - {self.reacao_adversa.nome}"
    

    
class CondicaoSaude(models.Model):
    nome = models.CharField(
        max_length=255,
        verbose_name="Nome da Condição de Saúde"
    )
    slug = models.SlugField(max_length=255, unique=True, blank=True, db_index=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.nome) or "condicao"
            slug = base
            i = 2
            while CondicaoSaude.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{i}"
                i += 1
            self.slug = slug
        super().save(*args, **kwargs)


    
    
    
    descricao = models.TextField(
        verbose_name="Descrição Relacionada à Condição de Saúde",
        blank=True, null=True
    )

    
    condition = models.CharField(
        max_length=255,
        blank=True, null=True,
        verbose_name="Condition"
    )
    condition_description = models.TextField(
        blank=True, null=True,
        verbose_name="Condition.description"
    )



    class Meta:
        verbose_name = "Condição de Saúde"
        verbose_name_plural = "Condições de Saúde"

    def __str__(self):
        return self.nome



class DetalhesTratamentoResumo(models.Model):
    
    tipos_eficacia = models.ManyToManyField('EficaciaPorEvidencia', blank=True)

    reacoes_adversas_teste = models.ManyToManyField(
        ReacaoAdversa,
        through='DetalhesTratamentoReacaoAdversaTeste',
        related_name='tratamentos_com_reacao_teste'
    )
    GRUPO_CHOICES = (
        ("criancas", "Crianças menores de 12 anos"),
        ("adolescentes", "Adolescentes 12 a 17 anos"),
        ("idosos", "Idosos +65 anos"),
        ("adultos", "Adultos"),
        ("lactantes", "Lactantes"),
        ("gravidez", "Gravidez"),
    )

    nome = models.CharField(max_length=200,blank=True)
    descricao = models.TextField(blank=True)
    


    condicoes_saude = models.ManyToManyField(
    "CondicaoSaude",
    blank=True,
    related_name="detalhes_tratamentos"
)
    comentario = models.TextField(blank=True, null=True)
    categoria = models.CharField(max_length=100, blank=True, null=True)
    evidencia_clinica = models.TextField(blank=True, null=True)
    principio_ativo = models.CharField(max_length=20000,blank=True)
    
    
    slug = models.SlugField(max_length=200, blank=True, null=True, unique=True)


    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.nome)
            slug = base_slug
            i = 2
            while DetalhesTratamentoResumo.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{i}"
                i += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nome
    
    fabricante = models.CharField(max_length=200,blank=True)
    comentario = models.TextField(null=True, blank=True)
    avaliacao = models.IntegerField(null=True, blank=True) 
    eficacia_min = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    eficacia_max = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    prazo_efeito_min = models.IntegerField(blank=True, null=True)  
    prazo_efeito_max = models.IntegerField(blank=True, null=True)
    link_para_compra_de_tratamento = models.URLField(blank=True, null=True)
    especificacao_do_custo = models.CharField(max_length=200,blank=True)
    reacoes_adversas = models.ManyToManyField(
        ReacaoAdversa,
        through='DetalhesTratamentoReacaoAdversa',  
        related_name='tratamentos_com_reacao'
    )
    
    UNIDADES = [
        ('minuto', 'Minuto'),
        ('hora', 'Hora'),
        ('dia', 'Dia'),
        ('sessao', 'Sessão'),
        ('segundo', 'Segundo'),
        ('semana', 'Semanas'),
    ]
    prazo_efeito_unidade = models.CharField(max_length=10, choices=UNIDADES, default='minuto')

    # Método auxiliar para pluralizar unidade
    def pluralizar_unidade(self, valor):
        excecoes = {
            'sessao': 'sessões',
        }
        unidade = self.prazo_efeito_unidade
        if valor == 1:
            
            return unidade
        
        return excecoes.get(unidade, unidade + 's')

    # Método para formatar prazo mínimo
    @property
    def prazo_efeito_min_formatado(self):
        return f"{self.prazo_efeito_min} {self.pluralizar_unidade(self.prazo_efeito_min)}"

    # Método para formatar prazo máximo
    @property
    def prazo_efeito_max_formatado(self):
        return f"{self.prazo_efeito_max} {self.pluralizar_unidade(self.prazo_efeito_max)}"

    # método para exibir a faixa completa
    @property
    def prazo_efeito_faixa_formatada(self):
        return f"{self.prazo_efeito_min_formatado} a {self.prazo_efeito_max_formatado}"

    
    interacao_medicamentosa = models.URLField(blank=True, null=True)
    genericos_similares = models.URLField(blank=True, null=True)
    prescricao_eletronica = models.URLField(blank=True, null=True)
    opiniao_especialista = models.URLField(blank=True, null=True)
    links_profissionais = models.URLField(blank=True, null=True)
    alerta = models.TextField(blank=True, null=True) 
    imagem = models.ImageField(upload_to="tratamentos/", blank=True, null=True)
    imagem_detalhes = models.ImageField(upload_to="tratamentos/detalhes/", blank=True, null=True)
    quando_usar = models.TextField(blank=True)    
    tipo_tratamento = models.ManyToManyField(TipoTratamento, blank=True)
    custo_medicamento = models.DecimalField(max_digits=7, decimal_places=2, blank=True, null=True)
    links_externos = models.TextField(blank=True, null=True)
    alertas = models.TextField(blank=True, null=True)
    grupo = models.CharField(max_length=20, choices=GRUPO_CHOICES, default="adultos")
    indicado_criancas = models.CharField(max_length=100, choices=[('SIM', 'Sim'), ('NÃO', 'Não')], default='NÃO')
    motivo_criancas = models.TextField(blank=True, null=True)
    indicado_adolescentes = models.CharField(max_length=100, choices=[('SIM', 'Sim'), ('NÃO', 'Não')], default='NÃO')
    motivo_adolescentes = models.TextField(blank=True, null=True)
    indicado_idosos = models.CharField(max_length=100, choices=[('SIM', 'Sim'), ('NÃO', 'Não')], default='NÃO')
    motivo_idosos = models.TextField(blank=True, null=True)
    indicado_adultos = models.CharField(max_length=100, choices=[('SIM', 'Sim'), ('NÃO', 'Não')], default='SIM')
    motivo_adultos = models.TextField(blank=True, null=True)
    indicado_lactantes = models.CharField(max_length=100, choices=[('SIM', 'Sim'), ('NÃO', 'Não')], default='SIM')
    motivo_lactantes = models.TextField(blank=True, null=True)
    indicado_gravidez= models.CharField(max_length=100, choices=[('SIM', 'Sim'), ('NÃO', 'Não')], default='SIM')
    motivo_gravidez = models.TextField(blank=True, null=True)
    contraindicacoes = models.ManyToManyField(Contraindicacao, blank=True)
    reacoes_adversas = models.ManyToManyField(ReacaoAdversa, blank=True)
    risco = models.FloatField(default=0.0, help_text="Risco percentual de efeito colateral (0 a 100%)")

    class Meta:
        verbose_name = "Detalhes Tratamentos - Resumo"
        verbose_name_plural = "Detalhes Tratamentos - Resumo"

    def __str__(self):
        return self.nome

COUNTRY_TRANSLATION = {
    'Afghanistan': 'Afeganistão',
    'Albania': 'Albânia',
    'Algeria': 'Argélia',
    'Andorra': 'Andorra',
    'Angola': 'Angola',
    'Antigua and Barbuda': 'Antígua e Barbuda',
    'Argentina': 'Argentina',
    'Armenia': 'Armênia',
    'Australia': 'Austrália',
    'Austria': 'Áustria',
    'Azerbaijan': 'Azerbaijão',
    'Bahamas': 'Bahamas',
    'Bahrain': 'Bahrein',
    'Bangladesh': 'Bangladesh',
    'Barbados': 'Barbados',
    'Belarus': 'Bielorrússia',
    'Belgium': 'Bélgica',
    'Belize': 'Belize',
    'Benin': 'Benin',
    'Bhutan': 'Butão',
    'Bolivia': 'Bolívia',
    'Bosnia and Herzegovina': 'Bósnia e Herzegovina',
    'Botswana': 'Botswana',
    'Brazil': 'Brasil',
    'Brunei': 'Brunei',
    'Bulgaria': 'Bulgária',
    'Burkina Faso': 'Burkina Faso',
    'Burundi': 'Burundi',
    'Cabo Verde': 'Cabo Verde',
    'Cambodia': 'Camboja',
    'Cameroon': 'Camarões',
    'Canada': 'Canadá',
    'Central African Republic': 'República Centro-Africana',
    'Chad': 'Chade',
    'Chile': 'Chile',
    'China': 'China',
    'Colombia': 'Colômbia',
    'Comoros': 'Comores',
    'Congo (Congo-Brazzaville)': 'Congo (Congo-Brazzaville)',
    'Congo (Congo-Kinshasa)': 'Congo (Congo-Kinshasa)',
    'Costa Rica': 'Costa Rica',
    'Croatia': 'Croácia',
    'Cuba': 'Cuba',
    'Cyprus': 'Chipre',
    'Czech Republic': 'República Tcheca',
    'Denmark': 'Dinamarca',
    'Djibouti': 'Djibouti',
    'Dominica': 'Dominica',
    'Dominican Republic': 'República Dominicana',
    'Ecuador': 'Equador',
    'Egypt': 'Egito',
    'El Salvador': 'El Salvador',
    'Equatorial Guinea': 'Guiné Equatorial',
    'Eritrea': 'Eritreia',
    'Estonia': 'Estônia',
    'Eswatini': 'Eswatini',
    'Ethiopia': 'Etiópia',
    'Fiji': 'Fiji',
    'Finland': 'Finlândia',
    'France': 'França',
    'Gabon': 'Gabão',
    'Gambia': 'Gâmbia',
    'Georgia': 'Geórgia',
    'Germany': 'Alemanha',
    'Ghana': 'Gana',
    'Greece': 'Grécia',
    'Grenada': 'Granada',
    'Guatemala': 'Guatemala',
    'Guinea': 'Guiné',
    'Guinea-Bissau': 'Guiné-Bissau',
    'Guyana': 'Guiana',
    'Haiti': 'Haiti',
    'Honduras': 'Honduras',
    'Hungary': 'Hungria',
    'Iceland': 'Islândia',
    'India': 'Índia',
    'Indonesia': 'Indonésia',
    'Iran': 'Irã',
    'Iraq': 'Iraque',
    'Ireland': 'Irlanda',
    'Israel': 'Israel',
    'Italy': 'Itália',
    'Jamaica': 'Jamaica',
    'Japan': 'Japão',
    'Jordan': 'Jordânia',
    'Kazakhstan': 'Cazaquistão',
    'Kenya': 'Quênia',
    'Kiribati': 'Quiribati',
    'Korea, North': 'Coreia do Norte',
    'Korea, South': 'Coreia do Sul',
    'Kuwait': 'Kuwait',
    'Kyrgyzstan': 'Quirguistão',
    'Laos': 'Laos',
    'Latvia': 'Letônia',
    'Lebanon': 'Líbano',
    'Lesotho': 'Lesoto',
    'Liberia': 'Libéria',
    'Libya': 'Líbia',
    'Liechtenstein': 'Liechtenstein',
    'Lithuania': 'Lituânia',
    'Luxembourg': 'Luxemburgo',
    'Madagascar': 'Madagascar',
    'Malawi': 'Malawi',
    'Malaysia': 'Malásia',
    'Maldives': 'Maldivas',
    'Mali': 'Mali',
    'Malta': 'Malta',
    'Marshall Islands': 'Ilhas Marshall',
    'Mauritania': 'Mauritânia',
    'Mauritius': 'Maurícias',
    'Mexico': 'México',
    'Micronesia': 'Micronésia',
    'Moldova': 'Moldávia',
    'Monaco': 'Mônaco',
    'Mongolia': 'Mongólia',
    'Montenegro': 'Montenegro',
    'Morocco': 'Marrocos',
    'Mozambique': 'Moçambique',
    'Myanmar': 'Mianmar',
    'Namibia': 'Namíbia',
    'Nauru': 'Nauru',
    'Nepal': 'Nepal',
    'Netherlands': 'Países Baixos',
    'New Zealand': 'Nova Zelândia',
    'Nicaragua': 'Nicarágua',
    'Niger': 'Níger',
    'Nigeria': 'Nigéria',
    'North Macedonia': 'Macédônia do Norte',
    'Norway': 'Noruega',
    'Oman': 'Omã',
    'Pakistan': 'Paquistão',
    'Palau': 'Palau',
    'Panama': 'Panamá',
    'Papua New Guinea': 'Papua Nova Guiné',
    'Paraguay': 'Paraguai',
    'Peru': 'Peru',
    'Philippines': 'Filipinas',
    'Poland': 'Polônia',
    'Portugal': 'Portugal',
    'Qatar': 'Catar',
    'Romania': 'Romênia',
    'Russia': 'Rússia',
    'Rwanda': 'Ruanda',
    'Saint Kitts and Nevis': 'São Cristóvão e Nevis',
    'Saint Lucia': 'Santa Lúcia',
    'Saint Vincent and Grenadines': 'São Vicente e Granadinas',
    'Samoa': 'Samoa',
    'San Marino': 'São Marino',
    'Sao Tome and Principe': 'São Tomé e Príncipe',
    'Saudi Arabia': 'Arábia Saudita',
    'Senegal': 'Senegal',
    'Serbia': 'Sérvia',
    'Seychelles': 'Seychelles',
    'Sierra Leone': 'Serra Leoa',
    'Singapore': 'Singapura',
    'Slovakia': 'Eslováquia',
    'Slovenia': 'Eslovênia',
    'Solomon Islands': 'Ilhas Salomão',
    'Somalia': 'Somália',
    'South Africa': 'África do Sul',
    'South Sudan': 'Sudão do Sul',
    'Spain': 'Espanha',
    'Sri Lanka': 'Sri Lanka',
    'Sudan': 'Sudão',
    'Suriname': 'Suriname',
    'Sweden': 'Suécia',
    'Switzerland': 'Suíça',
    'Syria': 'Síria',
    'Taiwan': 'Taiwan',
    'Tajikistan': 'Tajiquistão',
    'Tanzania': 'Tanzânia',
    'Thailand': 'Tailândia',
    'Timor-Leste': 'Timor-Leste',
    'Togo': 'Togo',
    'Tonga': 'Tonga',
    'Trinidad and Tobago': 'Trinidad e Tobago',
    'Tunisia': 'Tunísia',
    'Turkey': 'Turquia',
    'Turkmenistan': 'Turcomenistão',
    'Tuvalu': 'Tuvalu',
    'Uganda': 'Uganda',
    'Ukraine': 'Ucrânia',
    'United Arab Emirates': 'Emirados Árabes Unidos',
    'United Kingdom': 'Reino Unido',
    'United States': 'Estados Unidos',
    'Uruguay': 'Uruguai',
    'Uzbekistan': 'Uzbequistão',
    'Vanuatu': 'Vanuatu',
    'Vatican City': 'Vaticano',
    'Venezuela': 'Venezuela',
    'Vietnam': 'Vietnã',
    'Yemen': 'Iémen',
    'Zambia': 'Zâmbia',
    'Zimbabwe': 'Zimbábue',
}

COUNTRIES = [
    (country.name, COUNTRY_TRANSLATION.get(country.name, country.name))
    for country in pycountry.countries
]


COUNTRIES += [
    
    ('Multiple countries in the Americas', 'Vários países da América'),
    ('Multiple countries in Europe', 'Vários países da Europa'),
    ('Multiple countries in Asia', 'Vários países da Ásia'),
    ('Multiple countries in Africa', 'Vários países da África'),
    ('Multiple countries from more than one continent', 'Vários países de mais de um continente'),
]


class Pais(models.Model):
    nome = models.CharField(max_length=100, choices=COUNTRIES, unique=True)

    def __str__(self):
        return self.nome
    

class DetalheTratamentoCondicaoSaude(models.Model):
    tratamento = models.ForeignKey('DetalhesTratamentoResumo', on_delete=models.CASCADE)
    condicao = models.ForeignKey('CondicaoSaude', on_delete=models.CASCADE)

    
    descricao_relacionada = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('tratamento', 'condicao')  


class EvidenciasClinicas(models.Model):
    tratamento = models.ForeignKey("DetalhesTratamentoResumo", on_delete=models.CASCADE, related_name="evidencias")
    titulo = models.CharField(
        max_length=255,
        verbose_name="Código",
        blank=True,
        null=True
    )
    descricao = models.TextField()
    evidence_description = models.TextField(
        verbose_name="Evidence.description",
        blank=True,
        null=True
    )
    numero_participantes = models.IntegerField() 
    condicao_saude = models.ForeignKey(
        "CondicaoSaude",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="evidencias"
    )

    rigor_da_pesquisa = models.IntegerField(default=0)
    link_estudo = models.URLField(blank=True, null=True)
    data_publicacao = models.DateField(blank=True, null=True)
    autores = models.CharField(max_length=255, blank=True, null=True)


    pais = models.CharField(
        max_length=100,
        choices=COUNTRIES,
        blank=True,
        null=True,
        verbose_name="Países"
    )

    paises = models.ManyToManyField('Pais', blank=True, verbose_name="País")

    country = models.CharField(        
        max_length=100,
        choices=COUNTRIES,
        blank=True,
        null=True,
        verbose_name="Country"
    )

    imagem_estudo = models.ImageField(upload_to="evidencias/", blank=True, null=True)
    fonte = models.CharField(max_length=255, blank=True, null=True, verbose_name="Fonte")
    eficacia_min = models.DecimalField(max_digits=5, decimal_places=2,null=True, blank=True)
    eficacia_max = models.DecimalField(max_digits=5, decimal_places=2,null=True, blank=True)
    pdf_estudo = models.FileField(upload_to="pdf_estudos/", blank=True, null=True)
    link_pdf_estudo = models.URLField(blank=True, null=True)
    referencia_bibliografica = models.TextField(
    blank=True,
    null=True,
    verbose_name="Título do artigo"
)
    evidence_title = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Evidence.title"
    )

    participantes_com_beneficio = models.IntegerField(default=0)
    participantes_iniciaram_tratamento = models.IntegerField(default=0)
    percentual = models.CharField(max_length=100, blank=True, null=True) 
    risco_reacao = models.CharField(max_length=100, blank=True, null=True)  # ex: "1% a 10% COMUM"

    class Meta:
        verbose_name = "Evidência Clínica"
        verbose_name_plural = "Evidências Clínicas"

    def __str__(self):
        return f"{self.titulo} - {self.tratamento.nome}"
    @property
    def percentual_eficacia(self):

        if self.participantes_iniciaram_tratamento > 0:
            return (self.participantes_com_beneficio / self.participantes_iniciaram_tratamento) * 100
        return 0.0  




class Tratamento(models.Model):
    nome = models.CharField(max_length=255)
    descricao = models.TextField()
    

class Avaliacao(models.Model):
    tratamento = models.ForeignKey(DetalhesTratamentoResumo, on_delete=models.CASCADE, related_name='avaliacoes')
    comentario = models.TextField(max_length=400)
    usuario_nome = models.CharField(max_length=100)

    estrelas = models.PositiveIntegerField(choices=[(1, '1 estrela'), (2, '2 estrelas'), (3, '3 estrelas'), 
                                                        (4, '4 estrelas'), (5, '5 estrelas')], blank=True, null=True)
    data = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Avaliação para {self.tratamento.nome} - {self.estrelas} estrelas"
    
    class Meta:
        verbose_name = "Avaliação"
        verbose_name_plural = "Avaliações"
    


# pré-requisito nos models (resumo)
class TratamentoCondicao(models.Model):
    tratamento = models.ForeignKey('DetalhesTratamentoResumo', on_delete=models.CASCADE, related_name='condicoes_relacionadas')
    condicao  = models.ForeignKey('CondicaoSaude', on_delete=models.CASCADE, related_name='tratamentos_relacionados')
    descricao = models.TextField(blank=True, null=True) 
    class Meta:
        unique_together = ('tratamento', 'condicao')
    class Meta:
        verbose_name = "Tratamento Condição"
        verbose_name_plural = "Tratamentos Condições"

    def __str__(self):
        return f"{self.condicao.nome}"
    

class TipoEficacia(models.Model):
    tipo_eficacia = models.CharField(max_length=255) 
    descricao = models.TextField(blank=True, null=True)  
    imagem = models.ImageField(upload_to='icones_eficacia/', blank=True, null=True)  # Campo de imagem para o ícone



    eficacia_por_tipo = models.ManyToManyField('EficaciaPorTipo', related_name='tipos_de_eficacia', blank=True)

    def __str__(self):
        return self.tipo_eficacia  





class EficaciaPorTipo(models.Model):
    tipo_eficacia = models.CharField(max_length=255)
    percentual_eficacia_calculado = models.FloatField()
    participantes_iniciaram_tratamento = models.IntegerField()
    participantes_com_beneficio = models.IntegerField()

    # Relacionamento com TipoEficacia (ManyToManyField)
    tipos_eficacia = models.ManyToManyField(
        TipoEficacia, related_name='eficacias_tipo', blank=True
    )

    def __str__(self):
        return self.tipo_eficacia





# models.py

class EficaciaPorEvidencia(models.Model):
    evidencia = models.ForeignKey(EvidenciasClinicas, on_delete=models.CASCADE, related_name="eficacia_por_evidencias")
    tipo_eficacia = models.ForeignKey(TipoEficacia, on_delete=models.CASCADE)
    
    # Campos de participantes
    participantes_com_beneficio = models.IntegerField(default=0)
    participantes_iniciaram_tratamento = models.IntegerField(default=0)
    
    # Eficácia calculada
    @property
    def percentual_eficacia_calculado(self):
        if self.participantes_iniciaram_tratamento > 0:
            return (self.participantes_com_beneficio / self.participantes_iniciaram_tratamento) * 100
        return 0.0
    
    def __str__(self):
        return f"{self.evidencia.titulo} - {self.tipo_eficacia.tipo_eficacia} - Eficácia: {self.percentual_eficacia_calculado}%"
    

from django.db import models
from django.utils.text import slugify
from django.core.exceptions import ValidationError


class PaginaDetalheTratamento(models.Model):
    condicao = models.ForeignKey(
        "core.CondicaoSaude",
        on_delete=models.CASCADE,
        related_name="paginas_tratamento"
    )

    tratamento = models.ForeignKey(
        "core.DetalhesTratamentoResumo",
        on_delete=models.CASCADE,
        related_name="paginas_publicas"
    )

    publicada = models.BooleanField(default=True)

    # SEO
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.TextField(blank=True)

    # Customização opcional
    titulo_custom = models.CharField(max_length=255, blank=True)
    descricao_custom = models.TextField(blank=True)

    # CTA
    cta_label = models.CharField(max_length=120, blank=True)
    cta_url = models.URLField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("condicao", "tratamento")
        verbose_name = "URL Detalhe"
        verbose_name_plural = "URLs Detalhes"

    def __str__(self):
        return f"{self.condicao.nome} - {self.tratamento.nome}"

    def clean(self):
        # impede conflito com admin e api
        if self.condicao.slug in ["admin", "api"]:
            raise ValidationError("Slug da condição não pode ser 'admin' ou 'api'.")
