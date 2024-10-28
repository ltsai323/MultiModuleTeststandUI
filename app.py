from flask import Flask, render_template, jsonify, request
from app_global_variables import _VARS_, _LOG_CENTER_, _JOB_STAT_
import app_bkgrun
import app_actbtn
from DebugManager import BUG

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for CSRF protection asdf




@app.route('/', methods=['GET', 'POST'])
@app.route('/index')
def index():
    '''
home pages

It shows the current status of the whole jobs
This page shows action buttons configured from `app_actbtn.py`.
And `app_bkgrun.py` configures the jobs sent to bkg
    '''

    form_dict = app_actbtn.AllAvailableInputFields()

    available_form_dict = {}
    for n, v in form_dict.items():
        field_names = [field.type for field in v]
        if len(field_names) > 1:
            BUG(f'all available fields in [{n}]: ', field_names)
            available_form_dict[n] = v



    BUG('get current status : ', app_bkgrun.get_current_status())
    available_buttons = app_bkgrun.get_current_status()
    the_stat = app_bkgrun.app_b.web_stat

    return render_template('index_db.html', forms = available_form_dict, availableBUTTONs = available_buttons, webSTAT = the_stat)




if __name__ == '__main__':
    app.job_is_running = False
    from app_socketio import socketio
    # regist functions from app_actbtn.py
    app.register_blueprint(app_actbtn.app_b)
    app_actbtn.module_init(app_actbtn.app_b)

    # regist functions from app_bkgrun.py
    app.register_blueprint(app_bkgrun.app_b)
    app_bkgrun.module_init(app_bkgrun.app_b)

    # how do I handle multiple connection? -> Disable duplicated connection?

    socketio.init_app(app)
    BUG(f'init of the server : initialize of the web status :', app_bkgrun.get_current_status())
    host='0.0.0.0'
    port=5001
    print(f'[Web activated] {host}@{port}')
    socketio.run(app,host=host, port=port)

