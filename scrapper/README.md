<!-- PROJECT LOGO -->
<br />
<p align="center">
  <a href="https://github.com/Syphoon/ACCB_IT/tree/GUI">
    <!-- <img src="./img/logo_2.png" alt="Logo" width="100"> -->
	<h3 align="center">Projeto ACCB - GUI</h3>
  </a>
  <p align="center">
    Projeto desenvolvido para o projeto de iniciação tecnológica
    <br />
    <!-- <a href="https://syphoon.github.io/ACCB_IT/tree/GUI"><strong>Documentação do código do projeto</strong></a> -->
  </p>
</p>

## Informações de Desenvolvimento

Para rodar o projeto preferencialmente inicie um ambiente virtual com :

```
	pip install virtualenv
	python -m venv <nome>

```

Em seguida abra a pasta do ambiente e clone o repositório em questão com :

```
	cd <nome>
	git clone https://github.com/smvasconcelos/ACCB_IT.git --single-branch --branch desktop-web
```

E por último inicie o ambiente virtual e instale as dependências do python para iniciar o projeto :

```
	cd Scripts
	activate.bat
	cd ..
	pip install -r requirements.txt

```

Agora é só rodar o projeto com python -m flask run ou python app.py.

## Observações

Para que seja possível gerar um exe sem uma janela de console do windows é necessário alterar um arquivo fonte do selenium, este que se encontra em :

```
	\Lib\site-packages\selenium\webdriver\common\service.py
	Altere então :
	self.process = subprocess.Popen(cmd, env=self.env, close_fds=platform.system() != 'Windows', stdout=self.log_file, stderr=self.log_file, stdin=PIPE)
	para :
	self.process = subprocess.Popen(cmd, stdin=PIPE, stdout=PIPE ,stderr=PIPE, shell=False, creationflags=0x08000000)
```

E em seguida é só executar o comando pyinstaller app.spec.
