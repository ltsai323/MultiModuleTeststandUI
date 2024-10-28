from flask import Flask, render_template, request, jsonify
from dform import UserInputFormFactory
import ConfigHandler

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for CSRF protection

@app.route('/', methods=['GET', 'POST'])
def index():
    # Example parameters
    parameters = [
        ConfigHandler.LoadedParameterIntegerField('int1', {}),
        ConfigHandler.LoadedParameterRadioField('opt1', {'options': [0, 1, 2, 3]})
    ]
    
    form_class = UserInputFormFactory('testing', parameters)
    form = form_class()

    return render_template('d.html', form=form)

@app.route('/submit', methods=['POST'])
def submit():
    parameters = [
        ConfigHandler.LoadedParameterIntegerField('int1', {}),
        ConfigHandler.LoadedParameterRadioField('opt1', {'options': [0, 1, 2, 3]})
    ]

    form_class = UserInputFormFactory('testing', parameters)
    form = form_class()

    if form.validate_on_submit():
        data = {name: getattr(form, name).data for name in form._fields}
        print('submitted data : ', data)  # Process the form data as needed
        return jsonify({'status': 'success', 'message': 'Data sent successfully!'})
    
    return jsonify({'status': 'error', 'message': 'Validation failed', 'errors': form.errors})

if __name__ == '__main__':
    app.run(debug=True)

