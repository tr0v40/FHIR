import requests
from bs4 import BeautifulSoup

def buscar_imagem_google(medicamento):
    """ Busca a primeira imagem do Google Imagens para o medicamento. """
    url = f"https://www.google.com/search?tbm=isch&q={medicamento.replace(' ', '+')}"
    headers = {"User-Agent": "Mozilla/5.0"}

    # Faz a requisição ao Google
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    # Encontra as imagens nos resultados
    imagens = soup.find_all("img")
    if len(imagens) > 1:
        return imagens[1]["src"]  # A primeira imagem costuma ser do Google
    return None
 