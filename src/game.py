import copy
import random

from src.board import Board
from src.utils import Stone, make_2d_array, get_opposite_stone
from src.group import Group, GroupManager
from src.exceptions import (
    SelfDestructException, KoException, InvalidInputException)

class Game(object):
    '''
    Manage the high level gameplay of Go
    '''
    def __init__(self, config, board=None, gm=None, count_pass=0):
        if board is None:
            self.board = Board(config)
        else:
            self.board = board

        self.board_size = config['board_size']
        self.player1 = config.get('player1', 0)
        self.player2 = config.get('player2', 0)

        if gm is None:
            self.gm = GroupManager(self.board,
                                   enable_self_destruct=config['enable_self_destruct'])
        else:
            self.gm = gm

        self.count_pass = count_pass

    def create_copy(self):
        return copy.deepcopy(self)

    def place_black(self, y, x):
        '''
        Place a black stone at coordinate (y, x)
        '''
        self._place_stone(Stone.BLACK, y, x)

    def place_white(self, y, x):
        '''
        Place a white stone at coordinate (y, x)
        '''
        self._place_stone(Stone.WHITE, y, x)

    def pass_turn(self):
        '''
        Pass this turn
        '''
        self.count_pass += 1

    def is_over(self):
        '''
        Check if the game is over (only if there are two consecutive passes)
        '''
        return self.count_pass >= 2
    
    def is_within_bounds(self, y, x):
        '''
        Check if the given coordinate is within the range of the board
        '''
        return self.board.is_within_bounds(y, x)

    def _place_stone(self, stone, y, x):
        '''
        Place a stone at (y, x), then resolve interactions due to the move.
        Throw an exception if self-destruct or ko rules are violated
        '''
        if stone == Stone.EMPTY:
            return False
        if self.board[y][x]!=Stone.EMPTY:
            return False
        self.board.place_stone(stone, y, x)
        self.gm.board.place_stone(stone,y,x)
        try:
            self.gm.resolve_board(y, x)
        except SelfDestructException as e:
            self.board.remove_stone(y, x)
            raise e
        except KoException as e:
            self.board.remove_stone(y, x)
            raise e
            
        self.count_pass = 0
        self.gm.update_state()
        return True

    @property
    def num_black_captured(self):
        '''
        Return the number of captured black stones
        '''
        return self.gm._num_captured_stones[Stone.BLACK]

    @property
    def num_white_captured(self):
        '''
        Return the number of captured white stones
        '''
        return self.gm._num_captured_stones[Stone.WHITE]

    def render_board(self):
        '''
        Render the board
        '''
        self.board._render()

    def get_scores(self):
        '''
        Return the score under Chinese / area scoring.

        Each stone on the board is worth 1 point, and each connected empty region
        is counted for the player whose stones surround it entirely.
        Neutral regions that touch both colors are ignored.
        '''
        scores = {Stone.BLACK: 0, Stone.WHITE: 0}

        for y in range(self.board_size):
            for x in range(self.board_size):
                stone = self.board[y, x]
                if stone == Stone.BLACK:
                    scores[Stone.BLACK] += 1
                elif stone == Stone.WHITE:
                    scores[Stone.WHITE] += 1

        traversed = make_2d_array(self.board_size, self.board_size,
                                  default=lambda: False)

        for y in range(self.board_size):
            for x in range(self.board_size):
                if traversed[y][x] or self.board[y, x] != Stone.EMPTY:
                    continue

                search = [(y, x)]
                traversed[y][x] = True
                region = []
                owners = set()

                while search:
                    cy, cx = search.pop()
                    region.append((cy, cx))

                    for ly, lx in self.board.get_liberty_coords(cy, cx):
                        neighbor = self.board[ly, lx]
                        if neighbor == Stone.EMPTY and not traversed[ly][lx]:
                            traversed[ly][lx] = True
                            search.append((ly, lx))
                        elif neighbor in (Stone.BLACK, Stone.WHITE):
                            owners.add(neighbor)

                if len(owners) == 1:
                    scores[next(iter(owners))] += len(region)

        return scores
    def get_legal_moves(self,team):
        moves=[]
        for i in range (self.board_size):
            for j in range(self.board_size):
                try:
                    new_board=self.create_copy()
                    success=new_board._place_stone(team,i,j)
                    #print(new_board.board)
                    if success:
                        if team==Stone.BLACK:
                            if new_board.board[i][j]==Stone.BLACK:
                                moves.append(str(i)+" "+str(j))
                        else:
                            if new_board.board[i][j]==Stone.WHITE:
                                moves.append(str(i)+" "+str(j))
                except KoException:
                    x=1
                except SelfDestructException:
                    x=1
        return moves


