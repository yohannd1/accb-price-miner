# from eventlet.hubs import epolls, kqueue, selects
# from dns import dnssec, e164, hash, namedict, tsigkeyring, update, version, zone

from flask import Flask, render_template, request, g
from engineio.async_drivers import gevent
from flask_material import Material
from flask_socketio import SocketIO, send, emit
import time
import json
import sqlite3
import sys
import database
import traceback
import scrapper
from datetime import date

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
Material(app)
socketio = SocketIO(app)

# Quando usar list_estab ou list_product novamente e atualizar, lembrar da rota anterior.


def log_error(err):

    with open('err.log', 'w+') as outfile:

        outfile.write("Date : {} \n".format(time.asctime()))
        for error in err:
            outfile.write(str(error))

    return


@app.route("/")
def home():

    db = database.Database()

    search = db.db_get_search('search_date', str(date.today()))
    search_id = search[0][0] if len(search) != 0 else None
    search = True

    backup_info = db.db_get_backup(search_id)

    if len(backup_info) != 0:

        active, city, done, estab_info, product_info, search_id = backup_info[0]
        estab_info = json.loads(estab_info)
        estab_names = estab_info['names']
        estab_data = estab_info['info']
        product = json.loads(product_info)

        if done == 0:

            search = True

    city = db.db_get_city()
    estab = db.db_get_estab()
    product = db.db_get_product()

    return render_template("home.html", data=city, search=search, product="Açúcar", city=city[0][0], estab_names=estab, products=product)


@app.route("/insert_product")
def insert_product():

    db = database.Database()
    product_name = request.args.get('product_name')
    keywords = request.args.get('keywords')

    try:

        db.db_save_product(
            {"product_name": product_name, "keywords": keywords})
        return {"success": True, "message": "O produto {} foi inserido com sucesso".format(product_name)}

    except sqlite3.Error as er:

        # print('SQLite error: %s' % (' '.join(er.args)))
        # print("Exception class is: ", er.__class__)
        # print('SQLite traceback: ')
        exc_type, exc_value, exc_tb = sys.exc_info()
        log_error(traceback.format_exception(exc_type, exc_value, exc_tb))

        return {"success": False, "message": "O produto {} não pode ser inserido.".format(product_name)}


@app.route("/remove_product")
def remove_product():

    db = database.Database()
    product_name = request.args.get('product_name')
    try:
        db.db_delete("product", "product_name", product_name)
        return {"success": True, "message": "O produto {} foi removido com sucesso".format(product_name)}

    except sqlite3.Error as er:

        # print('SQLite error: %s' % (' '.join(er.args)))
        # print("Exception class is: ", er.__class__)
        # print('SQLite traceback: ')
        exc_type, exc_value, exc_tb = sys.exc_info()
        log_error(traceback.format_exception(exc_type, exc_value, exc_tb))

        return {"success": False, "message": "O produto {} não pode ser removido.".format(product_name)}


@app.route("/select_product")
def select_product():

    db = database.Database()
    products = db.db_get_product()

    return json.dumps([product for product in products])


@app.route("/update_product")
def update_product():

    db = database.Database()
    product_name = request.args.get('product_name')
    keywords = request.args.get('keywords')
    primary_key = request.args.get('primary_key')

    try:

        db.db_update_product(
            {"product_name": product_name, "keywords": keywords, "primary_key": primary_key})
        return {"success": True, "message": "O produto {} foi atualizado com sucesso".format(primary_key)}

    except sqlite3.Error as er:

        # print('SQLite error: %s' % (' '.join(er.args)))
        # print("Exception class is: ", er.__class__)
        # print('SQLite traceback: ')
        exc_type, exc_value, exc_tb = sys.exc_info()
        log_error(traceback.format_exception(exc_type, exc_value, exc_tb))

        return {"success": False, "message": "O produto {} não pode ser atualizado.".format(primary_key)}


