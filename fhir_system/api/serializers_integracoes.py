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


class IntegracaoDetalhesTratamentoListSerializer(serializers.ModelSerializer):
    """
    Serializer leve para listagem de tratamentos.

    Usado apenas no GET /api/integracoes/tratamentos/
    para evitar carregar todos os campos pesados da tabela.
    """

    class Meta:
        model = DetalhesTratamentoResumo
        fields = [
            "id",
            "nome",
            "fabricante",
            "principio_ativo",
            "categoria_regulatoria",
            "tipo_prescricao",
            "descricao",
            "quando_usar",
            "custo_medicamento",
            "alertas",
        ]
        read_only_fields = ["id"]


class IntegracaoDetalhesTratamentoSerializer(serializers.ModelSerializer):
    """
    Serializer completo para detalhe, criação e edição de tratamentos.

    Usado em:
    GET /api/integracoes/tratamentos/<id>/
    POST /api/integracoes/tratamentos/
    PUT /api/integracoes/tratamentos/<id>/
    PATCH /api/integracoes/tratamentos/<id>/
    """

    class Meta:
        model = DetalhesTratamentoResumo
        fields = "__all__"
        read_only_fields = ["id"]


class IntegracaoCondicaoSaudeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CondicaoSaude
        fields = "__all__"
        read_only_fields = ["id"]


class IntegracaoReacaoAdversaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReacaoAdversa
        fields = "__all__"
        read_only_fields = ["id"]


class IntegracaoContraindicacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contraindicacao
        fields = "__all__"
        read_only_fields = ["id"]


class IntegracaoTipoTratamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoTratamento
        fields = "__all__"
        read_only_fields = ["id"]


class IntegracaoEvidenciasClinicasSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvidenciasClinicas
        fields = "__all__"
        read_only_fields = ["id"]


class IntegracaoAvaliacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Avaliacao
        fields = "__all__"
        read_only_fields = ["id"]


class IntegracaoEficaciaPorEvidenciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = EficaciaPorEvidencia
        fields = "__all__"
        read_only_fields = ["id"]


class IntegracaoTipoEficaciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoEficacia
        fields = "__all__"
        read_only_fields = ["id"]


class IntegracaoDetalhesTratamentoReacaoAdversaSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetalhesTratamentoReacaoAdversa
        fields = "__all__"
        read_only_fields = ["id"]


class IntegracaoTreatmentsUSASerializer(serializers.ModelSerializer):
    class Meta:
        model = TreatmentsUSA
        fields = "__all__"
        read_only_fields = ["id"]