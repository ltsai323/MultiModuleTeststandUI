from flask import Flask, render_template, Response, stream_with_context
import time
import sys
import threading

app = Flask(__name__)

def generate_output():
    """
    Generator function to yield the output line by line.
    """
    print('starting')
    yield "Starting execution...\n"
    for i in range(10):
        time.sleep(1)
        print('outrput')
        yield f"Output {i+1}\n"
    yield "Execution finished.\n"

@app.route('/')
def index():
    return render_template('index.html')
@app.route('/run_script')
def run_script():
    print('haaaa')


@app.route('/execute')
def execute():
    """
    Route to execute the function and stream the output.
    """
    return Response(stream_with_context(generate_output()), mimetype='text/plain')

if __name__ == "__main__":
    app.run(debug=True)

