<p align="center">
  <img src="accb/static/img/accb.png" alt="Logo ACCB" width="100"/>
</span>
<h1 align="center">ACCB Price Miner</h1>

O ACCB Price Miner, desenvolvido por [Samuel
Vasconcelos](https://github.com/smvasconcelos/) como Projeto de
Iniciação Tecnológica, é um software que busca automatizar a coleta de
preços de produtos na Bahia, pela plataforma [Preço da Hora
(BA)](https://precodahora.ba.gov.br/).

Esta versão é uma melhora, feita por
[Yohanan](https://github.com/yohannd1/), da [versão original de
Samuel](https://github.com/smvasconcelos/ACCB_IT), feita sob um Projeto
de Extensão com o objetivo de manutenir o sistema e melhorá-lo em alguns
aspectos.

A página oficial do projeto está disponível no [site da IM&A da
UESC](https://ima.uesc.br/accb_price_miner/).

**Plataformas suportadas**: Windows 10+, Linux

## Preparação

Clone o repositório:

```sh
git clone https://github.com/yohannd1/accb-price-miner/ --depth 1
```

Crie um ambiente virtual usando o `venv` e o ative:

```sh
# em linux e windows
python -m venv venv

# em linux
source venv/bin/activate

# em windows (batch)
venv\Scripts\activate.bat

# em windows (PowerShell)
Set-ExecutionPolicy Unrestricted -Scope Process
venv\Scripts\activate.ps1
```

**Daqui para frente, é subentendido que os comandos do python
relacionados ao ambiente virtual estão acessíveis diretamente**. Caso
algum comando não esteja disponível, verifique se ele está acessível em
`venv/bin/nome_comando` (ou `venv/Scripts/nome_comando` no Windows).

Se você estiver usando Windows, certifique-se que está com Windows 10+ e
tem um compilador de C++ instalado disponível em seu ambiente.

Caso queira usar MinGW, [veja a seção sobre cygwin/mingw da documentação
do
pyinstaller](https://pyinstaller.readthedocs.io/en/stable/bootloader-building.html#build-using-cygwin-and-mingw).

## Testes e compilação

Instale o pacote do `accb-price-miner` no ambiente virtual (isso só
precisa ser feito na primeira vez):

```sh
pip install -e .
```

Para rodar o aplicativo (debug):

```sh
python accb/__main__.py
```

Para criar um executável (usando PyInstaller, `pip install pyinstaller`):

```sh
pyinstaller accb.spec
```

## Localização dos dados

Este programa pode criar alguns arquivos:

- `./accb.sqlite`: banco de dados do programa (com dados de pesquisa e
    opções)

- `./accb.log`: log do programa (quando debug está desativado)

Além disso, o usuário escolhe uma pasta em seu sistema para colocar os
dados exportados.

## Ferramentas de desenvolvimento

Esse projeto usa `black` para formatar o código (`pip install black`):

```sh
black .
```

É possível também verificar a corretude de tipos do código (até certo
ponto) usando `mypy` (`pip install mypy`):

```sh
mypy accb/__main__.py --ignore-missing-imports
```

Para gerar a documentação do programa usando `pdoc` (`pip install
pdoc`):

```sh
pdoc -o doc accb
```
