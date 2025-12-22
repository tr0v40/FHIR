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
    
)

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
    percentual_eficacia_calculado = serializers.ReadOnlyField()  # Usando ReadOnlyField para acessar a propriedade
    nome_tratamento = serializers.CharField(source='evidencia.tratamento.nome', read_only=True)  # Nome do tratamento

    class Meta:
        model = EficaciaPorEvidencia
        fields = ['tipo_eficacia', 'participantes_com_beneficio', 'participantes_iniciaram_tratamento', 'percentual_eficacia_calculado', 'nome_tratamento']




class EvidenciasClinicasSerializer(serializers.ModelSerializer):
    condicao_saude = CondicaoSaudeSerializer(read_only=True)
    eficacia_por_evidencia = EficaciaPorEvidenciaSerializer(many=True, read_only=True)

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

