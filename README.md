<p align="center">
  <img src="accb/static/img/accb.png" alt="Logo ACCB" width="100"/>
</span>
<h1 align="center">ACCB Price Miner</h1>

O ACCB Price Miner, desenvolvido por [Samuel
Vasconcelos](https://github.com/smvasconcelos/) como Projeto de
Iniciação Tecnológica, é um software que busca automatizar a coleta de
preços de produtos na Bahia, utilizando-se de dados da plataforma Preço
da Hora.

Esta versão é uma melhora da [versão
original](https://github.com/smvasconcelos/ACCB_IT) feita por
[Yohanan](https://github.com/yohannd1/) como Projeto de Extensão,
buscando manutenir o projeto e melhorá-lo em alguns aspectos.

A página oficial do projeto está disponível no [site da IM&A da
UESC](https://ima.uesc.br/accb_price_miner/).

**Plataformas suportadas**: Windows 10+, Linux

## Preparação

Clone o repositório:

```sh
git clone https://github.com/yohannd1/accb-price-miner/ --depth 1
```

TODO: especificar a branch aqui! a não ser que a main tenha se tornado a
oficial já.

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
pyinstaller app.spec
```

Nota: o executável criado para windows usa `uac_admin=True`, que faz o
executável precisar de persmissão de administrador. Isso foi feito
porque, por algum motivo, abrir o diálogo de arquivo pelo Tkinter estava
pedindo permissão de administrador. :(

## Ferramentas de desenvolvimento

Esse projeto usa `black` para formatar o código (`pip install black`):

```sh
black .
```

É possível também verificar a corretude de tipos do código (até certo
ponto) usando `mypy` (`pip install mypy`):

```sh
mypy app.py --ignore-missing-imports
```

Para gerar a documentação do programa usando `pdoc` (`pip install
pdoc`):

```sh
pdoc -o doc accb
```
