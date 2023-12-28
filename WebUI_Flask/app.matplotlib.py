# app.py
from flask import Flask, render_template
import psycopg2
import matplotlib.pyplot as plt
from io import BytesIO
import base64

app = Flask(__name__)

@app.route('/')
def index():
    # Connect to PostgreSQL

    ## permission denied to test1 user. (Only insert permission)
    # connection = psycopg2.connect(
    #     dbname="TESTDB",
    #     user="test1",
    #     password="testPWD",
    #     host="localhost",
    #     port="5423"
    # )
    connection = psycopg2.connect(
        dbname="TESTDB",
        user="root",
        password="myROOTpasswd_",
        host="localhost",
        port="5423"
    )

    # Execute SQL query
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM public.cpu_usage;")
    records = cursor.fetchall()

    # Extract data for plotting
    injection_times, usages = zip(*records)

    # Plotting
    plt.plot(injection_times, usages)
    plt.xlabel('Injection Time')
    plt.ylabel('Usage')
    plt.title('Usage Over Time')
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Save the plot to a BytesIO object
    img_stream = BytesIO()
    plt.savefig(img_stream, format='png')
    img_stream.seek(0)
    img_data = base64.b64encode(img_stream.getvalue()).decode('utf-8')
    img_url = f'data:image/png;base64,{img_data}'

    # Close connections
    cursor.close()
    connection.close()

    return render_template('index.html', img_url=img_url)

if __name__ == '__main__':
    app.run(debug=True)

