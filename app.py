from flask import Flask, render_template, request, jsonify
import flask_apps.shared_state as shared_state
from flask_wtf.csrf import CSRFProtect

# app.py
import logging
import logging.config
from datetime import datetime

import os
os.system('mkdir -p logs')
logfile = datetime.now().strftime("logs/app_%Y%m%d-%H%M%S.log")


class StatusFilter(logging.Filter):
    def filter(self, record):
        # Return False to exclude log records containing "/status HTTP/1.1"
        msg = record.getMessage()
        if "/status HTTP/1.1" in msg:
            return False
        return True

#logging.basicConfig(
#    level=logging.DEBUG,
#    format='[basicCONFIG AAAA] %(levelname)s - %(message)s',
#    datefmt='%H:%M:%S'
#)
#logger = logging.getLogger('flask.app')
#logger = logging.getLogger('werkzeug')
#logger.addFilter(StatusFilter())
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "status_filter": {
            "()": StatusFilter
        }
    },
    "formatters": {
        "default": {
            "format": "[%(levelname)s] %(asctime)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "level": "INFO",
            "filters": ["status_filter"],
            "stream": "ext://sys.stdout"
        },
        "file": {
            "class": "logging.FileHandler",
            "formatter": "default",
            "level": "DEBUG",
            "filename": logfile,
            "encoding": "utf8",
            "mode": "a"
        }
    },
    "loggers": {
        # Configure your Flask app logger
        "flask.app": {  # Replace with your app's module name or use app.logger.name
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False
        },
        # Werkzeug logger - optional, also filtered
        "werkzeug": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "filters": ["status_filter"],
            "propagate": False
        }
    },
    "root": {
        "level": "WARNING",
        "handlers": ["console", "file"]
    }
}
logging.config.dictConfig(LOGGING_CONFIG)



import flask_apps.app_task1    as app_task1
import flask_apps.app_task2    as app_task2
import flask_apps.app_daqsummary as app_daqsummary

app = Flask(__name__)
app.config["SECRET_KEY"] = '7eCZ^6nUxb6hjN5EbLYak&fvt'
csrf = CSRFProtect(app)
app.register_blueprint(app_task1.app, url_prefix='/task1')
app.register_blueprint(app_task2.app, url_prefix='/task2')

app.register_blueprint(app_daqsummary.app)


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

#@app.route('/status')
#def status():
#    return jsonify( {'status':shared_state.server_status, 'jobmode':shared_state.jobmode} )

### note only if jobmode is notSELECTED or job status is DESTROYED, allowed to select new jobmode

if __name__ == "__main__":
    app.run(debug=True, port=5001)
