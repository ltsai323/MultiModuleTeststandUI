from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

user_input = {
    'section1': [
        {'id': 'opt1', 'type': 'radio', 'default_values': ['val1', 'val2', 'val3']},
        {'id': 'opt2', 'type': 'text', 'default_values': 'mesg'},
        {'id': 'opt3', 'type': 'number', 'default_values': 27},
    ],
    'section2': [
        {'id': 'opt1', 'type': 'text', 'default_values': 'mesg'},
    ]
}

@app.route('/')
def index():
    return render_template('b.html', user_input=user_input)

@app.route('/submit', methods=['POST'])
def submit():
    data = request.get_json()
    print('received data')
    for key, val in data.items():
        print(f'{key} : {val}')
    #print(data)  # Process the incoming data as needed
    return jsonify({'status': 'success', 'data': data})

if __name__ == '__main__':
    app.run(debug=True)
