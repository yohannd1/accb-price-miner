from flask import Flask, render_template, request, g
from flask_material import Material
import json
import sqlite3
import sys
import database
import traceback

app = Flask(__name__)
Material(app)


@app.route("/")
def home():

    db = database.Database()
    g.city = db.db_get_city()
    g.estab = db.db_get_estab()
    g.product = db.db_get_product()

    return render_template("pages/home.html", data=g.city, search=False, product="Açúcar", city=g.city[0][0], estab_names=g.estab, products=g.product)


@app.route("/select_estab")
def select_estab():

    db = database.Database()
    city = request.args.get('city')
    g.estab = db.db_get_estab()
    g.estab_list = [estab for estab in g.estab if estab[0] == city]
    return json.dumps(g.estab_list)


@app.route("/update_estab")
def update_estab():

    db = database.Database()
    city_name = request.args.get('city_name')
    estab_name = request.args.get('estab_name')
    primary_key = request.args.get('primary_key')
    web_name = request.args.get('web_name')
    adress = request.args.get('adress')

    try:

        db.db_update_estab({"primary_key": primary_key, "city_name": city_name, "estab_name": estab_name,
                           "web_name": web_name, "adress": adress})
        return {"success": True, "message": "O estabelecimento {} foi atualizado com sucesso".format(estab_name)}

    except sqlite3.Error as er:

        # print('SQLite error: %s' % (' '.join(er.args)))
        # print("Exception class is: ", er.__class__)
        # print('SQLite traceback: ')
        # exc_type, exc_value, exc_tb = sys.exc_info()
        # print(traceback.format_exception(exc_type, exc_value, exc_tb))

        return {"success": False, "message": "O estabelecimento {} não pode ser atualizado.".format(estab_name)}


@app.route("/insert_estab")
def insert_estab():

    db = database.Database()
    city_name = request.args.get('city_name')
    estab_name = request.args.get('estab_name')
    web_name = request.args.get('web_name')
    adress = request.args.get('adress')

    try:

        db.db_save_estab({"city_name": city_name, "estab_name": estab_name,
                         "web_name": web_name, "adress": adress})
        return {"success": True, "message": "O estabelecimento {} foi adicionado com sucesso".format(estab_name)}

    except sqlite3.Error as er:

        # print('SQLite error: %s' % (' '.join(er.args)))
        # print("Exception class is: ", er.__class__)
        # print('SQLite traceback: ')
        # exc_type, exc_value, exc_tb = sys.exc_info()
        # print(traceback.format_exception(exc_type, exc_value, exc_tb))

        return {"success": False, "message": "O estabelecimento {} não pode ser adicionado.".format(estab_name)}


@app.route("/select_city")
def select_city():

    db = database.Database()
    g.cities = db.db_get_city()
    return json.dumps(g.cities)


@app.route("/insert_city")
def insert_city():

    db = database.Database()
    city_name = request.args.get('city_name')

    try:

        db.db_save_city(city_name)
        return {"success": True, "message": "A cidade {} foi adicionado com sucesso".format(city_name)}

    except sqlite3.Error as er:

        # print('SQLite error: %s' % (' '.join(er.args)))
        # print("Exception class is: ", er.__class__)
        # print('SQLite traceback: ')
        # exc_type, exc_value, exc_tb = sys.exc_info()
        # print(traceback.format_exception(exc_type, exc_value, exc_tb))

        return {"success": False, "message": "A cidade {} não pode ser adicionado.".format(city_name)}


@app.route("/remove_estab")
def remove_estab():

    db = database.Database()
    estab_name = request.args.get('estab_name')
    try:
        db.db_delete("estab", "estab_name", estab_name)
        return {"success": True, "message": "O estabelecimento {} foi removido com sucesso".format(estab_name)}

    except sqlite3.Error as er:

        # print('SQLite error: %s' % (' '.join(er.args)))
        # print("Exception class is: ", er.__class__)
        # print('SQLite traceback: ')
        # exc_type, exc_value, exc_tb = sys.exc_info()
        # print(traceback.format_exception(exc_type, exc_value, exc_tb))

        return {"success": False, "message": "O estabelecimento {} não pode ser removido.".format(estab_name)}


# Insere a função para ser chamada em todos os templates a qualquer momento
@app.context_processor
def utility_processor():
    def format_price(amount, currency="€"):
        return f"{amount:.2f}{currency}"

    def decode(text):
        return text.encode('utf8').decode('utf8')
    return dict(format_price=format_price, enumerate=enumerate, decode=decode)


if __name__ == '__main__':

    app.run(debug=True)
