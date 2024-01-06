# Crypto Coins Dashboard Backend

This repository contains a Flask application for fetching, managing, and serving cryptocurrency data through API endpoints.

## Table of Contents

- [Introduction](#introduction)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [Scheduled Updates](#scheduled-updates)


## Introduction

This Flask application provides various API endpoints to handle cryptocurrency data. It fetches data from the CryptoGecko API, stores it in an SQLite database, and offers endpoints for users to retrieve, add, and remove liked coins. Additionally, it periodically updates the data using a scheduler.

## Prerequisites

- Python 3.x
- Flask
- requests
- sqlite3

## Installation

1. Clone this repository:

   ```bash
   git clone https://github.com/your-username/crypto-backend.git
   cd crypto-backend
   
1. Set up a virtual environment (optional but recommended):

```bash
python3 -m venv venv
source venv/bin/activate
```

2. Install the required packages:
```bash
pip install Flask requests
```

## Usage

Start the server:
```bash
python -m flask --app src/app.py run
```
## API Endpoints

- GET /v1/crypto: Fetches all cryptocurrency data stored in the database.
- POST /v1/users/{user_id}/add_liked_coins: Adds liked coins for a specific user.
- GET /v1/users/{user_id}/liked_coins: Retrieves liked coins for a specific user.
- DELETE /v1/users/{user_id}/liked_coins/delete: Removes liked coins for a specific user.

## Scheduled Updates
The application features a scheduler that periodically updates cryptocurrency data fetched from the CryptoGecko API. The update interval is set to every 30 seconds.
