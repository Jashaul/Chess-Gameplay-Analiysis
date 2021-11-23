import requests
import json

import logging
logging.basicConfig(filename='scraping_info.log', filemode='w', format='%(asctime)s - %(levelname)s - %(message)s', level=logging.DEBUG)

def fetch_info(user, gametype, limit = None):
    url = f"https://lichess.org/api/games/user/{user}?rated=true&perfType=\"{gametype}\"&pgnInJson=true&clocks=true&evals=true&tags=true"
    if limit:
        url = url + f'&max={limit}' 
    payload={}
    headers = {
    'Accept': 'application/x-ndjson'
    }

    try:
        logging.info(f"request start - {user}")
        file_path = f'data/{user}_data_all.json'
        response = requests.request("GET", url, headers=headers, data=payload)
        logging.info("request end")
        if response.status_code == 200:
            logging.info("writing file")
            with open(file_path, 'w') as f:
                f.write(json.dumps([record for record in response.text.split("\n")[:-1]]))
                logging.info(f"{user} data stored")
            return [user, file_path]
        else:
            logging.error(f"request error {user}: {response.status_code}")
            return None
        
    except Exception as e:
        logging.error(f"error fetching {user} game data", exc_info=True)