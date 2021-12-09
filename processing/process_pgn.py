import csv
import heapq
import re
import chess
import pandas as pd


def timer_to_seconds(timer):
    split_timer = timer.split(':')
    return int(split_timer[2]) + (int(split_timer[1]) * 60) + (int(split_timer[0]) * 60 * 60)


# Initializing the default board config for black and white
default_black_config = {0: 'r',
                        1: 'n',
                        2: 'b',
                        3: 'q',
                        4: 'k',
                        5: 'b',
                        6: 'n',
                        7: 'r'}
default_white_config = {56: 'R',
                        57: 'N',
                        58: 'B',
                        59: 'Q',
                        60: 'K',
                        61: 'B',
                        62: 'N',
                        63: 'R'}


def process_pgn(game_id, pgn):
    # Function to process individual PGNs
    parsed_pgn = {}
    split_pgn = [x for x in pgn.split('\n') if len(x.strip()) != 0]
    for pgn_row in split_pgn[:-1]:
        split_row = pgn_row.split('[')[1].split(' \"')
        key = split_row[0]
        value = split_row[1].split('\"]')[0]
        parsed_pgn[key] = value
    moves = split_pgn[-1]
    # Regular Expression to parse the moves in PGN
    re_query = "(\d*)\.?\.?\.?\s((\w*|O-O|O-O-O|\w*=?@?\w*)+#?\+?)\s{\s(\[%eval\s#?(-?\d*(\.\d*)?)\]\s)?\[%clk\s(\d*:\d*\:\d*)\]\s}"
    matches = re.findall(re_query, moves)

    if "standard" not in parsed_pgn["Variant"].lower() or parsed_pgn["TimeControl"] == "-":
        # Checking if the game variant is standard and there is TimeControl
        return None

    parsed_moves = []
    clock, addition = (int(x) for x in parsed_pgn["TimeControl"].split('+'))
    if clock < 600:
        # Discarding games which are less than 10 minutes
        return None
    black_move_rating = 0.0
    white_move_rating = 0.0
    black_player_clock = clock
    white_player_clock = clock
    player = "white"
    count = 0
    moves_heap = []
    # Initializing the chess board
    board = chess.Board()
    for x in matches:
        # Fetching Possible moves at a current position in game
        possible_moves = str(board.legal_moves).split(' (')[1].split(")>")[0].split(', ')
        # Fetching the possible captures from the list of possible moves
        possible_captures = [x for x in possible_moves if 'x' in x]
        # Fetching the current move/play from PGN
        current_play = x[1]
        # Performing the move on chess board
        board.push_san(current_play)
        # Fetching Stockfish rating from PGN
        stockfish_rating = x[4]
        game_timer = x[6]
        # Fetching Player rating for White and Black
        white_elo = int(parsed_pgn["WhiteElo"])
        black_elo = int(parsed_pgn["BlackElo"])
        parsed_move = {
            "play_no": int(x[0]),
            "game_type": parsed_pgn["Event"],
            "game_id": game_id,
            "player": player,
            "possible_moves": possible_moves,
            "no_moves": len(possible_moves),
            'possible_captures': possible_captures,
            "no_captures": len(possible_captures),
            "play": current_play,
            "clock_timer": game_timer,
            "time_remaining": timer_to_seconds(game_timer),
            'game': board.__str__(),
            'WhiteElo': white_elo,
            'BlackElo': black_elo,
            "Result": parsed_pgn["Result"],
            "RatingDiff": abs(white_elo - black_elo),
            "critical_position": 0  # Top 3 moves based on elapsed time
        }
        board_config = re.split("\s", board.__str__())
        # Fetching the number of developed pieces for black and white
        developed_pieces_white = 0
        for piece_index, piece in default_white_config.items():
            if board_config[piece_index] != piece:
                developed_pieces_white += 1
        parsed_move["developed_pieces_white"] = developed_pieces_white
        developed_pieces_black = 0
        for piece_index, piece in default_black_config.items():
            if board_config[piece_index] != piece:
                developed_pieces_black += 1
        parsed_move["developed_pieces_black"] = developed_pieces_black

        # Calculating elapsed time for both white and black
        elapsed_time = 0
        if player == "white":
            elapsed_time = white_player_clock - parsed_move["time_remaining"]
            white_player_clock = parsed_move['time_remaining'] + addition
        else:
            elapsed_time = black_player_clock - parsed_move["time_remaining"]
            black_player_clock = parsed_move["time_remaining"] + addition
        parsed_move["elapsed_time"] = elapsed_time

        # Calculating the change in stockfish evaluation due the current move
        if len(stockfish_rating) != 0:
            if '#' in stockfish_rating:
                stockfish_rating = 100 if float(stockfish_rating.split('#')[1]) > 0 else -100
            else:
                stockfish_rating = float(stockfish_rating)

            if player == "white":
                eval_change = stockfish_rating - white_move_rating
                white_move_rating = stockfish_rating
            else:
                eval_change = stockfish_rating - black_move_rating
                black_move_rating = stockfish_rating
            parsed_move["stockfish_rating"] = stockfish_rating
            parsed_move["eval_change"] = eval_change
        else:
            # Initializing stockfish evaluation to empty string if unavailable
            stockfish_rating = ""
            parsed_move["stockfish_rating"] = ""
            parsed_move["eval_change"] = ""

        # Considering the mid game moves only with
        if count > 18:
            if stockfish_rating != "":
                if 0 < abs(stockfish_rating) <= 2:
                    moves_heap.append((count, elapsed_time))
            else:
                moves_heap.append((count, elapsed_time))
        count += 1
        parsed_moves.append(parsed_move)
        player = "black" if player != "black" else "white"
    # Marking the top 3 moves from heap into
    for heapIndex, _ in heapq.nlargest(10, moves_heap, key=lambda x: x[1]):
        parsed_moves[heapIndex]["critical_position"] = 1
    return parsed_pgn, parsed_moves


# csv file name
filename = "/Users/vamshiadi/Downloads/all.csv"

# initializing the titles and rows list
fields = []
parsed_pgn = []
processed_rows = []
# reading csv file
index = 0
processed_index = 0
with open(filename, 'r') as csvfile:
    # creating a csv reader object
    csvreader = csv.reader(csvfile)

    # extracting each data row one by one
    for row in csvreader:
        index += 1
        if len(row) != 0 and row[0] == "id":
            # Checking if the row is fields row
            fields = row
            continue

        pgn_index = fields.index("pgn")
        processed_pgn = process_pgn(row[0], row[pgn_index])
        if processed_pgn is not None:
            # Checking and saving the processed moves from the pgn
            processed_index += 1
            parsed_pgn += processed_pgn[1]
# Fetching CSV Fields for CSV Writer
csv_fields = list(parsed_pgn[0].keys())
# Writing the csv to file.
with open('parsed_pgn.csv', 'w') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=csv_fields)
    writer.writeheader()
    writer.writerows(parsed_pgn)
