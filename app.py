from flask import Flask, render_template, jsonify, request
import app_global_variables as gVAR
import app_actbtn as app_actbtn
from PythonTools.DebugManager import BUG
from flask_wtf.csrf import CSRFProtect
from flask_cors import CORS
from flask import current_app

app = Flask(__name__, static_folder='./static')
app.config.from_object(gVAR.TestConfig) # initialize global variables

CORS(app, resources={r"/*": {"origins": ["http://127.0.0.1:5001", "http://127.0.0.1:5000"]}})
# add csrf protect asdf
app.secret_key = 'your_secret_key'  # Required for CSRF protection. The availability checking required
csrf = CSRFProtect(app)





@app.route('/', methods=['GET', 'POST'])
@app.route('/index')
def index():
    '''
home pages

It shows the current status of the whole jobs
This page shows action buttons configured from `app_actbtn.py`.
    '''

    return render_template('index.html')
    #return render_template('index.ref.html')


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



if __name__ == '__main__':

    app.job_is_running = False
    from app_socketio import socketio
    # regist functions from app_actbtn.py
    app.register_blueprint(app_actbtn.app_b)
    #app_actbtn.module_init(app_actbtn.app_b)
    import app_DAQresults
    app.register_blueprint(app_DAQresults.app_b)


    socketio.init_app(app)

    host='0.0.0.0'
    #host='192.168.51.213'
    port=5001
    print(f'[Web activated] {host}@{port}')
    socketio.run(app,host=host, port=port)

