#!/usr/bin/env python3
# app.py
from flask import Flask, render_template
import psycopg2
import plotly.express as px

app = Flask(__name__)
db_params_1_user = {
    'host':'localhost',
    'port':5423,
    'user':'test1',
    'password':'testPWD',
    'database':'TESTDB'
    }
db_params_1_root = {
        'dbname':"TESTDB",
        'user':"root",
        'password':"myROOTpasswd_",
        'host':"localhost",
        'port':5423
        }

@app.route('/')
def index():
    # Connect to PostgreSQL
    #db_param = db_params_1_root
    db_param = db_params_1_user
    connection = psycopg2.connect(**db_param)

    # Execute SQL query
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM public.cpu_usage;")
    records = cursor.fetchall()

    # Extract data for plotting
    injection_times, usages = zip(*records)

    # Create a Plotly line chart
    fig = px.line(x=injection_times, y=usages, labels={'x': 'Injection Time', 'y': 'Usage'},
                  title='Usage Over Time')

    # Save the plot as HTML
    plot_html = fig.to_html(full_html=False)

    # Close connections
    cursor.close()
    connection.close()

    return render_template('index_plotly.html', plot_html=plot_html)

if __name__ == '__main__':
    #app.run(debug=True)
    app.run(host='0.0.0.0',port=5000, debug=True)

