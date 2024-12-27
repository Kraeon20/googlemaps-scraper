from flask import Flask, render_template, request, jsonify
import asyncio
from scraper import main
from flask_socketio import SocketIO

app = Flask(__name__)
socketio = SocketIO(app, async_mode='eventlet')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/start_scraping', methods=['POST'])
def start_scraping():
    search_term = request.form['search_term']
    total = int(request.form['total'])
    search_list = [search_term]
    quantities = [total]

    socketio.start_background_task(asyncio.run, main(search_list, quantities, socketio))
    return jsonify({"message": "Scraping started!"})


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8000)