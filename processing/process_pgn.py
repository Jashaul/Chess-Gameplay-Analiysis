import csv
import heapq
import re
import chess
import pandas as pd


def timer_to_seconds(timer):
    split_timer = timer.split(':')
    return int(split_timer[2]) + (int(split_timer[1]) * 60) + (int(split_timer[0]) * 60 * 60)


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


def process_pgn(id, pgn):
    parsed_pgn = {}
    split_pgn = [x for x in pgn.split('\n') if len(x.strip()) != 0]
    for row in split_pgn[:-1]:
        split_row = row.split('[')[1].split(' \"')
        key = split_row[0]
        value = split_row[1].split('\"]')[0]
        parsed_pgn[key] = value
    moves = split_pgn[-1]
    parsed_moves = []
    re_query = "(\d*)\.?\.?\.?\s((\w*|O-O|O-O-O|\w*=?@?\w*)+#?\+?)\s{\s(\[%eval\s#?(-?\d*(\.\d*)?)\]\s)?\[%clk\s(\d*:\d*\:\d*)\]\s}"
    matches = re.findall(re_query, moves)

    if "standard" not in parsed_pgn["Variant"].lower() or parsed_pgn["TimeControl"] == "-":
        return None

    parsed_moves = []
    clock, addition = (int(x) for x in parsed_pgn["TimeControl"].split('+'))
    if clock < 600:
        return None
    black_move_rating = 0.0
    white_move_rating = 0.0
    black_player_clock = clock
    white_player_clock = clock
    player = "white"
    count = 0
    moves_heap = []
    board = chess.Board()
    for x in matches:
        possible_moves = str(board.legal_moves).split(' (')[1].split(")>")[0].split(', ')
        possible_captures = [x for x in possible_moves if 'x' in x]
        current_play = x[1]
        board.push_san(current_play)
        stockfish_rating = x[4]
        game_timer = x[6]
        white_elo = int(parsed_pgn["WhiteElo"])
        black_elo = int(parsed_pgn["BlackElo"])
        parsed_move = {
            "play_no": int(x[0]),
            "game_type": parsed_pgn["Event"],
            "game_id": id,
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
        elapsed_time = 0
        board_config = re.split('\s',board.__str__())
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
        if player == "white":
            elapsed_time = white_player_clock - parsed_move["time_remaining"]
            white_player_clock = parsed_move['time_remaining'] + addition
        else:
            elapsed_time = black_player_clock - parsed_move["time_remaining"]
            black_player_clock = parsed_move["time_remaining"] + addition
        parsed_move["elapsed_time"] = elapsed_time
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
            stockfish_rating = ""
            parsed_move["stockfish_rating"] = ""
            parsed_move["eval_change"] = ""
        if count > 18:
            if stockfish_rating != "":
                if 0 < abs(stockfish_rating) <= 2:
                    moves_heap.append((count, elapsed_time))
            else:
                moves_heap.append((count, elapsed_time))
        count += 1
        parsed_moves.append(parsed_move)
        player = "black" if player != "black" else "white"
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
    #
    # # extracting field names through first row
    # fields = next(csvreader)

    # extracting each data row one by one
    for row in csvreader:
        index += 1
        if len(row) != 0 and row[0] == "id":
            fields = row
            continue

        pgn_index = fields.index("pgn")
        processed_pgn = process_pgn(row[0], row[pgn_index])
        if processed_pgn is not None:
            processed_index += 1
            processed_rows.append(dict(zip(fields, row)))
            parsed_pgn += processed_pgn[1]

    # get total number of rows
    print("Total no. of rows: %d" % (csvreader.line_num))

print(len(parsed_pgn))
csv_fields = list(parsed_pgn[0].keys())
with open('parsed_pgn.csv', 'w') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=csv_fields)
    writer.writeheader()
    writer.writerows(parsed_pgn)
