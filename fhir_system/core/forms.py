from django import forms
from django.contrib.auth.models import User
from .models import EvidenciasClinicas
from .models import DetalhesTratamentoResumo, CondicaoSaude
from django import forms
from .models import Avaliacao

class UserRegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    password_confirm = forms.CharField(
        widget=forms.PasswordInput, label="Confirme sua senha"
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


class EvidenciasClinicasForm(forms.ModelForm):
    class Meta:
        model = EvidenciasClinicas
        fields = "__all__"




class DetalhesTratamentoResumoForm(forms.ModelForm):
    condicao_saude = forms.ModelMultipleChoiceField(
        queryset=CondicaoSaude.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Condições de Saúde"
    )

    class Meta:
        model = DetalhesTratamentoResumo
        fields = ['nome', 'prazo_efeito_min', 'prazo_efeito_max', 'condicao_saude']


        

class ComentarioForm(forms.ModelForm):
    class Meta:
        model = Avaliacao
        fields = ['usuario_nome', 'comentario']

    usuario_nome = forms.CharField(max_length=255, required=True, label='Nome Completo', widget=forms.TextInput(attrs={'placeholder': 'Digite seu nome'}))
    comentario = forms.CharField(widget=forms.Textarea, required=True, label='Comentário')


from django import forms
from django_select2.forms import Select2MultipleWidget
from .models import EvidenciasClinicas, Pais

class EvidenciasClinicasForm(forms.ModelForm):
    pais = forms.ModelMultipleChoiceField(
        queryset=Pais.objects.all(),  # Garante que estamos carregando os países do banco de dados
        widget=Select2MultipleWidget(),  # Usando o widget Select2 para uma boa interface
        required=False  # Não torna o campo obrigatório
    )

    class Meta:
        model = EvidenciasClinicas
        fields = ['titulo', 'descricao', 'paises']  # Incluindo o campo pais
