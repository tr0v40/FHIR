
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
    constraints = [
        models.UniqueConstraint(
            fields=[
                'tratamento',
                'reacao_adversa',
                'grau_comunalidade',
                'reacao_min',
                'reacao_max',
            ],
            name='unique_reacao_adversa_completa_por_tratamento'
        )
    ]

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
    nome = models.CharField(max_length=255)
    slug = models.SlugField(max_length=140, unique=True, blank=True, null=True, db_index=True)

    descricao = models.TextField(blank=True, null=True)

    condition = models.CharField(max_length=255, blank=True, default="")
    condition_description = models.TextField(blank=True, default="")
    condition_slug = models.SlugField(max_length=140, unique=True, blank=True, null=True, db_index=True)

    def save(self, *args, **kwargs):
        if self.nome:
            base = slugify(self.nome) or "condicao"
            slug = base
            i = 2
            while CondicaoSaude.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{i}"
                i += 1
            self.slug = slug

        if self.condition:
            base = slugify(self.condition) or "condition"
            slug = base
            i = 2
            while CondicaoSaude.objects.filter(condition_slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{i}"
                i += 1
            self.condition_slug = slug
        else:
            self.condition_slug = None

        super().save(*args, **kwargs)

    def __str__(self):
        return self.nome
    
    
    
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
    CATEGORIA_REGULATORIA_CHOICES = [
        ("novo", "Novo"),
        ("referencia", "Referência"),
        ("similar", "Similar"),
        ("generico", "Genérico"),
        ("fitoterapico", "Fitoterápico"),
        ("biologico", "Biológico"),
        ("especifico", "Específico"),
        ("dinamizado", "Dinamizado"),
        ("radiofarmaco", "Radiofármaco"),
        ("gases_medicinais", "Gases medicinais"),
        ("nao_aplicavel", "Não aplicável"),
    ]

    TIPO_PRESCRICAO_CHOICES = [
        ("isento_de_prescricao", "Isento de prescrição"),
        ("tarja_vermelha", "Tarja vermelha"),
        ("tarja_preta", "Tarja preta"),
        ("nao_medicamentosos", "Não medicamentosos"),
    ]

    categoria_regulatoria = models.CharField(
        "Categoria regulatória",
        max_length=50,
        choices=CATEGORIA_REGULATORIA_CHOICES,
        blank=True,
        null=True,
    )

    tipo_prescricao = models.CharField(
        "Tipo de prescrição",
        max_length=50,
        choices=TIPO_PRESCRICAO_CHOICES,
        blank=True,
        null=True,
    )
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
    id_tratamento = models.CharField(
    "ID tratamento / Código EAN",
    max_length=255,
    blank=True,
    default="",
    db_index=True,
    help_text="Informe o código EAN ou códigos de referência do medicamento. Para múltiplos códigos, separe por vírgula.",
)
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
    imagem_anv = models.ImageField(upload_to="tratamentos/", blank=True, null=True)
    imagem_detalhes_anv = models.ImageField(upload_to="tratamentos/detalhes/", blank=True, null=True)
    imagem = models.ImageField(upload_to="tratamentos/", blank=True, null=True)
    imagem_detalhes = models.ImageField(upload_to="tratamentos/detalhes/", blank=True, null=True)
    especificacao_tecnica_para_pacientes = models.FileField(upload_to="pdf_especificacao_pacientes/", blank=True, null=True)
    especificacao_tecnica_para_medicos = models.FileField(upload_to="pdf_especificacao_medicos/", blank=True, null=True)
    quando_usar = models.TextField(blank=True)    
    tipo_tratamento = models.ManyToManyField(TipoTratamento, blank=True)
    custo_medicamento = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    links_externos = models.TextField(blank=True, null=True)
    alertas = models.TextField(blank=True, null=True)
    grupo = models.CharField(max_length=20, choices=GRUPO_CHOICES, default="adultos")
    links_externos = models.TextField(blank=True, null=True)

    risco_morte = models.BooleanField(
        default=False,
        verbose_name="Risco de morte?"
    )

    circunstancias_risco_morte = models.TextField(
        blank=True,
        null=True,
        verbose_name="Circunstâncias de risco de morte"
    )

    risco_dano_irreversivel_saude = models.BooleanField(
        default=False,
        verbose_name="Risco de dano irreversível à saúde?"
    )

    circunstancias_risco_permanente_saude = models.TextField(
        blank=True,
        null=True,
        verbose_name="Circunstâncias de risco permanente à saúde"
    )

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
    tratamento = models.ForeignKey(
        "DetalhesTratamentoResumo",
        on_delete=models.CASCADE,
        related_name="condicoes_relacionadas"
    )

    condicao = models.ForeignKey(
        "CondicaoSaude",
        on_delete=models.CASCADE,
        related_name="tratamentos_relacionados"
    )

    descricao = models.TextField(blank=True)

    aparecer_na_lista = models.BooleanField(
        default=True,
        verbose_name="Aparecer na lista da doença"
    )

    class Meta:
        unique_together = ("tratamento", "condicao")

    def __str__(self):
        return f"{self.tratamento} - {self.condicao}"
    

class TipoEficacia(models.Model):
    tipo_eficacia = models.CharField(max_length=255)
    slug = models.SlugField(max_length=140, unique=True, blank=True, null=True, db_index=True)

    descricao = models.TextField(blank=True, null=True)
    outcome_type = models.CharField(max_length=255, blank=True, default="")
    outcome_slug = models.SlugField(max_length=140, unique=True, blank=True, null=True, db_index=True)

    imagem = models.ImageField(upload_to="icones_eficacia/", blank=True, null=True)
    eficacia_por_tipo = models.ManyToManyField(
        "EficaciaPorTipo",
        related_name="tipos_de_eficacia",
        blank=True,
    )

    def save(self, *args, **kwargs):
        if self.tipo_eficacia:
            base = slugify(self.tipo_eficacia) or "tipo"
            slug = base
            i = 2
            while TipoEficacia.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{i}"
                i += 1
            self.slug = slug

        if self.outcome_type:
            base = slugify(self.outcome_type) or "outcome"
            slug = base
            i = 2
            while TipoEficacia.objects.filter(outcome_slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{i}"
                i += 1
            self.outcome_slug = slug
        else:
            self.outcome_slug = None

        super().save(*args, **kwargs)

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

from django.db import models


class EficaciaPorEvidencia(models.Model):
    evidencia = models.ForeignKey(
        EvidenciasClinicas,
        on_delete=models.CASCADE,
        related_name="eficacia_por_evidencias"
    )
    tipo_eficacia = models.ForeignKey(TipoEficacia, on_delete=models.CASCADE)

    # Campos de participantes principais
    participantes_com_beneficio = models.IntegerField(default=0)
    participantes_iniciaram_tratamento = models.IntegerField(default=0)

    # Novo campo: pesquisa com placebo
    feito_pesquisa_com_placebo = models.BooleanField(
        default=False,
        verbose_name="Feito pesquisa com placebo?"
    )

    # Campos do placebo
    tipo_eficacia_placebo = models.ForeignKey(
        TipoEficacia,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="eficacia_placebo_tipos",
        verbose_name="Tipo eficácia usuários placebo"
    )
    participantes_receberam_placebo = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Participantes que receberam placebo"
    )
    participantes_placebo_com_beneficio = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Participantes placebo com benefício"
    )

    @property
    def percentual_eficacia_calculado(self):
        if self.participantes_iniciaram_tratamento > 0:
            return (
                self.participantes_com_beneficio
                / self.participantes_iniciaram_tratamento
            ) * 100
        return 0.0

    @property
    def eficacia_placebo_calculada(self):
        if (
            self.participantes_receberam_placebo
            and self.participantes_receberam_placebo > 0
            and self.participantes_placebo_com_beneficio is not None
        ):
            return (
                self.participantes_placebo_com_beneficio
                / self.participantes_receberam_placebo
            ) * 100
        return 0.0

    def __str__(self):
        return (
            f"{self.evidencia.titulo} - "
            f"{self.tipo_eficacia.tipo_eficacia} - "
            f"Eficácia: {self.percentual_eficacia_calculado:.2f}%"
        )

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



