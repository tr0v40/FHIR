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
)


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
        fields = '__all__'


class EficaciaPorEvidenciaSerializer(serializers.ModelSerializer):
    tipo_eficacia = TipoEficaciaSerializer(read_only=True)
    percentual_eficacia_calculado = serializers.FloatField(read_only=True)

    class Meta:
        model = EficaciaPorEvidencia
        fields = '__all__'


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

    # se quiser expor os prazos já formatados:
    prazo_efeito_min_formatado = serializers.ReadOnlyField()
    prazo_efeito_max_formatado = serializers.ReadOnlyField()
    prazo_efeito_faixa_formatada = serializers.ReadOnlyField()

    class Meta:
        model = DetalhesTratamentoResumo
        fields = '__all__'
