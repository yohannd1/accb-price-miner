from logging import debug
from flask import Flask, render_template
from datetime import datetime
from waitress import serve
import re

app = Flask(__name__)

@app.route("/")
def home():
    names = ['samuel', 'alanis', 'fernanda']
    return render_template("home.html", data=names)


if __name__ == '__main__':

    # serve(app, host="0.0.0.0", port=8080)
    app.run(debug=True)
