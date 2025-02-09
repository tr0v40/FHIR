from django.db import models

class Organization(models.Model):
    name = models.CharField(max_length=255)
    address = models.TextField(blank=True, null=True)
    contact_info = models.TextField(blank=True, null=True)
    identifier = models.CharField(max_length=255, blank=True, null=True)

class SubstanceDefinition(models.Model):
    name = models.CharField(max_length=255)
    molecular_formula = models.CharField(max_length=255, blank=True, null=True)
    molecular_weight = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    manufacturer = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='substances')

class Ingredient(models.Model):
    substance = models.ForeignKey(SubstanceDefinition, on_delete=models.CASCADE, related_name='ingredients')
    role = models.CharField(max_length=255)  # Ativo, Excipiente, etc.
    strength = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

class ManufacturedItemDefinition(models.Model):
    name = models.CharField(max_length=255)
    form = models.CharField(max_length=255)  # Comprimido, Cápsula, Líquido, etc.
    ingredients = models.ManyToManyField(Ingredient, related_name='manufactured_items')

class PackagedProductDefinition(models.Model):
    package_type = models.CharField(max_length=255)
    quantity = models.IntegerField()
    manufactured_item = models.ForeignKey(ManufacturedItemDefinition, on_delete=models.CASCADE, related_name='packaged_products')

class AdministrableProductDefinition(models.Model):
    route_of_administration = models.CharField(max_length=255)
    dosage_form = models.CharField(max_length=255)
    packaged_product = models.ForeignKey(PackagedProductDefinition, on_delete=models.CASCADE, related_name='administrable_products')

class MedicinalProductDefinition(models.Model):
    name = models.CharField(max_length=255)
    administrable_product = models.ForeignKey(AdministrableProductDefinition, on_delete=models.CASCADE, related_name='medicinal_products')
    manufacturer = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='medicinal_products')

class RegulatedAuthorization(models.Model):
    authorization_number = models.CharField(max_length=255)
    status = models.CharField(max_length=255)  # Aprovado, Pendente, Suspenso
    date_issued = models.DateField()
    holder = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='authorizations')
    medicinal_product = models.ForeignKey(MedicinalProductDefinition, on_delete=models.CASCADE, related_name='authorizations')

class ClinicalUseDefinition(models.Model):
    medicinal_product = models.ForeignKey(MedicinalProductDefinition, on_delete=models.CASCADE, related_name='clinical_uses')
    contraindications = models.TextField(blank=True, null=True)
    indications = models.TextField(blank=True, null=True)
    interactions = models.TextField(blank=True, null=True)
    adverse_effects = models.TextField(blank=True, null=True)


class Composition(models.Model):
    title = models.CharField(max_length=255)
    date = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='compositions')
    medicinal_product = models.ForeignKey(MedicinalProductDefinition, on_delete=models.CASCADE, related_name='compositions')
    section_text = models.TextField()

class Binary(models.Model):
    content_type = models.CharField(max_length=100)
    data = models.BinaryField()
    medicinal_product = models.ForeignKey(MedicinalProductDefinition, on_delete=models.CASCADE, related_name='binaries')

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
    CID = models.CharField(max_length=50, default="CID-NÃO-ESPECIFICADO", blank=True, null=True)
    # Campo com lógica invertida
    not_indicated = models.BooleanField(
        default=False,  # Se False, é indicado para uso
        verbose_name="Não Indicado para Uso"
    )

    def is_indicated(self):
        """Retorna se o item é indicado para uso"""
        return not self.not_indicated  # Se False, está indicado

    def __str__(self):
        return f"{self.element_id} - Indicado para Uso: {'Sim' if self.is_indicated() else 'Não'}"

from django.db import models

class AgeRangeChoices(models.TextChoices):
    FAIXA_1 = "0-10", "0 a 10 anos"
    FAIXA_2 = "11-20", "11 a 20 anos"
    FAIXA_3 = "21-30", "21 a 30 anos"
    FAIXA_4 = "31-60", "31 a 60 anos"
    FAIXA_7 = "61-70", "61 a 70 anos"
    FAIXA_8 = "71-80", "71 a 80 anos"
    FAIXA_9 = "81+", "81 anos ou mais"

    # Novos grupos adicionados
    GRAVIDEZ = "gravidez", "Gravidez"
    LACTANTE = "lactante", "Lactante"

class StudyGroup(models.Model):
    element_id = models.CharField(
        max_length=20,
        primary_key=True,
        unique=True
    )

    study_group_idade = models.CharField(
        max_length=20,  # Aumentei o tamanho para acomodar os novos valores
        choices=AgeRangeChoices.choices,
        default=AgeRangeChoices.FAIXA_1,
        verbose_name="Faixa Etária"
    )

    def __str__(self):
        return f"Grupo {self.element_id} - {self.study_group_idade}"