<!-- PROJECT LOGO -->
<br />
<p align="center">
  <a href="https://github.com/smvasconcelos/ACCB_IT/tree/Executavel">
    <!-- <img src="./img/logo_2.png" alt="Logo" width="100"> -->
	<h3 align="center">Projeto ACCB - Guia de Funcionalidades</h3>
  </a>
</p>


<!-- TABLE OF CONTENTS -->
<details open="open">
  <summary>Opções</summary>
  <ol>
    <li>
        <a href="#definição">Definição</a><br>
    </li>
	<li>
        <a href="#tratar-pesquisas">Tratar Pesquisas</a><br>
	</li>
	<li>
        <a href="#tratar-pesquisas-todos">Tratar Pesquisas Todos</a><br>
	</li>
  </ol>
</details>

## Definição

Dado uma estrutura :

```
-- ACCB.exe
-- Itabuna [25-06-2021]
-- Itabuna [25-06-2021]
-- Itabuna [25-06-2021]
-- Ilhéus [25-06-2021]
-- Ilhéus [25-06-2021]
-- Ilhéus [25-06-2021]
-- Ilhéus [25-06-2021]
```

o programa itera por cada pasta de pesquisa e retorna 2 pastas com 3 subdiretórios cada em cada pasta de sua respectiva cidade.

```
-- ACCB.exe
...
-- Coleta Datada
   --Itabuna
		-- Coleta Padrão
		-- Coleta Arquivo TODOS
		-- Coleta Extra
   --Ilhéus
		-- Coleta Padrão
		-- Coleta Arquivo TODOS
		-- Coleta Extra
-- Coleta Concatenada
   --Itabuna
		-- Coleta Padrão
		-- Coleta Arquivo TODOS
		-- Coleta Extra
   --Ilhéus
		-- Coleta Padrão
		-- Coleta Arquivo TODOS
		-- Coleta Extra
```
	-- Coleta Datada -> Retorna todas as coletas de cada pasta concatenadas em um unico arquivo do seu respectivo estabelecimento em que cada 'sheet' (planilha) é a data da coleta.
	-- Coleta Concatenada -> Concatena todas as coletas do resultado anterior (Coleta Datada) em um arquivo do seu respectivo estabelecimento, com uma unica 'sheet' (panilha) e todas as duplicações de valores existentes em cada data.

## Tratar Pesquisas
```
O comando Tratar Pesquisas faz todo esse processo com os arquivos da pesquisa padrão e os coloca na pasta Coleta Padrão, ou seja, todos os arquivos que não tem Todos no nome.
```
## Tratar Pesquisas Todos
```
O comando Tratar Pesquisas Todos, faz a mesma coisa que a de cima, porém ele faz a pesquisa no arquivo Todos daquela data, colocando os resultados da pesquisa Padrão em Aquivo na pasta Coleta Arquivo TODOS e também pesquisa cada estabelecimento único que aparece no arquivo TODOS daquela data, ou seja, qualquer estabelecimento que não pertence a pesquisa oficial é colocado na Coleta Extra, com o nome do seu estabelecimento no mesmo padrão que as demais.
```

## Contribuidores

- [Samuel Mendonça](https://github.com/smvasconcelos)
