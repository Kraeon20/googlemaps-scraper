FROM python:3.10.7

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# Install Playwright and its dependencies
RUN pip install playwright
RUN playwright install
RUN playwright install-deps

# Copy the rest of the application files to the container
COPY . .

# Expose the correct port
EXPOSE 8000

# Command to run the application
CMD ["gunicorn", "--worker-class", "eventlet", "-w", "1", "-b", "0.0.0.0:8000", "app:app"]