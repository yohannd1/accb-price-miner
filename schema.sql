DROP TABLE IF EXISTS city;
DROP TABLE IF EXISTS estab;
DROP TABLE IF EXISTS product;
DROP TABLE IF EXISTS search_item;
DROP TABLE IF EXISTS search;
DROP TABLE IF EXISTS backup;

CREATE TABLE city (
	city_name text,
	PRIMARY KEY(city_name)
);

CREATE TABLE search (
	id INTEGER,
	done text,
	city_name text,
	search_date date,
	duration decimal,
	PRIMARY KEY(id),
	FOREIGN KEY (city_name) REFERENCES city (city_name) ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TABLE search_item (
	search_id text NOT NULL,
	product_name text NOT NULL,
	web_name text NOT NULL,
	adress text NOT NULL,
	price text NOT NULL,
	keyword text NOT NULL,
	PRIMARY KEY (search_id, web_name, adress, product_name, price),
	FOREIGN KEY (search_id) REFERENCES search (id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE backup (
	active text,
	city text,
	done int,
	estab_info text,
	product_info text,
	search_id text,
	FOREIGN KEY (search_id) REFERENCES search (id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE product (
	product_name text,
	keywords varchar,
	PRIMARY KEY(product_name)
);

CREATE TABLE keyword (
	id INTEGER,
	product_name text,
	keyword varchar,
	rate decimal,
	similarity decimal,
	valid boolean,
	PRIMARY KEY(id),
	FOREIGN KEY (product_name) REFERENCES product (product_name) ON UPDATE CASCADE
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

