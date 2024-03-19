from flask import Flask, render_template, jsonify

app = Flask(__name__)




@app.route('/')
@app.route('/index')
def index():
    return render_template('index_db.html')



if __name__ == '__main__':
    app.job_is_running = False
    from app_socketio import socketio
    import app_actbtn
    app.register_blueprint(app_actbtn.app_b)
    app_actbtn.module_init(app_actbtn.app_b)
    #app.register_blueprint(app_3.app_b,  url_prefix='/pages')

    import app_bkgrun
    app.register_blueprint(app_bkgrun.app_b)
    app_bkgrun.module_init(app_bkgrun.app_b)

    # # power supply
    # from new_structure import UnitStageCommander
    # import subunit as subunit
    # pwrconn = subunit.PyModuleConnectionConfig('PWR1', '192.168.50.60', 2000)
    # pwrconf = subunit.PyModuleCommandPool('../CommandPost/data/subunit_testsample.yaml')
    # pwrunit = subunit.SubUnit(pwrconn,pwrconf)
    # app.pwrcmder = UnitStageCommander(pwrunit)

    # # SSH connector
    # sshconn = subunit.PyModuleConnectionConfig('SSHTEST1', '192.168.50.60', 2000)
    # sshconf = subunit.PyModuleCommandPool('../CommandPost/data/subunit_ssh_connect.yaml')
    # sshunit = subunit.SubUnit(sshconn,sshconf)
    # #app.sshcmder = UnitStageCommander(sshunit)

    # app.cmders = {}
    # app.cmders['sshcmder'] = UnitStageCommander(sshunit)
    # app.cmders['pwrcmder'] = UnitStageCommander(sshunit)
    # app.pwrcmder = app.cmders['pwrcmder']
    # connection in docker
    #app.conn_power_supply = ConnectConfigs(ip='172.17.0.1',port=2235)

    # connection directly executed
    #app.conn_power_supply = ConnectConfigs(ip='127.0.0.1',port=2000)


    #app.conn_power_supply = ConnectConfigs(ip='127.0.0.1',port=2000) # test module running in local
    #app.conn_power_supply = ConnectConfigs(ip='172.17.0.1',port=2001) # test module running in docker container
    #app.conn_ssh_connect = ConnectConfigs(ip='127.0.0.1',port=2000)
    #app.conn_ssh_connect = ConnectConfigs(ip='127.0.0.1',port=2000)
    #app.conn_tst_connect = ConnectConfigs(ip='127.0.0.1',port=2000)


    #app.run(debug=True)
    #app.run(host='0.0.0.0', port=8888, threaded=True)
    socketio.init_app(app)
    socketio.run(app,host='0.0.0.0', port=8888)
    #app.run(host='0.0.0.0', port=8888, threaded=True)

### asdf need to handle connection error