class PaginaListaTratamento(models.Model):

    tratamentos_ocultos = models.ManyToManyField(
    "DetalhesTratamentoResumo",
    blank=True,
    related_name="listas_em_que_foi_ocultado",
    verbose_name="Tratamentos ocultos desta lista",
)
    
    publicada = models.BooleanField(default=True)

    condicao_saude = models.ForeignKey(
        "core.CondicaoSaude",
        on_delete=models.PROTECT,
        related_name="paginas_listas",
    )

    tipo_eficacia = models.ForeignKey(
        "core.TipoEficacia",
        on_delete=models.PROTECT,
        related_name="paginas_listas",
    )

    template = models.CharField(
        max_length=200,
        default="core/lista_tratamentos.html",  # <<< importante bater com o caminho real
        help_text="Template django que renderiza a lista",
    )

    titulo = models.CharField(max_length=255, blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("condicao_saude", "tipo_eficacia")
        verbose_name = "URLs Listas"
        verbose_name_plural = "URLs Listas"

    def __str__(self):
        return f"{self.condicao_saude} / {self.tipo_eficacia}"
    
class TreatmentsUSAReacaoAdversaTeste(models.Model):
    treatment_usa = models.ForeignKey(
        'TreatmentsUSA',
        on_delete=models.CASCADE,
        related_name='reacoes_adversas_teste_detalhes'
    )
    reacao_adversa = models.ForeignKey(
        ReacaoAdversa,
        on_delete=models.CASCADE,
        related_name='usa_test_treatments'
    )
    grau_comunalidade = models.CharField(max_length=100, blank=True, null=True)
    reacao_min = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    reacao_max = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)

    class Meta:
        verbose_name = "USA Treatment Adverse Reaction Test Detail"
        verbose_name_plural = "USA Treatment Adverse Reaction Test Details"

    def __str__(self):
        return f"{self.treatment_usa} - {self.reacao_adversa}"

