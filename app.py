from flask import Flask, render_template

# app.py
from flask import Flask
import logging
import flask_apps.app_task1    as app_task1
import flask_apps.app_task2    as app_task2

logging.basicConfig(
    level=logging.DEBUG,
    format='[basicCONFIG] %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)

app = Flask(__name__)
app.register_blueprint(app_task1.app, url_prefix='/task1')
app.register_blueprint(app_task2.app, url_prefix='/task2')

@app.route("/")
def index():
    return render_template("index_mainpage.html")

@app.route("/index.html")
def index_alias():
    return render_template("index_mainpage.html")

if __name__ == "__main__":
    app.run(debug=True)


