# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org Flask

# Make port 80 available to the world outside this container
EXPOSE 8888

# Define environment variable
ENV NAME World

# Run app.py when the container launches
CMD ["python", "app.button_send_cmd_via_socket.py"]