from django.db import models
from django.utils.text import slugify


class TreatmentsUSACondition(models.Model):
    treatment = models.ForeignKey(
        "TreatmentsUSA",
        on_delete=models.CASCADE,
        related_name="condition_relations"
    )
    condition = models.ForeignKey(
        "CondicaoSaude",
        on_delete=models.CASCADE,
        related_name="usa_treatment_relations"
    )
    description = models.TextField(blank=True)
    appear_on_list = models.BooleanField(default=True)

    class Meta:
        unique_together = ("treatment", "condition")

    def __str__(self):
        return f"{self.treatment} - {self.condition}"


class TreatmentsUSA(models.Model):
    tratamento_br = models.ForeignKey(
        "DetalhesTratamentoResumo",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tratamentos_usa",
        verbose_name="Brazil treatment"
    )

    tipos_eficacia = models.ManyToManyField(
        'EficaciaPorEvidencia',
        blank=True,
        verbose_name="Efficacy types"
    )

    reacoes_adversas_teste = models.ManyToManyField(
        ReacaoAdversa,
        through='TreatmentsUSAReacaoAdversaTeste',
        related_name='usa_treatments_with_test_reaction',
        blank=True,
        verbose_name="Adverse reactions test"
)
    GROUP_CHOICES = (
        ("children", "Children under 12 years"),
        ("teenagers", "Teenagers 12 to 17 years"),
        ("elderly", "Elderly 65+"),
        ("adults", "Adults"),
        ("lactating", "Lactating"),
        ("pregnancy", "Pregnancy"),
    )

    UNIT_CHOICES = [
        ('minute', 'Minute'),
        ('hour', 'Hour'),
        ('day', 'Day'),
        ('session', 'Session'),
        ('second', 'Second'),
        ('week', 'Weeks'),
    ]

    name = models.CharField(max_length=200, blank=True, verbose_name="Name")
    description = models.TextField(blank=True, verbose_name="Description")

    health_conditions = models.ManyToManyField(
        "CondicaoSaude",
        blank=True,
        related_name="usa_treatments",
        verbose_name="Health conditions"
    )

    comment = models.TextField(blank=True, null=True, verbose_name="Comment")
    category = models.CharField(max_length=100, blank=True, null=True, verbose_name="Category")
    clinical_evidence = models.TextField(blank=True, null=True, verbose_name="Clinical evidence")
    active_ingredient = models.CharField(max_length=20000, blank=True, verbose_name="Active ingredient")

    slug = models.SlugField(max_length=200, blank=True, null=True, unique=True)

    manufacturer = models.CharField(max_length=200, blank=True, verbose_name="Manufacturer")
    rating = models.IntegerField(null=True, blank=True, verbose_name="Rating")

    efficacy_min = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, verbose_name="Min efficacy")
    efficacy_max = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, verbose_name="Max efficacy")

    effect_time_min = models.IntegerField(blank=True, null=True, verbose_name="Min effect time")
    effect_time_max = models.IntegerField(blank=True, null=True, verbose_name="Max effect time")
    effect_time_unit = models.CharField(
        max_length=10,
        choices=UNIT_CHOICES,
        default='minute',
        verbose_name="Effect time unit"
    )

    treatment_purchase_link = models.URLField(blank=True, null=True, verbose_name="Treatment purchase link")
    cost_specification = models.CharField(max_length=200, blank=True, verbose_name="Cost specification")

    adverse_reactions = models.ManyToManyField(
        ReacaoAdversa,
        blank=True,
        related_name='usa_treatments_with_reaction',
        verbose_name="Adverse reactions"
    )

    drug_interaction = models.URLField(blank=True, null=True, verbose_name="Drug interaction")
    generic_similar = models.URLField(blank=True, null=True, verbose_name="Generic/similar")
    electronic_prescription = models.URLField(blank=True, null=True, verbose_name="Electronic prescription")
    specialist_opinion = models.URLField(blank=True, null=True, verbose_name="Specialist opinion")
    professional_links = models.URLField(blank=True, null=True, verbose_name="Professional links")

    alert = models.TextField(blank=True, null=True, verbose_name="Alert")
    image = models.ImageField(upload_to="tratamentos_usa/", blank=True, null=True, verbose_name="Image")
    detail_image = models.ImageField(upload_to="tratamentos_usa/detalhes/", blank=True, null=True, verbose_name="Detail image")
    when_to_use = models.TextField(blank=True, verbose_name="When to use")
    treatment_type = models.ManyToManyField(TipoTratamento, blank=True, verbose_name="Treatment type")
    treatment_cost = models.DecimalField(max_digits=7, decimal_places=2, blank=True, null=True, verbose_name="Treatment cost")
    external_links = models.TextField(blank=True, null=True, verbose_name="External links")
    alerts = models.TextField(blank=True, null=True, verbose_name="Alerts")

    group = models.CharField(max_length=20, choices=GROUP_CHOICES, default="adults", verbose_name="Group")

    indicated_children = models.CharField(
        max_length=100,
        choices=[('YES', 'Yes'), ('NO', 'No')],
        default='NO',
        verbose_name="Indicated for children"
    )
    reason_children = models.TextField(blank=True, null=True, verbose_name="Reason children")

    indicated_teenagers = models.CharField(
        max_length=100,
        choices=[('YES', 'Yes'), ('NO', 'No')],
        default='NO',
        verbose_name="Indicated for teenagers"
    )
    reason_teenagers = models.TextField(blank=True, null=True, verbose_name="Reason teenagers")

    indicated_elderly = models.CharField(
        max_length=100,
        choices=[('YES', 'Yes'), ('NO', 'No')],
        default='NO',
        verbose_name="Indicated for elderly"
    )
    reason_elderly = models.TextField(blank=True, null=True, verbose_name="Reason elderly")

    indicated_adults = models.CharField(
        max_length=100,
        choices=[('YES', 'Yes'), ('NO', 'No')],
        default='YES',
        verbose_name="Indicated for adults"
    )
    reason_adults = models.TextField(blank=True, null=True, verbose_name="Reason adults")

    indicated_lactating = models.CharField(
        max_length=100,
        choices=[('YES', 'Yes'), ('NO', 'No')],
        default='YES',
        verbose_name="Indicated for lactating"
    )
    reason_lactating = models.TextField(blank=True, null=True, verbose_name="Reason lactating")

    indicated_pregnancy = models.CharField(
        max_length=100,
        choices=[('YES', 'Yes'), ('NO', 'No')],
        default='YES',
        verbose_name="Indicated for pregnancy"
    )
    reason_pregnancy = models.TextField(blank=True, null=True, verbose_name="Reason pregnancy")

    contraindications = models.ManyToManyField(
        Contraindicacao,
        blank=True,
        related_name="usa_treatments_with_contraindication",
        verbose_name="Contraindications"
    )

    risk = models.FloatField(
        default=0.0,
        help_text="Risk percentage of side effects (0 to 100%)",
        verbose_name="Risk"
    )
    
    def save(self, *args, **kwargs):
        if not self.slug and self.name:
            base_slug = slugify(self.name)
            slug = base_slug
            i = 2
            while TreatmentsUSA.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{i}"
                i += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name or "Unnamed USA Treatment"

    def pluralize_unit(self, value):
        exceptions = {
            'session': 'sessions',
        }
        unit = self.effect_time_unit
        if value == 1:
            return unit
        return exceptions.get(unit, unit + 's')

    @property
    def effect_time_min_formatted(self):
        if self.effect_time_min is None:
            return ""
        return f"{self.effect_time_min} {self.pluralize_unit(self.effect_time_min)}"

    @property
    def effect_time_max_formatted(self):
        if self.effect_time_max is None:
            return ""
        return f"{self.effect_time_max} {self.pluralize_unit(self.effect_time_max)}"

    @property
    def effect_time_range_formatted(self):
        return f"{self.effect_time_min_formatted} to {self.effect_time_max_formatted}"

    class Meta:
        verbose_name = "Treatment USA"
        verbose_name_plural = "Treatments USA"


