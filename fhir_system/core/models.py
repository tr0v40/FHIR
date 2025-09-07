from django.db import models
from django.utils.text import slugify

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
    eficacia_min = models.DecimalField(max_digits=5, decimal_places=2)
    eficacia_max = models.DecimalField(max_digits=5, decimal_places=2)
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

    # 🔹 Novos campos vindos de ClinicalUseDefinition
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
    descricao = models.TextField(
        verbose_name="Descrição Relacionada à Condição de Saúde",
        blank=True, null=True
    )

    # 🔹 Novos campos
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

    nome = models.CharField(max_length=200)
    descricao = models.TextField()
    
    condicao_saude = models.ForeignKey(
        "CondicaoSaude",  # A tabela que será referenciada
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="detalhes_tratamento"
    )
    comentario = models.TextField(blank=True, null=True)
    categoria = models.CharField(max_length=100, blank=True, null=True)
    evidencia_clinica = models.TextField(blank=True, null=True)
    principio_ativo = models.CharField(max_length=200)
    
    
    slug = models.SlugField(max_length=200, blank=True, null=True, unique=True)


    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nome)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nome
    
    fabricante = models.CharField(max_length=200)
    comentario = models.TextField(null=True, blank=True)
    avaliacao = models.IntegerField(null=True, blank=True)  
    eficacia_min = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    eficacia_max = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    prazo_efeito_min = models.IntegerField()  # Para armazenar o tempo em minutos
    prazo_efeito_max = models.IntegerField()
    reacoes_adversas = models.ManyToManyField(
        ReacaoAdversa,
        through='DetalhesTratamentoReacaoAdversa',  # modelo intermediário
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
            # singular
            return unidade
        # plural com exceções
        return excecoes.get(unidade, unidade + 's')

    # Método para formatar prazo mínimo
    @property
    def prazo_efeito_min_formatado(self):
        return f"{self.prazo_efeito_min} {self.pluralizar_unidade(self.prazo_efeito_min)}"

    # Método para formatar prazo máximo
    @property
    def prazo_efeito_max_formatado(self):
        return f"{self.prazo_efeito_max} {self.pluralizar_unidade(self.prazo_efeito_max)}"

    # Opcional: método para exibir a faixa completa
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

    quando_usar = models.TextField()    
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

import pycountry

# Monta a lista de países automaticamente
COUNTRIES = [(country.name, country.name) for country in pycountry.countries]



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
        verbose_name="País"
    )
    country = models.CharField(        
        max_length=100,
        choices=COUNTRIES,
        blank=True,
        null=True,
        verbose_name="Country"
    )

    imagem_estudo = models.ImageField(upload_to="evidencias/", blank=True, null=True)
    fonte = models.CharField(max_length=255, blank=True, null=True, verbose_name="Fonte")
    eficacia_min = models.DecimalField(max_digits=5, decimal_places=2)
    eficacia_max = models.DecimalField(max_digits=5, decimal_places=2)
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

    tipos_eficacia = models.ManyToManyField('TipoEficacia', through='EficaciaPorEvidencia', related_name='evidencias_eficacia')
    CURA = 'cura'
    ELIMINACAO_SINTOMAS = 'eliminacao_sintomas'
    REDUCAO_SINTOMAS = 'reducao_sintomas'
    PREVENCAO = 'prevencao'

    TIPO_EFICACIA_CHOICES = [
        (CURA, 'Cura'),
        (ELIMINACAO_SINTOMAS, 'Eliminação dos sintomas'),
        (REDUCAO_SINTOMAS, 'Redução dos sintomas'),
        (PREVENCAO, 'Prevenção'),
    ]

    # Adicionando o campo tipo_eficacia
    tipo_eficacia = models.CharField(
        max_length=20,
        choices=TIPO_EFICACIA_CHOICES,
        default=CURA,  # Você pode definir o valor padrão, caso necessário
    )

    # Outros campos da model
    # ...

    def __str__(self):
        return self.tipo_eficacia

    participantes_com_beneficio = models.IntegerField(default=0)
    participantes_iniciaram_tratamento = models.IntegerField(default=0)
    percentual = models.CharField(max_length=100, blank=True, null=True) 

    # Novo campo para reações adversas
    risco_reacao = models.CharField(max_length=100, blank=True, null=True)  # ex: "1% a 10% COMUM"

    class Meta:
        verbose_name = "Evidência Clínica"
        verbose_name_plural = "Evidências Clínicas"

    def __str__(self):
        return f"{self.titulo} - {self.tratamento.nome}"
    @property
    def percentual_eficacia(self):
        """Calcula o percentual de eficácia automaticamente"""
        if self.participantes_iniciaram_tratamento > 0:
            return (self.participantes_com_beneficio / self.participantes_iniciaram_tratamento) * 100
        return 0.0  # Caso não haja participantes iniciados, retorna 0


class Tratamento(models.Model):
    nome = models.CharField(max_length=255)
    descricao = models.TextField()
    # outros campos do tratamento

class Avaliacao(models.Model):
    tratamento = models.ForeignKey(Tratamento, on_delete=models.CASCADE, related_name='avaliacoes')
    comentario = models.TextField()
    estrelas = models.PositiveIntegerField(choices=[(1, '1 estrela'), (2, '2 estrelas'), (3, '3 estrelas'), 
                                                    (4, '4 estrelas'), (5, '5 estrelas')])
    data = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Avaliação para {self.tratamento.nome} - {self.estrelas} estrelas"
    


# pré-requisito nos models (resumo)
class TratamentoCondicao(models.Model):
    tratamento = models.ForeignKey('DetalhesTratamentoResumo', on_delete=models.CASCADE, related_name='condicoes_relacionadas')
    condicao  = models.ForeignKey('CondicaoSaude', on_delete=models.CASCADE, related_name='tratamentos_relacionados')
    descricao = models.TextField(blank=True, null=True)   # descrição específica desta condição no contexto do tratamento
    class Meta:
        unique_together = ('tratamento', 'condicao')
    class Meta:
        verbose_name = "Tratamento Condição"
        verbose_name_plural = "Tratamentos Condições"

    def __str__(self):
        return f"{self.condicao.nome}"
    

class TipoEficacia(models.Model):
    tipo_eficacia = models.CharField(max_length=255)  # Certifique-se de que este campo existe
    descricao = models.TextField(blank=True, null=True)  # Se for esse campo, adicione-o

    eficacia_por_tipo = models.ManyToManyField('EficaciaPorTipo', related_name='tipos_de_eficacia', blank=True)

    def __str__(self):
        return self.tipo_eficacia  # Isso deve ser acessado na admin





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
