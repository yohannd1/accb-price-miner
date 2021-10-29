from logging import debug
from flask import Flask, render_template
from datetime import datetime
from flask_material import Material
import webbrowser

import re


app = Flask(__name__)
Material(app)


@app.route("/")
def home():
    names = ['Ilhéus', 'Itabuna', 'Porto Seguro']
    estab_names = {

        'Alana Hipermercado',
        'Atacadao',
        'Cestao da Economia',
        'Itao Supermercado',
        'Jaciana Supermercado',
        'Gbarbosa',
        'Frutaria e Mercadinho Cladudinete',
        'Nenem Supermercados',
        'Supermercado Meira - Malhado',
        'Supermercado Meira - Centro',
        'Supermercado Meira - N. Senhora da Vitoria',
        'Supermercado Meira - Vilela',
        'Supermercado Meira - N. Costa',
        'Supermercado Mangostao',

    }

    return render_template("pages/home.html", data=names, search=False, product="Açúcar", estab_names=estab_names)


@app.route("/batatinha")
def run_script():
    return "batatinha"


# Insere a função para ser chamada em todos os templates a qualquer momento
@app.context_processor
def utility_processor():
    def format_price(amount, currency="€"):
        return f"{amount:.2f}{currency}"
    return dict(format_price=format_price)


@app.context_processor
def inject_enumerate():
    return dict(enumerate=enumerate)


if __name__ == '__main__':

    app.run(debug=True)
