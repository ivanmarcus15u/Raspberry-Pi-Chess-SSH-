import chess
import chess.engine
import chess.pgn
import time
import os
import random

ENGINE_PATH = "/usr/games/stockfish"

def print_board(board):
    print("\n   a b c d e f g h")
    print("  -----------------")
    for rank in range(7, -1, -1):
        row = str(rank + 1) + " |"
        for file in range(8):
            piece = board.piece_at(chess.square(file, rank))
            if piece:
                row += piece.symbol() + " "
            else:
                row += ". "
        print(row + "| " + str(rank + 1))
    print("  -----------------")
    print("   a b c d e f g h\n")


def select_elo():
    print("Select ELO:")
    elos = list(range(200, 3100, 100))

    for i, e in enumerate(elos):
        print(str(i + 1) + ". " + str(e))

    while True:
        try:
            choice = int(input("> "))
            if 1 <= choice <= len(elos):
                return elos[choice - 1]
        except:
            pass
        print("Invalid selection")


def get_think_time(elo):
    return max(0.02, (elo / 3000.0) * 0.3)


def main():
    os.system("clear")

    elo = select_elo()
    think_time = get_think_time(elo)

    # ---------- Engine Setup (Pi Safe) ----------
    try:
        engine = chess.engine.SimpleEngine.popen_uci(ENGINE_PATH, timeout=20)
    except:
        print("Failed to start Stockfish. Check installation.")
        return

    engine_elo = max(1320, elo)

    try:
        engine.configure({
            "UCI_LimitStrength": True,
            "UCI_Elo": engine_elo,
            "Threads": 1,
            "Hash": 16
        })
    except:
        print("Engine configuration failed")
        engine.quit()
        return

    board = chess.Board()
    game = chess.pgn.Game()
    node = game

    print("\nGame start\n")
    print_board(board)

    move_stack = []

    while not board.is_game_over():
        user_input = input("Your move (e2e4, undo, resign, quit): ").strip().lower()

        if user_input == "quit":
            print("Exiting")
            break

        if user_input == "resign":
            print("You resigned")
            break

        if user_input == "undo":
            if len(move_stack) >= 2:
                board.pop()
                board.pop()
                move_stack.pop()
                move_stack.pop()

                node = game
                temp_board = chess.Board()

                for m in move_stack:
                    node = node.add_variation(m)
                    temp_board.push(m)

                print_board(board)
            else:
                print("Nothing to undo")
            continue

        try:
            move = chess.Move.from_uci(user_input)
            if move not in board.legal_moves:
                print("Illegal move")
                continue
        except:
            print("Invalid format (use e2e4)")
            continue

        board.push(move)
        move_stack.append(move)
        node = node.add_variation(move)

        print_board(board)

        if board.is_game_over():
            break

        # ---------- Engine Move ----------
        try:
            if elo < 1200:
                result = engine.play(
                    board,
                    chess.engine.Limit(time=think_time),
                    options={"Skill Level": max(0, int(elo / 150))}
                )
            else:
                result = engine.play(board, chess.engine.Limit(time=think_time))
        except:
            print("Engine failed during move")
            break

        engine_move = result.move

        board.push(engine_move)
        move_stack.append(engine_move)
        node = node.add_variation(engine_move)

        print("Engine:", engine_move)
        print_board(board)

    # ---------- Endgame ----------
    print("\nGame Over")

    if board.is_checkmate():
        if board.turn == chess.WHITE:
            print("Black won by checkmate")
        else:
            print("White won by checkmate")
    elif board.is_stalemate():
        print("Draw by stalemate")
    elif board.is_insufficient_material():
        print("Draw by insufficient material")
    elif board.is_fifty_moves():
        print("Draw by 50 move rule")
    elif board.is_repetition():
        print("Draw by repetition")
    else:
        print("Result:", board.result())

    # ---------- PGN ----------
    game.headers["Event"] = "Pi Chess Game"
    game.headers["White"] = "Player"
    game.headers["Black"] = "Stockfish (" + str(elo) + ")"
    game.headers["Result"] = board.result()

    pgn_string = str(game)

    filename = "game_" + str(int(time.time())) + ".pgn"
    with open(filename, "w") as f:
        f.write(pgn_string)

    print("\nPGN saved to " + filename)

    print("\nCOPY THIS PGN\n")
    print(pgn_string)
    print("\nEND PGN\n")

    engine.quit()


if __name__ == "__main__":
    main()
