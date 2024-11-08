from flask import Flask, render_template, jsonify, request
from app_global_variables import _VARS_, _LOG_CENTER_, _JOB_STAT_
import app_bkgrun
import app_actbtn
from DebugManager import BUG
from flask_wtf.csrf import CSRFProtect
from flask_cors import CORS
import WebStatus

app = Flask(__name__, static_folder='./static')

CORS(app, resources={r"/*": {"origins": ["http://127.0.0.1:5001", "http://127.0.0.1:5000"]}})
# add csrf protect asdf
app.secret_key = 'your_secret_key'  # Required for CSRF protection. The availability checking required
csrf = CSRFProtect(app)

current_status = None # initialized at main function()


# def current_status() # new function for sockeio



@app.route('/', methods=['GET', 'POST'])
@app.route('/index')
def index():
    '''
home pages

It shows the current status of the whole jobs
This page shows action buttons configured from `app_actbtn.py`.
And `app_bkgrun.py` configures the jobs sent to bkg
    '''

    # I should delete this block but later
    # ''' '''
    # form_dict = app_actbtn.AllAvailableInputFields()

    # available_form_dict = {}
    # for n, v in form_dict.items():
    #     field_names = [field.type for field in v]
    #     if len(field_names) > 1:
    #         BUG(f'all available fields in [{n}]: ', field_names)
    #         available_form_dict[n] = v



    # BUG('get current status : ', app_bkgrun.get_current_status())
    # available_buttons = app_bkgrun.get_current_status()
    # the_stat = app_bkgrun.app_b.web_stat
    # ''' '''


    # should add fetch() function to index.html that require current status from api/current_status or use "initialize" button

    return render_template('index.html')
    #return render_template('index.html', forms = available_form_dict, availableBUTTONs = available_buttons, webSTAT = the_stat)


@app.route('/show_logpage')
def show_logpage():
    button_id = request.args.get('btnID')  # Retrieve the 'file' parameter from the URL
    if button_id:
        try:
            # Try to open the specific file based on the provided file name
            with open(f'logs/log_{button_id}', 'r') as file:
                content = file.read()
        except Exception as e:
            content = f"Error reading file log_{button_id}: {str(e)}"
    else:
        content = "No file specified."

    return render_template('show_logpage.html', btnID=button_id, content=content)

@app.route('/btn_initialize', methods=['GET'])
def btn_initialize():
    return current_status.jsonify()


if __name__ == '__main__':
    current_status = WebStatus.WebStatus()
    WebStatus.TestFunc(current_status)



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
    host='192.168.50.60'
    port=5001
    print(f'[Web activated] {host}@{port}')
    socketio.run(app,host=host, port=port)