class TreatmentUrlEnglish(models.Model):
    condition = models.ForeignKey(
        "core.CondicaoSaude",
        on_delete=models.CASCADE,
        related_name="english_treatment_pages",
    )
    treatment = models.ForeignKey(
        "core.TreatmentsUSA",
        on_delete=models.CASCADE,
        related_name="english_pages",
    )

    published = models.BooleanField(default=True)

    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.TextField(blank=True)

    custom_title = models.CharField(max_length=255, blank=True)
    custom_description = models.TextField(blank=True)

    cta_label = models.CharField(max_length=120, blank=True)
    cta_url = models.URLField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("condition", "treatment")

        # 👇 NOME QUE VAI APARECER NO ADMIN
        verbose_name = "URL Treatment"
        verbose_name_plural = "URLs Treatments"

    def __str__(self):
        return f"{self.condition.nome} - {self.treatment.name}"
    
class TreatmentListUrlEnglish(models.Model):
    published = models.BooleanField(default=True)

    health_condition = models.ForeignKey(
        "core.CondicaoSaude",
        on_delete=models.PROTECT,
        related_name="english_list_pages",
    )

    efficacy_type = models.ForeignKey(
        "core.TipoEficacia",
        on_delete=models.PROTECT,
        related_name="english_list_pages",
        null=True,
        blank=True,
    )

    template = models.CharField(
        max_length=200,
        default="core/en/treatment_list.html",
    )

    title = models.CharField(max_length=255, blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["health_condition", "efficacy_type"],
                name="unique_english_list_per_condition_and_efficacy",
            )
        ]

        # 👇 NOME QUE VAI APARECER NO ADMIN
        verbose_name = "URL List in English"
        verbose_name_plural = "URLs Lists in English"

    def __str__(self):
        if self.efficacy_type:
            return f"{self.health_condition} / {self.efficacy_type}"
        return f"{self.health_condition} / all"
    

