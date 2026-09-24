import json
from src.board import Board
from src.game import GameUI

def main(config):
    game = GameUI(config)
    game.play()

if __name__ == '__main__':
    size=-1
    player1=-1
    player2=-1
    while size<1:
        try:
            size=int(input("Enter board size: "))
        except ValueError:
            print("Must be an integer")
    while player1<0 or player1>2:
        try:
            player1=int(input("Who is player 1?: [0] Random, [1] Human, [2] AI"))
        except ValueError:
            print("Must be an integer in the player list")
    while player2<0 or player2>2:
            try:
                player2=int(input("Who is player 2?: [0] Random, [1] Human, [2] AI"))
            except ValueError:
                print("Must be an integer in the player list")
    config={
        'board_size': size,
        'black_stone': '○',
        'white_stone': '●',
        'enable_self_destruct': False,
        'player1': player1,
        'player2': player2
    }
    main(config)
