import os
import pandas as pd
import requests
import json
import parse
pd.set_option('mode.chained_assignment', None)

import logging
logging.basicConfig(filename='scraping_info.log', filemode='w', format='%(asctime)s - %(levelname)s - %(message)s', level=logging.DEBUG)

#  Fetch User Information via lichess api
def fetch_player_info(user, gametype, limit = None):
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

def player_iterator(player_info):
    # parse info to get player's user name
    if len(player_info[0].split("\xa0")) > 1:
        user_id = player_info[0].split("\xa0").pop()
    else:
        user_id = player_info[0]
    # fetch player's data
    fetch_player_info(user_id, "rapid")
    return user_id

if __name__ == "__main__": 
    try:   
        # Collect list of players
        player_list = pd.read_csv("player_list.csv").values.tolist()
        # Creates data folder to store json if it doesn't exist
        if not os.path.isdir('data'):
            os.mkdir(os.path.exists(os.path.join(os.getcwd(), 'data')))
            logging.debug("created data folder")
        # Calls function to fetch player data
        player_record = [player_iterator(record) for record in player_list[:]]
        # logging.debug(player_record)
        logging.info("player data fetched")
        for user in player_record:
            # merge all the json data
            parse.parse_data([user])
        logging.debug("merged json")
    except Exception as e:
        logging.debug(f"error fetching player list", exc_info=True)