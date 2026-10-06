from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import LoginSecurity
from django_select2.forms import Select2MultipleWidget
from django import forms
from .models import TreatmentListUrlEnglish, TipoEficacia, TreatmentsUSA


from .models import (
    Avaliacao,
    CondicaoSaude,
    DetalhesTratamentoResumo,
    EvidenciasClinicas,
    Pais,
    TratamentoCondicao,
)

class CustomAuthenticationForm(AuthenticationForm):

    MAX_FAILED_ATTEMPTS = 3

    def confirm_login_allowed(self, user):
        """
        Mantém todas as validações padrão do Django.
        """
        super().confirm_login_allowed(user)

    def get_invalid_login_error(self):
        """
        Retorna uma mensagem de erro de acordo com
        o estado atual de segurança da conta.
        """

        username = self.data.get("username", "").strip()

        # Não informa se um usuário existe ou não.
        if not username:
            return forms.ValidationError(
                "Usuário ou senha inválidos.",
                code="invalid_login",
            )

        UserModel = get_user_model()

        try:
            user = UserModel._default_manager.get(
                **{
                    UserModel.USERNAME_FIELD: username
                }
            )

        except UserModel.DoesNotExist:
            return forms.ValidationError(
                "Usuário ou senha inválidos.",
                code="invalid_login",
            )

        security, _ = LoginSecurity.objects.get_or_create(
            user=user
        )

        now = timezone.now()

        # =====================================================
        # BLOQUEIO ATIVO
        # =====================================================

        if (
            security.locked_until
            and security.locked_until > now
        ):
            return forms.ValidationError(
                (
                    "Acesso temporariamente bloqueado após "
                    "3 tentativas inválidas. "
                    "Tente novamente em 30 minutos."
                ),
                code="account_locked",
            )

        # =====================================================
        # BLOQUEIO EXPIRADO
        # =====================================================

        if (
            security.locked_until
            and security.locked_until <= now
        ):
            security.failed_attempts = 0
            security.locked_until = None

            security.save(
                update_fields=[
                    "failed_attempts",
                    "locked_until",
                ]
            )

        # =====================================================
        # TENTATIVAS RESTANTES
        # =====================================================

        failed_attempts = security.failed_attempts or 0

        remaining = max(
            0,
            self.MAX_FAILED_ATTEMPTS - failed_attempts
        )

        if remaining == 2:
            message = (
                "Usuário ou senha inválidos. "
                "Restam 2 tentativas."
            )

        elif remaining == 1:
            message = (
                "Usuário ou senha inválidos. "
                "Resta 1 tentativa."
            )

        elif remaining <= 0:
            message = (
                "Acesso temporariamente bloqueado após "
                "3 tentativas inválidas. "
                "Tente novamente em 30 minutos."
            )

        else:
            message = "Usuário ou senha inválidos."

        return forms.ValidationError(
            message,
            code="invalid_login",
        )

class UserRegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    password_confirm = forms.CharField(
        widget=forms.PasswordInput,
        label="Confirme sua senha"
    )

    class Meta:
        model = User
        fields = ["username", "email", "password"]

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password and password_confirm and password != password_confirm:
            self.add_error("password_confirm", "As senhas não coincidem")

        return cleaned_data


class TratamentoSearchForm(forms.Form):
    nome = forms.CharField(label="Nome", max_length=100, required=False)
    categoria = forms.CharField(label="Categoria", max_length=100, required=False)


class DetalhesTratamentoResumoForm(forms.ModelForm):
    condicao_saude = forms.ModelMultipleChoiceField(
        queryset=CondicaoSaude.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Condições de Saúde"
    )

    class Meta:
        model = DetalhesTratamentoResumo
        fields = ["nome", "prazo_efeito_min", "prazo_efeito_max", "condicao_saude"]


class ComentarioForm(forms.ModelForm):
    usuario_nome = forms.CharField(
        max_length=255,
        required=True,
        label="Nome Completo",
        widget=forms.TextInput(attrs={"placeholder": "Digite seu nome"})
    )
    comentario = forms.CharField(
        widget=forms.Textarea,
        required=True,
        label="Comentário"
    )

    class Meta:
        model = Avaliacao
        fields = ["usuario_nome", "comentario"]


class EvidenciasClinicasForm(forms.ModelForm):
    pais = forms.ModelMultipleChoiceField(
        queryset=Pais.objects.all(),
        widget=Select2MultipleWidget(),
        required=False
    )

    class Meta:
        model = EvidenciasClinicas
        fields = ["titulo", "descricao", "paises"]


class TratamentoCondicaoInlineForm(forms.ModelForm):
    class Meta:
        model = TratamentoCondicao
        fields = ("condicao", "descricao")

    def clean(self):
        cleaned_data = super().clean()
        condicao = cleaned_data.get("condicao")
        descricao = cleaned_data.get("descricao")

        if condicao and not descricao:
            self.add_error("descricao", "Preencha a descrição da condição.")

        return cleaned_data

from django import forms
from .models import TreatmentListUrlEnglish, TipoEficacia, CondicaoSaude

class TreatmentListUrlEnglishForm(forms.ModelForm):
    health_condition = forms.ModelChoiceField(
        queryset=CondicaoSaude.objects.all().order_by("nome"),
        required=True,
        label="Health condition"
    )

    efficacy_type = forms.ModelChoiceField(
        queryset=TipoEficacia.objects.all().order_by("tipo_eficacia"),
        required=False,
        label="Efficacy type"
    )

    class Meta:
        model = TreatmentListUrlEnglish
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["health_condition"].label_from_instance = (
            lambda obj: obj.condition if getattr(obj, "condition", "") else obj.nome
        )

        self.fields["efficacy_type"].label_from_instance = (
            lambda obj: obj.outcome_type if obj.outcome_type else obj.tipo_eficacia
        )

class TreatmentsUSAForm(forms.ModelForm):
    health_conditions = forms.ModelMultipleChoiceField(
        queryset=CondicaoSaude.objects.all().order_by("nome"),
        required=False,
        label="Health conditions"
    )

    class Meta:
        model = TreatmentsUSA
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["health_conditions"].label_from_instance = (
            lambda obj: obj.condition or obj.nome
        )

from .models import TreatmentUrlEnglish, CondicaoSaude, TreatmentsUSA

class TreatmentUrlEnglishForm(forms.ModelForm):
    condition = forms.ModelChoiceField(
        queryset=CondicaoSaude.objects.all().order_by("condition", "nome"),
        required=True,
        label="Condition"
    )

    treatment = forms.ModelChoiceField(
        queryset=TreatmentsUSA.objects.all().order_by("name"),
        required=True,
        label="Treatment"
    )

    class Meta:
        model = TreatmentUrlEnglish
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["condition"].label_from_instance = (
            lambda obj: obj.condition if getattr(obj, "condition", "") else obj.nome
        )

        self.fields["treatment"].label_from_instance = (
            lambda obj: obj.name if getattr(obj, "name", "") else str(obj)
        )