@app.route("/select_estab")
def select_estab():

    db = database.Database()
    city = request.args.get('city')
    g.estab = db.db_get_estab()
    g.estab_list = [estab for estab in g.estab if estab[0] == city]
    return json.dumps(g.estab_list)


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
        exc_type, exc_value, exc_tb = sys.exc_info()
        log_error(traceback.format_exception(exc_type, exc_value, exc_tb))

        return {"success": False, "message": "O estabelecimento {} não pode ser removido.".format(estab_name)}


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
        exc_type, exc_value, exc_tb = sys.exc_info()
        log_error(traceback.format_exception(exc_type, exc_value, exc_tb))

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
        exc_type, exc_value, exc_tb = sys.exc_info()
        log_error(traceback.format_exception(exc_type, exc_value, exc_tb))

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
        exc_type, exc_value, exc_tb = sys.exc_info()
        log_error(traceback.format_exception(exc_type, exc_value, exc_tb))

        return {"success": False, "message": "A cidade {} não pode ser adicionado.".format(city_name)}


@app.route("/update_city")
def update_city():

    db = database.Database()
    city_name = request.args.get('city_name')
    primary_key = request.args.get('primary_key')

    try:

        db.db_update_city({"city_name": city_name, "primary_key": primary_key})
        return {"success": True, "message": "A cidade {} foi editada com sucesso".format(city_name)}

    except sqlite3.Error as er:

        print('SQLite error: %s' % (' '.join(er.args)))
        print("Exception class is: ", er.__class__)
        print('SQLite traceback: ')
        exc_type, exc_value, exc_tb = sys.exc_info()
        log_error(traceback.format_exception(exc_type, exc_value, exc_tb))

        return {"success": False, "message": "A cidade {} não pode ser editada.".format(city_name)}


@app.route("/delete_city")
def delete_city():

    db = database.Database()
    city_name = request.args.get('city_name')

    try:

        db.db_delete('city', 'city_name', city_name)
        return {"success": True, "message": "A cidade {} foi deletada com sucesso".format(city_name)}

    except sqlite3.Error as er:

        # print('SQLite error: %s' % (' '.join(er.args)))
        # print("Exception class is: ", er.__class__)
        # print('SQLite traceback: ')
        exc_type, exc_value, exc_tb = sys.exc_info()
        log_error(traceback.format_exception(exc_type, exc_value, exc_tb))

        return {"success": False, "message": "A cidade {} não pode ser deletada.".format(city_name)}


# SocketIO

@socketio.on('search')
def handle_search(msg):

    db = database.Database()

    search = db.db_get_search('search_date', str(date.today()))
    search_id = search[0][0] if len(search) != 0 else None

    backup_info = db.db_get_backup(search_id)

    if len(backup_info) != 0 and msg['backup'] == 1:

        emit('captcha', {"type": 'notification',
             "message": "Retomando pesquisa ..."}, broadcast=True)
        active, city, done, estab_info, product_info, search_id = backup_info[0]
        estab_info = json.loads(estab_info)
        estab_names = estab_info['names']
        estab_data = estab_info['info']
        product = json.loads(product_info)

        if done == 0:
            scrap = scrapper.Scrap(
                estab_data, city, estab_names, product, active, search_id, False)

    else:
        emit('captcha', {"type": 'notification',
             "message": "Iniciando pesquisa ..."}, broadcast=True)
        if(msg['backup'] == 1 and len(backup_info) != 0):
            query = "DELETE * FROM search WHERE id = {}".format(search_id)
            db.db_run_query(query)

        search_id = db.db_save_search(0)
        active = 0.0
        city = msg['city']
        estab_names = json.loads(msg['names'])
        estabs = db.db_get_estab()
        product = db.db_get_product()

        estab_data = [estab for estab in estabs if estab[0]
                      == city and estab[1] in estab_names]

        scrap = scrapper.Scrap(estab_data, city, estab_names,
                               product, active, search_id, False)

        db.db_save_backup({'active': 0.0, 'city': city, 'done': 0, 'estab_info': json.dumps(
            {'names': estab_names, 'info': estab_data}), 'product_info': json.dumps(product), 'search_id': search_id})

    try:

        scrap.run()

    except:

        send({"type": 'error',
             "message": "Ocorreu um erro durante a pesquisa."}, broadcast=True)
        exc_type, exc_value, exc_tb = sys.exc_info()
        log_error(traceback.format_exception(exc_type, exc_value, exc_tb))

# Insere a função para ser chamada em todos os templates a qualquer momento


@app.context_processor
def utility_processor():

    def decode(text):
        return text.encode("utf8").decode("utf8")

    return dict(enumerate=enumerate, decode=decode)


if __name__ == '__main__':

    # app.run(debug=True)
    socketio.run(app, debug=True)
