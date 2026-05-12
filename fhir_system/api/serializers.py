from rest_framework import serializers



from core.models import (
    DetalhesTratamentoResumo,
    CondicaoSaude,
    ReacaoAdversa,
    Contraindicacao,
    TipoTratamento,
    EvidenciasClinicas,
    Avaliacao,
    EficaciaPorEvidencia,
    TipoEficacia,
    DetalhesTratamentoReacaoAdversa,
    TreatmentsUSA,
)

# -------------------------
# Serializers "completos" (compatibilidade)
# -------------------------

class DetalhesTratamentoReacaoAdversaSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetalhesTratamentoReacaoAdversa
        fields = ['id', 'tratamento', 'reacao_adversa', 'grau_comunalidade', 'reacao_min', 'reacao_max']


class CondicaoSaudeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CondicaoSaude
        fields = '__all__'


class ReacaoAdversaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReacaoAdversa
        fields = '__all__'


class ContraindicacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contraindicacao
        fields = '__all__'


class TipoTratamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoTratamento
        fields = '__all__'


class TipoEficaciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoEficacia
        fields = ['id', 'tipo_eficacia', 'descricao', 'imagem']


class EficaciaPorEvidenciaSerializer(serializers.ModelSerializer):
    tipo_eficacia = TipoEficaciaSerializer(read_only=True)
    percentual_eficacia_calculado = serializers.ReadOnlyField()
    nome_tratamento = serializers.CharField(source='evidencia.tratamento.nome', read_only=True)

    class Meta:
        model = EficaciaPorEvidencia
        fields = [
            'tipo_eficacia',
            'participantes_com_beneficio',
            'participantes_iniciaram_tratamento',
            'percentual_eficacia_calculado',
            'nome_tratamento',
        ]


class EvidenciasClinicasSerializer(serializers.ModelSerializer):
    condicao_saude = CondicaoSaudeSerializer(read_only=True)

    class Meta:
        model = EvidenciasClinicas
        fields = '__all__'


class AvaliacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Avaliacao
        fields = '__all__'


class DetalhesTratamentoResumoSerializer(serializers.ModelSerializer):
    condicao_saude = CondicaoSaudeSerializer(read_only=True)
    tipo_tratamento = TipoTratamentoSerializer(many=True, read_only=True)
    contraindicacoes = ContraindicacaoSerializer(many=True, read_only=True)
    reacoes_adversas = ReacaoAdversaSerializer(many=True, read_only=True)
    evidencias = EvidenciasClinicasSerializer(many=True, read_only=True)
    avaliacoes = AvaliacaoSerializer(many=True, read_only=True)
    tipos_eficacia = EficaciaPorEvidenciaSerializer(many=True, read_only=True)

    prazo_efeito_min_formatado = serializers.ReadOnlyField()
    prazo_efeito_max_formatado = serializers.ReadOnlyField()
    prazo_efeito_faixa_formatada = serializers.ReadOnlyField()

    class Meta:
        model = DetalhesTratamentoResumo
        fields = '__all__'

# -------------------------
# Serializers "lean" (tela Controle)
# -------------------------

class ContraindicacaoLeanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contraindicacao
        fields = ["nome"]

class TipoTratamentoLeanSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoTratamento
        fields = ["nome"]

class DetalhesTratamentoResumoTelaControleSerializer(serializers.ModelSerializer):
    tipo_tratamento = TipoTratamentoLeanSerializer(many=True, read_only=True)
    contraindicacoes = ContraindicacaoLeanSerializer(many=True, read_only=True)

    prazo_efeito_min_formatado = serializers.ReadOnlyField()
    prazo_efeito_max_formatado = serializers.ReadOnlyField()
    prazo_medio_minutos = serializers.ReadOnlyField()

    descricao_lista = serializers.SerializerMethodField()

    class Meta:
        model = DetalhesTratamentoResumo
        fields = [
            "id", "slug", "imagem", "nome", "descricao", "descricao_lista",
            "principio_ativo", "fabricante",
            "tipo_tratamento",
            "custo_medicamento",
            "prazo_medio_minutos",
            "prazo_efeito_min_formatado",
            "prazo_efeito_max_formatado",
            "prazo_efeito_unidade",
            "prazo_efeito_min",
            "prazo_efeito_max",
            "contraindicacoes",
            "indicado_criancas",
            "indicado_adolescentes",
            "indicado_adultos",
            "indicado_idosos",
            "indicado_lactantes",
            "indicado_gravidez",
            "condicoes_saude",
        ]

    def get_descricao_lista(self, obj):
        request = self.context.get("request")
        condicao_slug = None

        if request:
            condicao_slug = (request.query_params.get("condicao_slug") or "").strip()

        descricao_condicao = None

        if condicao_slug:
            descricao_condicao = (
                obj.condicoes_relacionadas
                .filter(condicao__slug=condicao_slug)
                .values_list("descricao", flat=True)
                .first()
            )

        if not descricao_condicao and condicao_slug:
            descricao_condicao = (
                obj.condicoes_relacionadas
                .filter(condicao__condition_slug=condicao_slug)
                .values_list("descricao", flat=True)
                .first()
            )

        if not descricao_condicao and request:
            nome_condicao = (
                obj.condicoes_saude
                .filter(slug=condicao_slug)
                .values_list("nome", flat=True)
                .first()
            )
            if nome_condicao:
                descricao_condicao = (
                    obj.condicoes_relacionadas
                    .filter(condicao__nome=nome_condicao)
                    .values_list("descricao", flat=True)
                    .first()
                )

        return descricao_condicao or obj.descricao

class TipoEficaciaDinamicoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoEficacia
        fields = ['id', 'tipo_eficacia', 'descricao', 'imagem']


class EficaciaPorEvidenciaDinamicaSerializer(serializers.ModelSerializer):
    tipo_eficacia = TipoEficaciaDinamicoSerializer(read_only=True)
    percentual_eficacia_calculado = serializers.ReadOnlyField()
    nome_tratamento = serializers.CharField(source='evidencia.tratamento.nome', read_only=True)
    tratamento_id = serializers.IntegerField(source='evidencia.tratamento.id', read_only=True)
    tratamento_slug = serializers.CharField(source='evidencia.tratamento.slug', read_only=True)

    class Meta:
        model = EficaciaPorEvidencia
        fields = [
            'tipo_eficacia',
            'participantes_com_beneficio',
            'participantes_iniciaram_tratamento',
            'percentual_eficacia_calculado',
            'nome_tratamento',
            'tratamento_id',
            'tratamento_slug',
        ]

class PaginaListaTratamentoFooterSerializer(serializers.Serializer):
    label = serializers.CharField()
    url = serializers.CharField()



class TreatmentsUSADynamicSerializer(serializers.ModelSerializer):
    treatment_type = TipoTratamentoLeanSerializer(many=True, read_only=True)
    contraindications = ContraindicacaoLeanSerializer(many=True, read_only=True)
    description_for_list = serializers.SerializerMethodField()

    class Meta:
        model = TreatmentsUSA
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "description_for_list",
            "category",
            "active_ingredient",
            "manufacturer",
            "image",
            "treatment_cost",
            "effect_time_min",
            "effect_time_max",
            "effect_time_unit",
            "risk",
            "group",
            "indicated_children",
            "indicated_teenagers",
            "indicated_adults",
            "indicated_elderly",
            "indicated_lactating",
            "indicated_pregnancy",
            "treatment_type",
            "contraindications",
        ]

    def get_description_for_list(self, obj):
        request = self.context.get("request")
        condition_slug = ""

        if request:
            condition_slug = (request.query_params.get("condition_slug") or "").strip()

        if condition_slug:
            description = (
                obj.condition_relations
                .filter(
                    condition__condition_slug=condition_slug,
                    appear_on_list=True,
                )
                .values_list("description", flat=True)
                .first()
            )

            if description:
                return description

        return obj.description


class EnglishEfficacyDynamicSerializer(serializers.ModelSerializer):
    treatment_id = serializers.SerializerMethodField()
    treatment_slug = serializers.SerializerMethodField()
    treatment_name = serializers.SerializerMethodField()
    efficacy_type = TipoEficaciaDinamicoSerializer(source="tipo_eficacia", read_only=True)
    efficacy_value = serializers.ReadOnlyField(source="percentual_eficacia_calculado")

    class Meta:
        model = EficaciaPorEvidencia
        fields = [
            "efficacy_type",
            "participantes_com_beneficio",
            "participantes_iniciaram_tratamento",
            "efficacy_value",
            "percentual_eficacia_calculado",
            "treatment_id",
            "treatment_slug",
            "treatment_name",
        ]

    def _get_english_treatment(self, obj):
        tratamento_br = getattr(obj.evidencia, "tratamento", None)

        if not tratamento_br:
            return None

        treatment = (
            TreatmentsUSA.objects
            .filter(tratamento_br=tratamento_br)
            .first()
        )

        if treatment:
            return treatment

        return (
            TreatmentsUSA.objects
            .filter(name__iexact=tratamento_br.nome)
            .first()
        )

    def get_treatment_id(self, obj):
        treatment = self._get_english_treatment(obj)
        return treatment.id if treatment else None

    def get_treatment_slug(self, obj):
        treatment = self._get_english_treatment(obj)
        return treatment.slug if treatment else ""

    def get_treatment_name(self, obj):
        treatment = self._get_english_treatment(obj)
        return treatment.name if treatment else ""