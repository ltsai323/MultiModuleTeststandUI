# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY ./PyModule_USBRS232_PowerSupply /app
COPY ./tools /app/tools

# Install any needed packages specified in requirements.txt
RUN pip install -U pyvisa-py
RUN pip install pyyaml psutil zeroconf pyserial pyusb 


# Make port 80 available to the world outside this container
EXPOSE 2000

