import pandas as pd
from scrap import fetch_info
pd.set_option('mode.chained_assignment', None)

import logging
logging.basicConfig(filename='scraping_info.log', filemode='w', format='%(asctime)s - %(levelname)s - %(message)s', level=logging.DEBUG)

def player_iterator(player_info):
    if len(player_info[0].split("\xa0")) > 1:
        user_id = player_info[0].split("\xa0").pop()
    else:
        user_id = player_info[0]
    fetch_info(user_id, "rapid")
    return player_info
    
player_list = pd.read_csv("player_list.csv").values.tolist()
try:
    player_record = [player_iterator(record) for record in player_list[:]]
    logging.info(player_record)
except Exception as e:
    logging.debug(f"error fetching player list", exc_info=True)