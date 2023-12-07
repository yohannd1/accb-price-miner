# 1 - Titulo

Gostária de agradecer a presenca de todos que estão aqui hoje. Hoje venho apresentar o projeto desenvolvido como trabalho de conclusão de curso, entitulado ACCB Price Miner.
Que é uma aplicacão de mineracão de dados semi automatica para auxiliar no projeto ACCB aqui da UESC.


# 2 - Organizacão

Esta apresentação irá seguir a seguinte organização, na introdução irei abordar a metodologia do projeto accb e a problemática à ser implementada. No desenvolvimento vou descrever nossos objetivos e suas dificuldades, e também as ferramentas utilizadas. Em seguida irei falar dos resultados do projeto e discussões a respeito.

# 3 - Introducão

- vazio

# 4 - O projeto ACCB É ?

O custo da cesta básica é um componente no cálculo do salário mínimo instituído em 1938 por decreto (Brasil 1938) e utilizado até o momento. A finalidade do projeto de extensão ACCB é acompanhar, mensalmente, a evolução dos preços dos 12 produtos de alimentação da cesta básica para os municípios de Ilhéus e Itabuna, ambos localizados no estado da Bahia, bem como o gasto mensal e o tempo de trabalho necessário despendido por um trabalhador para adquiri-los. A coleta dos dados era feita inicialmente nas prateleiras dos estabelecimentos por responsáveis ( estagiarios ) de acordo com um cronograma gerado anualmente.

# 5 - Metodologia

Expandindo mais sobre a metodologia do projeto ACCB e como ele surgiu. Temos que a plataforma web surgiu em meados de 2004, essa que auxilia o projeto ACCB. Posteriormente utilizavam só planilhas na mão. Durante esse periodo seguia-se então o seguinte fluxo disposto no fluxo abaixo. É realizado a coleta nos supermercados pelos estagiários  e anotado em planilhas para que em um outro momento seja então registrado através de formulários digitais no banco de dados ACCB.
Esse processo pode ser passível de errro devido à não só o intervalo entre os processos que o dado pode se perder, mas também é passível a erros de digitacão.

# 6 - Metodologia - Pandemia

  Como sabemos, muitas areas e pessoal foram afetadas pela pandemia de 2020, o mesmo aconteceu com o processo de coleta do projeto ACCB visto que eles necessitavam de presenca fisica nos estabelecimentos para realizar as coletas. Com esse problema em mente a equipe procurou formas de realiazr essa coleta pela internet, durante essas buscas eles encontraram a plataforma do preco da hora bahia. Este que detem de um acervo atualizado de notas fiscais geradas por estabelcimentos de todo o estado da bahia, possibilitando assim a coleta de precos de forma digital. Isso altera o fluxo para o que podemos ver no fluxo atualizado abaixo. Agora os estagiarios pesquisam no site do preco da hora e prosseguem com os outros processos como era antigamente.

# 7 - O problema

Com esse cenário em mente tivemos a seguinte problematica para resolver. O site nem sempre mostra todos os resultados possíveis, uma vez que as notas fiscais são geradas em tempo real, atualizando a cada 72 horas. O tempo de pesquisa acaba ficando cansativo uma vez que é necessário varias coletas para encontrar todos os produtos. E é necessário atencão continua dos estágiarios para anotar nas planilhas e digitar todos os produtos e precos. Temos um processo de coleta digital que potencialmente pode ser traduzido em funcionalidades de um software.

# 8 - Objetivos

Então com essas informacões podemos formalizar o nosso objetivo geral, que é automatizar o processo de pesquisa no site Preço da Hora BA, eliminando a fase de anotação e melhorar o tempo de pesquisa.

# 9 - Objetivos especificos

Destrichando mais esse objetivo temos então alguns objetivos especificos.

Sendo eles em ordem:

Desenvolver um software desktop para coletar os dados na plataforma do preco da hora bahia
Criar materiais de apoio para o treinamento da equipe
Gerar relatórios em forma de planilha mantendo a familiaridade nos relatórios já utilizados
E por fim permitir o cadastro de produtos e estabelecimentos que vão ser pesquisados.


