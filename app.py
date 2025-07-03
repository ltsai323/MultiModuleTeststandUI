from flask import Flask, render_template, request, jsonify
import flask_apps.shared_state as shared_state
from flask_wtf.csrf import CSRFProtect

# app.py
import logging
import flask_apps.app_task1    as app_task1
import flask_apps.app_task2    as app_task2

logging.basicConfig(
    level=logging.DEBUG,
    format='[basicCONFIG] %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)

app = Flask(__name__)
app.config["SECRET_KEY"] = '7eCZ^6nUxb6hjN5EbLYak&fvt'
csrf = CSRFProtect(app)
app.register_blueprint(app_task1.app, url_prefix='/task1')
app.register_blueprint(app_task2.app, url_prefix='/task2')


@app.route("/")
def index():
    return render_template("index_mainpage.html", selected_option=shared_state.jobmode)

@app.route("/index.html")
def index_alias():
    return render_template("index_mainpage.html", selected_option=shared_state.jobmode)

@app.route("/set_option", methods=["POST"])
def set_option():
    data = request.get_json()
    if "option" in data:
        shared_state.jobmode = data["option"]
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "log": f'[InvalidOption] set_option() received invalid input "{data}".'}), 400


### note only if jobmode is notSELECTED or job status is DESTROYED, allowed to select new jobmode

if __name__ == "__main__":
    app.run(debug=True)
