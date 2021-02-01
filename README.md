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
    <!-- <a href="https://adrielfabricio.github.io/coffee-chat/"><strong>Documentação do código do projeto</strong></a> -->
  </p>
</p>


<!-- TABLE OF CONTENTS -->
<details open="open">
  <summary>Sumário</summary>
  <ol>
    <li>
        <a href="#sobre-o-projeto">Sobre o projeto</a>
    </li>
	<li> <a href="#solução"> Solução </a> </li>
	<li> <a href="#utilizando"> Utilizando </a> </li>
  </ol>
</details>

## Sobre o projeto

O projeto tem como objetivo encontrar soluções tecnológicas para auxiliar no processo de coleta da cesta básica da UESC (ACCB).

## Solução

A partir de uma ferramenta web externa foi realizada uma pesquisa apra a possibilidade de extrar informações de tal site. Vendo a possibilidade foi criado um scrapper e a partir dele foi feita uma GUI para facilitar o uso pelos os usuários.


## Executavel

Em um terminal execute o seguinte comando :

pyinstaller --onefile --paths="C:\Users\samue\AppData\Local\Programs\Python\Python37-32\Lib\site-packages\win10toast" --paths="C:\Users\samue\AppData\Local\Programs\Python\Python37-32\Lib\site-packages\xlsxwriter"  —name="ACCB"  --icon=logo.ico  screen.py

## Utilizando

 1. Selecione o município 
 2. Selecione os estabelecimentos
 3. Caso o CAPTCHA seja ativado, abra seu navegador no link : www.precodahora.ba.gov.br/produtos/ e solucione o captcha e pressione SIM
 4. FIM

## Requisitos

Deve existir uma copia do navegador chrome instalado na maquina que deseja abrir o programa. (Windows 10)

Link para download: https://www.google.com/intl/pt-BR/chrome/

## Contribuidores

- [Samuel Mendonça](https://github.com/Syphoon)