class GameUI(object):
    '''
    Main interface between the game and the players
    '''
    def __init__(self, config):

        # the game object
        self.game = Game(config)

        # store which player's turn it is
        self.turn = Stone.BLACK

    def play(self):
        '''
        Start the game of Go. Two players alternate turns placing stones on the board
        until the game is over.
        '''
        while not self.game.is_over():
            is_turn_over = False
            self.game.render_board()
            print(self.game.get_legal_moves(self.turn))

            while not is_turn_over:
                if self.turn==Stone.BLACK:
                    if self.game.player1==1:
                        move = self._prompt_move()
                    else:
                        move=self.get_move(self.turn,self.game.player1)
                else:
                    if self.game.player2==1:
                        move=self._prompt_move()
                    else:
                        move=self.get_move(self.turn,self.game.player2)
                if move == 'pass':
                    self.game.pass_turn()
                    is_turn_over = True
                else:
                    is_turn_over = self._place_stone(move)

            self._switch_turns()

        self._display_result()

    def _display_result(self):
        '''
        Show the result of the game including the scores and winner
        '''
        scores = self.game.get_scores()
        black_score = scores[Stone.BLACK]
        white_score = scores[Stone.WHITE]

        print(f'Black score: {black_score}')
        print(f'White score: {white_score}')

        if black_score == white_score:
            print('The result is a tie!')
        else:
            winner = Stone.BLACK if black_score > white_score else Stone.WHITE
            winner = self._get_player_name(winner)
            print(f'The winner is {winner}!')        

    def _place_stone(self, move):
        '''
        Place a stone at the specified coordinate. Return True if it is valid
        '''
        y, x = move
        try:
            if self.turn == Stone.BLACK:
                self.game.place_black(y, x)
            elif self.turn == Stone.WHITE:
                self.game.place_white(y, x)
            is_turn_over = True
        except Exception as e:
            print(e)
            is_turn_over = False
        return is_turn_over

    def _get_player_name(self, stone):
        '''
        Return the player name for the specified stone
        '''
        return 'Black' if stone == Stone.BLACK else 'White'

    def _switch_turns(self):
        '''
        Swap the turn
        '''
        self.turn = Stone.BLACK if self.turn == Stone.WHITE else Stone.WHITE
        
    def _prompt_move(self):
        '''
        Prompt a user input move. The input format is one of
            - "pass" to pass for the current player   or
            - "y x" to place a stone at the specified coordinate
        The prompt repeats until a valid input is given
        '''
        move = None
        player = self._get_player_name(self.turn)
        while not self._is_valid_input(move):
            print('Please input a valid move'
            '(enter "pass" to pass or "y x" to place a stone at the coordinate (y, x))')
            move = input(f'{player} move: ')
        
        return self._parse_move(move)

    def get_move(self,team,player):
        moves=self.game.get_legal_moves(team)
        oppMoves=self.game.get_legal_moves(get_opposite_stone(team))
        if player==0:
            if len(moves)==0 or len(oppMoves)==0:
                return 'pass'
            move=random.choice(moves)
        #else:
        #your AI
        #just set different numbers of player to different versions
        return self._parse_move(move)
        
    
    def _is_valid_input(self, move):
        '''
        Check if the given input would give a valid move, in terms of placing a stone
        on the board
        '''
        if move == 'pass':
            return True
        try:
            y, x = self._parse_coordinates(move)
            if self.game.board[y][x]!=Stone.EMPTY:
                return False
            return self.game.is_within_bounds(y, x)
        except:
            return False

    def _parse_coordinates(self, move):
        '''
        Parse the coordinate input into (y, x) valid coordinates
        '''
        y, x = move.strip().split()
        y = self._label_to_coord(y)
        x = self._label_to_coord(x)
        return y, x
    
    def _label_to_coord(self, label):
        '''
        Translate an individual input coordinate into a valid one.
        The labels are given as 0, 1, 2, ... , 9, A, B, ...
        This helper translates all labels into integer coordinates
        Eg. _label_to_coord('9') --> 9
            _label_to_coord('A') --> 10
            _label_to_coord('C') --> 12
        '''
        if label.isnumeric():
            coord = int(label)
            if coord >= 10:
                raise InvalidInputException
            return int(label)
        if label.isalpha() and label >= 'A':
            diff = ord(label) - ord('A')
            if diff < 0:
                raise InvalidInputException
            return 10 + diff
        raise InvalidInputException

    def _parse_move(self, move):
        '''
        Parse an arbitrary input
        '''
        if move == 'pass':
            return move
        return self._parse_coordinates(move)
