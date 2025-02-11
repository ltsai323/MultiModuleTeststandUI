from flask import Flask, render_template, request, jsonify
from cform import UserInputForm

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for CSRF protection

@app.route('/', methods=['GET', 'POST'])
def index():
    form = UserInputForm()
    return render_template('c.html', form=form)

@app.route('/submit', methods=['POST'])
def submit():
    form = UserInputForm()
    if form.validate_on_submit():
        data = {
            'section1': {
                'opt1': form.opt1.data,
                'opt2': form.opt2.data,
                'opt3': form.opt3.data,
            },
            'section2': {
                'opt1': form.section2_opt1.data,
            }
        }
        print(data)  # Process the form data as needed
        return jsonify({'status': 'success', 'message': 'Data sent successfully!'})
    return jsonify({'status': 'error', 'message': 'Validation failed', 'errors': form.errors})

if __name__ == '__main__':
    app.run(debug=True)


