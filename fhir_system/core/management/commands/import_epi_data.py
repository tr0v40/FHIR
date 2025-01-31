import requests
import json
from django.core.management.base import BaseCommand
from core.models import (
    Organization, SubstanceDefinition, Ingredient, ManufacturedItemDefinition, 
    PackagedProductDefinition, AdministrableProductDefinition, MedicinalProductDefinition, 
    RegulatedAuthorization, ClinicalUseDefinition, Composition, Binary
)

FHIR_EPI_URL = "https://hl7.org/fhir/uv/emedicinal-product-info/epi-example.json"

class Command(BaseCommand):
    help = "Importa dados do FHIR ePI para o banco de dados Django"

    def handle(self, *args, **kwargs):
        response = requests.get(FHIR_EPI_URL)
        if response.status_code != 200:
            self.stderr.write(self.style.ERROR("Erro ao obter os dados do FHIR ePI"))
            return

        data = response.json()
        self.import_data(data)

    def import_data(self, data):
        self.stdout.write(self.style.SUCCESS("Importando dados do ePI..."))

        # Criar ou obter Organizações
        for org_data in data.get("Organization", []):
            org, created = Organization.objects.get_or_create(
                name=org_data["name"],
                defaults={
                    "address": org_data.get("address", ""),
                    "contact_info": org_data.get("contact", ""),
                    "identifier": org_data.get("identifier", "")
                }
            )

        # Criar ou obter Substâncias
        for sub_data in data.get("SubstanceDefinition", []):
            manufacturer = Organization.objects.filter(name=sub_data["manufacturer"]).first()
            SubstanceDefinition.objects.get_or_create(
                name=sub_data["name"],
                defaults={
                    "molecular_formula": sub_data.get("molecular_formula", ""),
                    "molecular_weight": sub_data.get("molecular_weight", 0),
                    "manufacturer": manufacturer
                }
            )

        # Criar ou obter Ingredientes
        for ing_data in data.get("Ingredient", []):
            substance = SubstanceDefinition.objects.filter(name=ing_data["substance"]).first()
            Ingredient.objects.get_or_create(
                substance=substance,
                role=ing_data["role"],
                strength=ing_data.get("strength", 0)
            )

        # Criar Medicinal Products
        for med_data in data.get("MedicinalProductDefinition", []):
            manufacturer = Organization.objects.filter(name=med_data["manufacturer"]).first()
            MedicinalProductDefinition.objects.get_or_create(
                name=med_data["name"],
                defaults={"manufacturer": manufacturer}
            )

        self.stdout.write(self.style.SUCCESS("Importação concluída com sucesso!"))