class SegurancaUso(models.Model):
    GRUPO_CRIANCAS = "criancas"
    GRUPO_ADOLESCENTES = "adolescentes"
    GRUPO_IDOSOS = "idosos"
    GRUPO_ADULTOS = "adultos"
    GRUPO_LACTANTES = "lactantes"
    GRUPO_GRAVIDEZ = "gravidez"

    GRUPO_CHOICES = [
        (GRUPO_CRIANCAS, "Crianças"),
        (GRUPO_ADOLESCENTES, "Adolescentes"),
        (GRUPO_IDOSOS, "Idosos"),
        (GRUPO_ADULTOS, "Adultos"),
        (GRUPO_LACTANTES, "Lactantes"),
        (GRUPO_GRAVIDEZ, "Gravidez"),
    ]

    tratamento = models.ForeignKey(
        "DetalhesTratamentoResumo",
        on_delete=models.PROTECT,
        related_name="segurancas_uso",
        verbose_name="Tratamento",
    )

    grupo = models.CharField(
        "Grupo",
        max_length=30,
        choices=GRUPO_CHOICES,
    )

    tem_seguranca_uso = models.BooleanField(
        "Tem segurança de uso?",
        default=False,
    )

    motivo = models.TextField(
        "Motivo",
        blank=True,
        default="",
    )

    numero_participantes = models.PositiveIntegerField(
        "Número de participantes",
        null=True,
        blank=True,
    )

    autores = models.TextField(
        "Autores",
        blank=True,
        default="",
    )

    link_estudo = models.URLField(
        "Link do estudo",
        max_length=1000,
        blank=True,
        default="",
    )

    data_publicacao = models.DateField(
        "Data de publicação",
        null=True,
        blank=True,
    )

    paises = models.CharField(
        "Países",
        max_length=500,
        blank=True,
        default="",
    )

    titulo = models.CharField(
        "Título",
        max_length=500,
        blank=True,
        default="",
    )

    fonte_local_publicacao = models.CharField(
        "Fonte / local de publicação",
        max_length=500,
        blank=True,
        default="",
    )

    imagem_local_publicacao = models.ImageField(
        "Imagem do local de publicação",
        upload_to="seguranca_uso/fontes/",
        null=True,
        blank=True,
    )

    descricao_pesquisa = models.TextField(
        "Descrição da pesquisa",
        blank=True,
        default="",
    )

    criado_em = models.DateTimeField(
        "Criado em",
        auto_now_add=True,
    )

    atualizado_em = models.DateTimeField(
        "Atualizado em",
        auto_now=True,
    )

    class Meta:
        verbose_name = "Segurança de uso"
        verbose_name_plural = "Segurança de uso"
        ordering = ["tratamento__nome", "grupo", "-data_publicacao"]

    def __str__(self):
        return f"{self.tratamento} — {self.get_grupo_display()}"
    
