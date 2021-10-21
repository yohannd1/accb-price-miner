from logging import debug
from flask import Flask, render_template
from datetime import datetime
from flask_material import Material

import re


class Web:

    search = False
    progress = False
    select = True

    def set_search(self, value):
        self.search = value

    def set_progress(self, value):
        self.search = value

    def set_select(self, value):
        self.select = value


app = Flask(__name__)
Material(app)


@app.route("/")
def home():
    names = ['Ilhéus', 'Itabuna', 'Porto Seguro']
    return render_template("pages/home.html", data=names, search=False)


if __name__ == '__main__':

    app.run(debug=True)
