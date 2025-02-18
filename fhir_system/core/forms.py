from django import forms
from django.contrib.auth.models import User

class UserRegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    password_confirm = forms.CharField(widget=forms.PasswordInput, label="Confirme sua senha")

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', "As senhas não coincidem")

        return cleaned_data


from django import forms

class TratamentoSearchForm(forms.Form):
    nome = forms.CharField(label='Nome', max_length=100, required=False)
    categoria = forms.CharField(label='Categoria', max_length=100, required=False)


from django import forms
from .models import EvidenciasClinicas

class EvidenciasClinicasForm(forms.ModelForm):
    class Meta:
        model = EvidenciasClinicas
        fields = '__all__'  # Garante que o novo campo seja incluído no formulário