class FatorRisco(models.Model):
    TIPO_GENETICO = "genetico"
    TIPO_COMPORTAMENTAL = "comportamental"
    TIPO_AMBIENTAL = "ambiental"
    TIPO_CLINICO = "clinico"
    TIPO_HORMONAL = "hormonal"
    TIPO_ALIMENTAR = "alimentar"
    TIPO_HISTORICO_FAMILIAR = "historico_familiar"
    TIPO_OUTRO = "outro"

    TIPO_FATOR_RISCO_CHOICES = [
        (TIPO_GENETICO, "Genético"),
        (TIPO_COMPORTAMENTAL, "Comportamental"),
        (TIPO_AMBIENTAL, "Ambiental"),
        (TIPO_CLINICO, "Clínico"),
        (TIPO_HORMONAL, "Hormonal"),
        (TIPO_ALIMENTAR, "Alimentar"),
        (TIPO_HISTORICO_FAMILIAR, "Histórico familiar"),
        (TIPO_OUTRO, "Outro"),
    ]

    condicao_saude = models.ForeignKey(
        "CondicaoSaude",
        on_delete=models.PROTECT,
        related_name="fatores_risco",
        verbose_name="Condição de saúde",
    )

    tipo_fator_risco = models.CharField(
        "Tipo do fator de risco",
        max_length=50,
        choices=TIPO_FATOR_RISCO_CHOICES,
    )

    nome = models.CharField(
        "Nome do fator de risco",
        max_length=255,
    )

    descricao = models.TextField(
        "Descrição do fator de risco",
        blank=True,
        default="",
    )

    criado_em = models.DateTimeField(
        "Criado em",
        auto_now_add=True,
    )

    atualizado_em = models.DateTimeField(
        "Atualizado em",
        auto_now=True,
    )

    class Meta:
        verbose_name = "Fator de risco"
        verbose_name_plural = "Fatores de risco"
        ordering = ["condicao_saude__nome", "tipo_fator_risco", "nome"]

    def __str__(self):
        return f"{self.nome} — {self.condicao_saude}"
    
from django.core.validators import MinValueValidator, MaxValueValidator, FileExtensionValidator


