from flask import Flask
import requests
import sqlite3
from flask import jsonify
from flask_cors import CORS
from flask import request

import sched
import time

import threading


app = Flask(__name__)
CORS(app, resources={r"/v1/*": {"origins": "http://localhost:3000"}})

API_ENDPOINT = 'https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=1&sparkline=false&price_change_percentage=1h&locale=en'

# Function to fetch data from the CryptoGecko API

def fetch_crypto_data():
    response = requests.get(API_ENDPOINT)
    if response.status_code == 200:
        crypto_data = response.json() 
        # Sort the data based on price_change_percentage_1h_in_currency
        sorted_data = sorted(crypto_data, key=lambda x: x.get('price_change_percentage_1h_in_currency', 0), reverse=True)
        return sorted_data
    else:
        return None
    

@app.route('/v1/crypto', methods=['GET'])
def get_crypto_data():
    conn = sqlite3.connect('crypto_data.db')
    cursor = conn.cursor()

    
    cursor.execute('''SELECT * FROM crypto_data''')
    data = cursor.fetchall()

    conn.close()

    # Convert data to a list of dictionaries
    crypto_data = []
    for row in data:
        crypto_data.append({
            'name': row[0],
            'image': row[1],
            'symbol': row[2],
            'current_price': row[3],
            'price_change_percentage_24h': row[4],
            'market_cap': row[5],
            'market_cap_rank': row[6],
            'price_change_percentage_1h_in_currency': row[7],
            'last_updated': row[8]
        })

    return jsonify(crypto_data)

def insert_data_into_db(data):
    conn = sqlite3.connect('crypto_data.db') 
    cursor = conn.cursor()
    
    # Create table if it doesn't exist
    cursor.execute('''CREATE TABLE IF NOT EXISTS crypto_data (
                        name TEXT PRIMARY KEY,
                        image TEXT,
                        symbol TEXT,
                        current_price REAL,
                        price_change_percentage_24h REAL,
                        market_cap REAL,
                        market_cap_rank INTEGER,
                        price_change_percentage_1h_in_currency REAL,
                        last_updated TEXT
                        
                    )''')
    
    for coin in data:
        try:
            cursor.execute('''INSERT INTO crypto_data (name, image, symbol, current_price, price_change_percentage_24h, market_cap, market_cap_rank, price_change_percentage_1h_in_currency, last_updated) 
                              VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', (coin['name'], coin['image'], coin['symbol'], coin['current_price'], coin['price_change_percentage_24h'],  coin['market_cap'], coin['market_cap_rank'], coin['price_change_percentage_1h_in_currency'], coin['last_updated']))
        except sqlite3.IntegrityError:
            cursor.execute('''UPDATE crypto_data
                              SET image=?, symbol=?, current_price=?, price_change_percentage_24h=?, market_cap=?, market_cap_rank=?, price_change_percentage_1h_in_currency=?, last_updated=?
                              WHERE name=?''', (coin['image'], coin['symbol'], coin['current_price'], coin['price_change_percentage_24h'],  coin['market_cap'], coin['market_cap_rank'], coin['price_change_percentage_1h_in_currency'], coin['last_updated'], coin['name']))
    
    conn.commit()  
    conn.close()   

def create_user_table():
    conn = sqlite3.connect('crypto_data.db') 
    cursor = conn.cursor()
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS user_table_crypto (
                        user_id INTEGER,
                        coin_name TEXT,
                        FOREIGN KEY (coin_name) REFERENCES crypto_data(name)
                    )''')
    
    conn.commit()
    conn.close()


create_user_table()

@app.route('/v1/users/<int:user_id>/add_liked_coins', methods=['POST'])
def add_liked_coins(user_id):
    coin_names = request.json.get('coin_names')  
    if not coin_names:
        return jsonify({'error': 'No coin names provided'}), 400
    
    conn = sqlite3.connect('crypto_data.db')
    cursor = conn.cursor()

  
    for coin_name in coin_names:
        try:
            cursor.execute('''INSERT INTO user_table_crypto (user_id, coin_name) VALUES (?, ?)''', (user_id, coin_name))
        except sqlite3.IntegrityError:
            # Handle potential duplicates or existing entries
            print(f"Coin '{coin_name}' already exists for user {user_id}.")

    conn.commit()
    conn.close()

    return jsonify({'message': 'Liked coins added successfully'}), 201  


@app.route('/v1/users/<int:user_id>/liked_coins', methods=['GET'])
def get_liked_coins(user_id):
    conn = sqlite3.connect('crypto_data.db')
    cursor = conn.cursor()

    # Fetch the names of coins liked by user_id 
    cursor.execute('''SELECT coin_name FROM user_table_crypto WHERE user_id = 1''')
    liked_coins = cursor.fetchall()
   

   
    liked_coins_details = []

    # Fetch details of each liked coin from crypto_data table
    for coin in liked_coins:
        cursor.execute("SELECT * FROM crypto_data WHERE name = ?", (coin[0],))
        coin_details = cursor.fetchone()
        
        
        if coin_details:
            coin_dict = {
                'name': coin_details[0],
                'image': coin_details[1],
                'symbol': coin_details[2],
                'current_price': coin_details[3],
                'price_change_percentage_24h': coin_details[4],
                'market_cap': coin_details[5],
                'market_cap_rank': coin_details[6],
                'price_change_percentage_1h_in_currency': coin_details[7],
                'last_updated': coin_details[8]
            }
            liked_coins_details.append(coin_dict)

    conn.close()

    return jsonify(liked_coins_details)



@app.route('/v1/users/<int:user_id>/liked_coins/delete', methods=['DELETE'])
def remove_liked_coins(user_id):
    coin_names = request.json.get('coin_names')
    if not coin_names:
        return jsonify({'error': 'No coin names provided'}), 400

    conn = sqlite3.connect('crypto_data.db')
    cursor = conn.cursor()
    print(coin_names)

    for coin_name in coin_names:

        cursor.execute('''DELETE FROM user_table_crypto WHERE user_id = ? AND coin_name = ?''', (user_id, coin_name))

    conn.commit()
    conn.close()

    return jsonify({'message': f'Coins removed successfully for user {user_id}'}), 200


# Flag to indicate whether an update is in progress
update_in_progress = False

def update_data_scheduler(scheduler):
    global update_in_progress

    if not update_in_progress:
        update_in_progress = True
        
        sorted_crypto_data = fetch_crypto_data()
        
        if sorted_crypto_data:
            insert_data_into_db(sorted_crypto_data)
            print('Data updated and sorted successfully!')
        else:
            print('Failed to update and sort data from the API.')

        update_in_progress = False
    
    # Reschedule the update after 30 seconds
    scheduler.enter(30, 1, update_data_scheduler, (scheduler,))

# Create a scheduler
update_scheduler = sched.scheduler(time.time, time.sleep)



def run_scheduler():
    update_scheduler.run()

scheduler_thread = threading.Thread(target=run_scheduler)
scheduler_thread.start()

if __name__ == '__main__':
    app.run(debug=True, port=5000)