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