class EvidenciaFatorRisco(models.Model):
    CORRELACAO = "correlacao"
    CAUSA = "causa"

    TIPO_RELACAO_CHOICES = [
        (CORRELACAO, "Correlação"),
        (CAUSA, "Causa"),
    ]

    GRUPO_CRIANCAS = "criancas"
    GRUPO_ADOLESCENTES = "adolescentes"
    GRUPO_IDOSOS = "idosos"
    GRUPO_ADULTOS = "adultos"
    GRUPO_LACTANTES = "lactantes"
    GRUPO_GRAVIDEZ = "gravidez"

    GRUPO_CHOICES = [
        (GRUPO_CRIANCAS, "Crianças"),
        (GRUPO_ADOLESCENTES, "Adolescentes"),
        (GRUPO_IDOSOS, "Idosos"),
        (GRUPO_ADULTOS, "Adultos"),
        (GRUPO_LACTANTES, "Lactantes"),
        (GRUPO_GRAVIDEZ, "Gravidez"),
    ]

    condicao_saude = models.ForeignKey(
        "CondicaoSaude",
        on_delete=models.PROTECT,
        related_name="evidencias_fatores_risco",
        verbose_name="Condição de saúde",
    )

    fator_risco = models.ForeignKey(
        "FatorRisco",
        on_delete=models.PROTECT,
        related_name="evidencias_fatores_risco",
        verbose_name="Fator de risco",
    )

    correlacao_ou_causa = models.CharField(
        "Correlação ou causa",
        max_length=20,
        choices=TIPO_RELACAO_CHOICES,
    )

    grupo = models.CharField(
        "Grupo",
        max_length=30,
        choices=GRUPO_CHOICES,
    )

    prevalencia = models.DecimalField(
        "Prevalência (%)",
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100),
        ],
        help_text="Informe o percentual entre 0 e 100.",
    )

    requer_exposicao = models.BooleanField(
        "Requer exposição a algum agente/situação para ser fator de risco?",
        default=False,
    )

    agentes_situacoes_necessarias = models.TextField(
        "Agentes/situações necessárias para esse item ser um fator de risco",
        blank=True,
        default="",
    )

    ano_dados_coletados = models.PositiveSmallIntegerField(
        "Data dos dados coletados (ano)",
        null=True,
        blank=True,
    )

    pais_dados_pesquisados = models.CharField(
        "País dos dados pesquisados",
        max_length=255,
        blank=True,
        default="",
    )

    rigor_pesquisa = models.CharField(
        "Rigor da pesquisa",
        max_length=255,
        blank=True,
        default="",
        help_text="Ex.: alto, médio, baixo, revisão sistemática, estudo observacional, metanálise etc.",
    )

    quantidade_participantes = models.PositiveIntegerField(
        "Quantidade de participantes",
        null=True,
        blank=True,
    )

    data_pesquisa = models.DateField(
        "Data da pesquisa",
        null=True,
        blank=True,
    )

    pais_pesquisa = models.CharField(
        "País da pesquisa",
        max_length=255,
        blank=True,
        default="",
    )

    nomes_autores = models.TextField(
        "Nomes dos autores",
        blank=True,
        default="",
    )

    titulo_pesquisa = models.CharField(
        "Título da pesquisa",
        max_length=500,
    )

    tipo_identificador_pesquisa = models.CharField(
        "Tipo de identificador da pesquisa",
        max_length=100,
        blank=True,
        default="",
        help_text="Ex.: DOI, PMID, ClinicalTrials.gov, outro.",
    )

    identificador_pesquisa = models.CharField(
        "Identificador DOI ou outro identificador da pesquisa",
        max_length=255,
        blank=True,
        default="",
    )

    descricao_pesquisa = models.TextField(
        "Descrição da pesquisa",
        blank=True,
        default="",
    )

    link_pesquisa = models.URLField(
        "Link para a pesquisa",
        max_length=1000,
        blank=True,
        default="",
    )

    arquivo_pdf_pesquisa = models.FileField(
        "Subir pesquisa em PDF",
        upload_to="evidencias_fatores_risco/pdfs/",
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=["pdf"])],
    )

    criado_em = models.DateTimeField(
        "Criado em",
        auto_now_add=True,
    )

    atualizado_em = models.DateTimeField(
        "Atualizado em",
        auto_now=True,
    )

    class Meta:
        verbose_name = "Evidência fator de risco"
        verbose_name_plural = "Evidências fatores de risco"
        ordering = [
            "condicao_saude__nome",
            "fator_risco__nome",
            "grupo",
            "-data_pesquisa",
        ]
        db_table = "evidencias_fatores_risco"

    def __str__(self):
        return f"{self.condicao_saude} — {self.fator_risco} — {self.get_grupo_display()}"