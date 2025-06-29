from django import template

register = template.Library()

@register.filter(name='replace_dot_with_comma')
def replace_dot_with_comma(value):
    """
    Substitui o ponto (.) por vírgula (,) em números decimais
    """
    try:
        # Verifica se o valor é um número float e converte para string
        return str(value).replace('.', ',')
    except:
        return value  # Retorna o valor original caso haja erro
