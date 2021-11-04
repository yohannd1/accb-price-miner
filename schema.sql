DROP TABLE IF EXISTS city;
DROP TABLE IF EXISTS estab;
DROP TABLE IF EXISTS product;

CREATE TABLE city (
	city_name text,
	PRIMARY KEY(city_name)
);

CREATE TABLE product (
	product_name text,
	keywords varchar,
	PRIMARY KEY(product_name)
);

CREATE TABLE estab (
	city_name text,
	estab_name text,
	adress varchar,
	web_name text,
	PRIMARY KEY(estab_name),
	FOREIGN KEY (city_name) REFERENCES city (city_name)
            ON DELETE CASCADE ON UPDATE CASCADE
);

INSERT INTO city VALUES ("Itabuna"),("Ilhéus");

INSERT INTO product VALUES ("ACUCAR CRISTAL","ACUCAR CRISTAL,ACUCAR CRISTAL 1KG"),
("ARROZ PARBOILIZADO","ARROZ PARBOILIZADO,ARROZ PARBOILIZADO 1KG"),
("BANANA PRATA","BANANA DA PRATA,BANANA PRATA,BANANA KG"),
("CAFE MOIDO","CAFE 250G,CAFE MOIDO"),
("CHA DENTRO","CHA DE DENTRO,COXAO MOLE,CARNE BOVINA CHA DE DENTRO"),
("FARINHA DE MANDIOCA","FARINHA DE MANDIOCA,FARINHA MAND,FARINHA MANDIOCA"),
("FEIJAO CARIOCA","FEIJAO CARIOCA"),
("LEITE LIQUIDO","LEITE LIQUIDO"),
("MANTEIGA 500G","MANTEIGA 500G,MANTEIGA"),
("OLEO SOJA","OLEO DE SOJA,OLEO 900ML"),
("PAO FRANCES","PAO FRANCES,PAO FRANCES KG"),
("TOMATE KG","TOMATE KG");

INSERT INTO estab VALUES ("Itabuna","Atacadao Rondelli","AVENIDA JOSE SOARES PINHEIRO 2700","RONDELLI COMERCIO E TRANSPORTE LTDA"),
("Itabuna","Bom de Preco","RUA BARAO DO RIO BRANCO 203","BOM DE PRECO"),
("Itabuna","Bom Preco","AVENIDA AZIZ MARON S/N", "BOMPRECO"),
("Itabuna","Compre Aqui - Canal","PRACA DOS CAPUCHINHOS 238","SUPERMERCADOS COMPRE AQUI"),
("Itabuna","Compre Aqui","AVENIDA AMELIA AMADO 358","SUPERMERCADOS COMPRE AQUI"),
("Itabuna","Mercado Mattos","RUA C 390","MERCADO MATOS"),
("Itabuna","Mercado Dois Imaos","AVENIDA BIONOR REBOUÇAS BRANDÃO 368","MERCADO IRMÃOS"),
("Itabuna","Maxx Atacado","RODOVIA ITABUNA - ILHEUS, KM 2, BR 415 S/N","MAXXI"),
("Itabuna","Novo Barateiro","RUA GETULIO VARGAS 116","NOVO BARATEIRO"),
("Itabuna","Supermercado Meira","AVENIDA JURACY MAGALHAES 426","SUPERMERCADOS DALNORDES"),
("Itabuna","Supermercado Barateiro","RUA JOSE BONIFACIO 226","ITAO"),
("Itabuna","Supermercado Itao - Centro","AVENIDA AMELIA AMADO 296","ITAO SUPERMERCADOS IMPORTACOES E EXPORTACOES S/A"),
("Itabuna","Supermercado Itao - S.C","AVENIDA PRINCESA ISABEL 775","HIPER ITAO"),
("Ilhéus","Alana Hipermercado","Rua Santos Dumont 40","Alana Hipermercado"),
("Ilhéus","Atacadao","Rodovia jorge Amado S/n","Atacadao"),
("Ilhéus","Cestao da Economia","Avenida Lotus 24","NAO POSSUI"),
("Ilhéus","Itao Supermercado","Avenida Petrobrás S/n","Supermercados Itao"),
("Ilhéus","Jaciana Supermercado","Rua Coronel Pessoa 51","Mercado Jaciana"),
("Ilhéus","Gbarbosa","Avenida Lomando Junior 786","GBARBOSA"),
("Ilhéus","Frutaria e Mercadinho Claudinete","Avenida Ilhéus/Salobrinho 91","Frutaria e Mercadinho Claudinete"),
("Ilhéus","Nenem Supermercados","Rua Dois de Julho  480","Meu Mercado"),
("Ilhéus","Supermercado Meira - Malhado","Rua Uruguaiana 1187","Supermercado Dalnorde"),
("Ilhéus","Supermercado Meira - Centro","Avenida Coronel Misael Tavares 432","Dalnorde Supermercados"),
("Ilhéus","Supermercado Meira - N. Senhora da Vitoria","Rua Sao Jorge 64","DALNORDE SUPERMERCADOS"),
("Ilhéus","Supermercado Meira - Vilela","Avenida Governador Paulo Souto  865","Supermercado Meira"),
("Ilhéus","Supermercado Meira - N. Costa","Rua Jacaranda 250","Dalnorde Supermercados"),
("Ilhéus","Supermercado Mangostao","Avenida Lindolfo Collor 101","Supermercado Mangostao LTDA");