# 10 - Desenvolvimento

Com todos os objetivos em mente e finalizados, podemos partir para o desenvolvimento da aplicacão em si e o seu planejamento.

-- Vazio

# 11 - Requisitos principais

Para realizar o desenvolvimento da aplicacão realizamos um levantamento de requisitos para mapear toda a metodologia que seria necessário para implementar o sistema.

E para que isso fosse feito é necessário primeiro conhecer o metodo de coleta dos estagiários na plataforma do preco da hora bahia.
Em seguida precisamos transformar esse fluxo em um script automatizado de coleta.
E para facilitar a utilizacão precisamos garantir que a interface do sistema é facil e intuitiva de utilizar.
Esses dados vão precisar ser armazenados localmente para tratamento e futuro acesso.
Como podemos resolver o problema do reCaptcha e como formatar arquivos excel são problema que tivemos que resolver ao longo do projeto.

# 12 - Ferramentas

Depois de realizar esse mapeamento pesquisamos então as ferramentas que melhor se encaixavam para implementar os requisitos e que mais se encaixavam com o meu perfil de desenvolvedor.

Acabamos então escolhendo para o backend e scrapping o python, por conta da facilidade de implementacão e familiaridade de utilizacão de ferramentas.
Optamos também posteriormente pela triade web para implementar a interface do sistema.
E por fim um dos pacotes que permitiu o controle de rotas do backend e comunicacão socket o Flask.

# 13 - Metodologia

Com os requisitos e ferramentas definidos precisamos então definir a metodologia de desenvolvimento do sistema. Primeiro vamos comecar realizando o levantamento de requisitos do sistema, seguindo da analise continua de ferramentas e plataforma.
Partindo então para o mockup do sistema e prototipacão. Realiazndo por fim os testes e ajustes produzindo então a versão final.

# 14 - Dificuldades

Durante o desenvolvimento tivemos algumas dificuldades, sendo a principal delas o recaptcha que é um mecanismo de defesea contra programas automaizados maliciosos que buscam prejudicar o sistema. Para solucionar esse problema, optamos em emitir um alerta para o usuário resolver o captcha enquanto a pesquisa fica parada esperando um retorno.

O processo de simular a coleta em si, foi algo que deu um pouco de trabalho devido a natureza do script.

Limitacõies da plataforma como manutencão.

Gerar um arquivo executável para testes com a nova versão web se demonstrou bem complexo e desafiador devido a forma de empacotamento do pacote uitilziado.

# 15 - Resultados

Nessas sessões vamos falar sobre os resultados do desenvolvimento e suas versões.

# 16 - Desktop

Essa foi a versão inicial desenvolvida somente com a interface nativa do python com o tkinter, nela era possível configurar os produtos e estabelecimentos por uma tabela excel e navegar pelas etapas como mostrado nas figuras.

# 17 - Desktop Web

Por conta das limitacões anteriores foi desenvolvido então uma versão da interface web, que por utilizar varios elementos familiares á todo usuário digital, facilitou o uso da aplicacão.

Na figura da esquerda temos a tela principal da pesquisa, seguido então pela selecão de estabelecimentos.

# 18 - Desktop Web

Pesquisa continua e o campo de feedback continuo onde mostra todos os produtos coletados. E na direita temos a planilha excel com todos os estabelecimentos e seus devidos precos coletados.

# 19 - Resultado

A aplicacão pode ser encontrada no site do IMA, disponibilizado url mostrada. E nela temos uma breve descricão da aplicacão tao bem quanto o manual de utilizacão e a aplicacão em si.

# 20 - Discussões e trabalhjos futuros

Vamos então falar sobre alguns pontos que valem ser discutidos e lembrados

# 21 - Discussões

ler os tópicops

# 22 - Discussões

ler os tópicos

# 23 - Trabalhos

Ler os tópicos
