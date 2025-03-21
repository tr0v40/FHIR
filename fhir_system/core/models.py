from django.db import models


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

    class Meta:
        verbose_name = "Contraindicação"
        verbose_name_plural = "Contraindicações"

    def __str__(self):
        return self.nome


class ReacaoAdversa(models.Model):
    nome = models.CharField(max_length=200)
    descricao = models.TextField()
    risco_reacao = models.FloatField(default=0.0, help_text="Risco percentual de efeito colateral (0 a 100%)")
    imagem = models.ImageField(upload_to="reacoes_adversas/", blank=True, null=True)

    class Meta:
        verbose_name = "Reação Adversa"
        verbose_name_plural = "Reações Adversas"

    def __str__(self):
        return self.nome


class DetalhesTratamentoResumo(models.Model):
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
    categoria = models.CharField(max_length=100, blank=True, null=True)
    evidencia_clinica = models.TextField(blank=True, null=True)
    principio_ativo = models.CharField(max_length=200)
    fabricante = models.CharField(max_length=200)
    avaliacao = models.DecimalField(max_digits=3, decimal_places=2, blank=True, null=True)
    eficacia_min = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    eficacia_max = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    prazo_efeito_min = models.IntegerField()  # Para armazenar o tempo em minutos
    prazo_efeito_max = models.IntegerField()  
    imagem = models.ImageField(upload_to="tratamentos/", blank=True, null=True)
    confiabilidade_pesquisa = models.CharField(max_length=100, blank=True, null=True)
    funciona_para_todos = models.CharField(max_length=100, blank=True, null=True)
    adesao = models.CharField(max_length=200, blank=True, null=True)
    quando_tomar = models.TextField()
    realizar_tratamento_quando = models.TextField(blank=True, null=True)
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
    indicado_lactantes = models.CharField(max_length=100, choices=[('A', 'A'), ('B', 'B'), ('C', 'C')], default='C')
    motivo_lactantes = models.TextField(blank=True, null=True)
    indicado_gravidez= models.CharField(max_length=100, choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D'), ('X', 'X')], default='D')
    motivo_gravidez = models.TextField(blank=True, null=True)
    contraindicacoes = models.ManyToManyField(Contraindicacao, blank=True)
    reacoes_adversas = models.ManyToManyField(ReacaoAdversa, blank=True)
    risco = models.FloatField(default=0.0, help_text="Risco percentual de efeito colateral (0 a 100%)")

    class Meta:
        verbose_name = "Detalhes Tratamentos - Resumo"
        verbose_name_plural = "Detalhes Tratamentos - Resumo"

    def __str__(self):
        return self.nome

class EvidenciasClinicas(models.Model):
    tratamento = models.ForeignKey("DetalhesTratamentoResumo", on_delete=models.CASCADE, related_name="evidencias")
    titulo = models.CharField(max_length=255)
    descricao = models.TextField()
    condicao_saude = models.CharField(max_length=255, blank=True, null=True)
    grau_evidencia = models.CharField(max_length=100)
    estudo_publicado = models.CharField(max_length=255, blank=True, null=True)
    link_estudo = models.URLField(blank=True, null=True)
    data_publicacao = models.DateField(blank=True, null=True)
    autores = models.CharField(max_length=255, blank=True, null=True)
    imagem_estudo = models.ImageField(upload_to="evidencias/", blank=True, null=True)
    eficacia_min = models.DecimalField(max_digits=5, decimal_places=2)
    eficacia_max = models.DecimalField(max_digits=5, decimal_places=2)
    pdf_estudo = models.FileField(upload_to="pdf_estudos/", blank=True, null=True)
    link_pdf_estudo = models.URLField(blank=True, null=True)
    referencia_bibliografica = models.TextField(blank=True, null=True)

    # Novo campo para reações adversas
    risco_reacao = models.CharField(max_length=100, blank=True, null=True)  # ex: "1% a 10% COMUM"

    class Meta:
        verbose_name = "Evidência Clínica"
        verbose_name_plural = "Evidências Clínicas"

    def __str__(self):
        return f"{self.titulo} - {self.tratamento.nome}"
