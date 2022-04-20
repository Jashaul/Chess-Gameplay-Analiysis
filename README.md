# Chess-Gameplay-Analysis
To analyse a game of chess and identify the critical position(s). A critical position is a position in chess where one player has to make a crucial move to avoid the game from being steered in an unfavorable direction. Recognizing these positions in a game is usually hard for a new or an amateur player but a well seasoned player with years of experience can identify it with ease.

## Fetch data
1) Install requirements
```
pip install -r scripts/requirements.txt
```
2) To Fetch chess data via. Lichess API, execute main.py
```Python
python scripts/main.py
```
3) Preprocess PGN(Portable Game Notation) data 
```Python
python scripts/process_pgn.py
```