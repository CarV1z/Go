import json
from src.board import Board
from src.game import GameUI

def main(config):
    game = GameUI(config)
    game.play()

if __name__ == '__main__':
    size=-1
    while size<1:
        try:
            size=int(input("Enter board size: "))
        except ValueError:
            print("Must be an integer")
    config={
        'board_size': size,
        'black_stone': '○',
        'white_stone': '●',
        'enable_self_destruct': False
    }
    main(config)
