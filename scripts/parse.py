import pandas as pd
import logging
import json
from flatten_json import flatten
logging.basicConfig(filename='scraping_info.log', filemode='w', format='%(asctime)s - %(levelname)s - %(message)s', level=logging.DEBUG)

# converts each player's json data to csv and merges all csv
def parse_data(record, table_info = None):
    if len(record[0].split("\xa0")) > 1:
        user_id = record[0].split("\xa0").pop()
    else:
        user_id = record[0]
    # read json file
    df = pd.read_json(f'data/{user_id}_data_all.json')
    print(df.size)
    if table_info == None:
        table_info = []
    for i in range(df.size):
        # convert to dict
        info = json.loads(df.loc[i][0])
        if 'analysis' in info:
            analysis_info = str(info['analysis'])
            info.pop('analysis', None)
        else:
            analysis_info = None        
        info = flatten(info)
        info['analysis'] = analysis_info
        table_info.append(info)
    # convert list to dataframe and store in csv file        
    table_df = pd.json_normalize(table_info)
    table_df.to_csv('raw_data.csv', mode='a', index=False, encoding='utf-8')
    return True

def merge_data():
    player_list = pd.read_csv("player_list.csv").values.tolist()
    try:
        for record in player_list[:]:
            parse_data(record)
            logging.info(record)
    except Exception as e:
        logging.debug(f"error stiching player data", exc_info=True)