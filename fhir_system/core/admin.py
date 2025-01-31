from django.contrib import admin
from .models import (
    Organization,
    SubstanceDefinition,
    Ingredient,
    ManufacturedItemDefinition,
    PackagedProductDefinition,
    AdministrableProductDefinition,
    MedicinalProductDefinition,
    RegulatedAuthorization,
    ClinicalUseDefinition,
    Composition,
    Binary
)
# Register your models here.

admin.site.register(Organization)
admin.site.register(SubstanceDefinition)
admin.site.register(Ingredient)
admin.site.register(ManufacturedItemDefinition)
admin.site.register(PackagedProductDefinition)
admin.site.register(AdministrableProductDefinition)
admin.site.register(MedicinalProductDefinition)
admin.site.register(RegulatedAuthorization)
admin.site.register(ClinicalUseDefinition)
admin.site.register(Composition)
admin.site.register(Binary)
