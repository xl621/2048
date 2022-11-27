import curses
import random
from itertools import chain

# cureses is used for GUI in Terminal
# please install curses using "pip install windows-curses" if you don't have it



class Action(object):
    # game control
    UP = 'up'
    LEFT = 'left'
    DOWN = 'down'
    RIGHT = 'right'
    RESTART = 'restart'
    EXIT = 'exit'

    letter_codes = [ord(ch) for ch in 'WASDRQwasdrq']
    # w, a, s, d are for valid movements, q is for exiting the game
    # retrieve integers representing the Unicode characters    
    actions = [UP, LEFT, DOWN, RIGHT, RESTART, EXIT]
    # user's input
    actions_dict = dict(zip(letter_codes, actions * 2))
    # * 2 is used to cover upper case and lower case
    def __init__(self, stdscr):
        self.stdscr = stdscr

    def get(self):
        char = 'N'
        while char not in self.actions_dict:
            char = self.stdscr.getch()
        return self.actions_dict[char]


class Grid(object):
    def __init__(self, size):
        self.size = size
        self.cells = None
        self.score = 0
        self.reset()

    def reset(self):
        self.cells = [[0 for i in range(self.size)] for j in range(self.size)]
        self.add_random_item()
        self.add_random_item()
    # initialize with a 2D array with 0
    def add_random_item(self):
        empty_cells = [(i, j) for i in range(self.size)
                       for j in range(self.size) if self.cells[i][j] == 0]
        (i, j) = random.choice(empty_cells) #randomly pick an empty cell and insert a value
        self.cells[i][j] = 4 if random.randrange(100) >= 90 else 2
    # if the random number generated is lager than 90, insert 4 in a cell, otherwise insert 2
    def transpose(self):
        self.cells = [list(row) for row in zip(*self.cells)]
    # transpose the matrix using the zip(*) function
    def invert(self):
        self.cells = [row[::-1] for row in self.cells]

    def tighten(self, row):  # squeeze non-zero elements together
        new_row = [i for i in row if i != 0]
        new_row += [0 for i in range(len(row) - len(new_row))]
        return new_row
    # squeeze all the non-zero cells together
    def merge(self, row):
        # print("row in merge {}".format(row))
        pair = False
        new_row = []
        for i in range(len(row)):
            if pair:
                self.score += 2 * row[i]
                new_row.append(2 * row[i])
                pair = False
            else:
                if i + 1 < len(row) and row[i] == row[i+1]:
                    pair = True
                    new_row.append(0)
                else:
                    new_row.append(row[i])
                    # append the number itself when merge is not possible
        assert len(new_row) == len(row)
        # assert that the length of the new row is the same, otherwise return error
        # return new_row
        return new_row

    
    def move_row_left(self, row):
        # move rows to the left
        return self.tighten(self.merge(self.tighten(row)))
    
    # move a row to the left
    def move_left(self):
        self.cells = [self.move_row_left(row) for row in self.cells]

    def move_right(self):
        self.invert()
        self.move_left()
        self.invert()

    def move_up(self):
        self.transpose()
        self.move_left()
        self.transpose()

    def move_down(self):
        self.transpose()
        self.move_right()
        self.transpose()

    @staticmethod
    def row_can_move_left(row):
        def change(i):
            if row[i] == 0 and row[i + 1] != 0:
                return True
            if row[i] != 0 and row[i + 1] == row[i]:
                return True
            return False
        return any(change(i) for i in range(len(row) - 1))
        #if one row can be moved to the left, the other rows can be moved as well

    def can_move_left(self):
        return any(self.row_can_move_left(row) for row in self.cells)

    def can_move_right(self):
        self.invert()
        can = self.can_move_left()
        self.invert()
        return can

    def can_move_up(self):
        self.transpose()
        can = self.can_move_left()
        self.transpose()
        return can

    def can_move_down(self):
        self.transpose()
        can = self.can_move_right()
        self.transpose()
        return can


class Screen(object):
    #for the board
    help_string1 = '(W)Up (S)Down (A)Left (D)Right'
    help_string2 = '       (R)Restart (Q) Exit'
    gameover_string = '        GAME OVER'
    win_string = '              YOU WIN'

    def __init__(self, screen=None, grid=None, score=0, best_score=0, over=False, win=False):
        self.grid = grid
        self.score = grid.score
        self.over = over
        self.win = win
        self.screen = screen
        self.counter = 0

    def cast(self, string):
        self.screen.addstr(string + '\n')
    # draw the graph and display the input using Curses's addstr function

    # draw vertical lines for rows
    def draw_row(self, row):
        self.cast(''.join('|{:^5} '.format(num) if num >
                  0 else '|      ' for num in row) + '|')

    def draw(self):
        self.screen.clear()
        #clear the screen
        self.cast('SCORE: ' + str(self.score))
        for row in self.grid.cells:
            self.cast('+------' * self.grid.size + '+')
            self.draw_row(row)
        self.cast('+------' * self.grid.size + '+')
        #for the score
        if self.win:
            self.cast(self.win_string)
        else:
            if self.over:
                self.cast(self.gameover_string)
            else:
                self.cast(self.help_string1)
        self.cast(self.help_string2)
        #for prompts


class GameManager(object):
    #game status
    def __init__(self, size=4, win_num=2048):
        self.size = size #board size
        self.win_num = win_num #winning score
        self.reset() #reset the game

    def reset(self):
        self.state = 'init' #initialization
        self.win = False    #win status
        self.over = False   #lose status
        self.score = 0      #initial score
        self.grid = Grid(self.size) #create the board
        self.grid.reset()   #reset the game

    @property
    def screen(self):  # display the board
        return Screen(screen=self.stdscr, score=self.score, grid=self.grid, win=self.win, over=self.over)

    def move(self, direction): #decide if the action from user still applicable
        if self.can_move(direction):
            getattr(self.grid, 'move_' + direction)()
            # use getattr to return the value of the named attribute of grid in move_left, move_right, move_up, and move_down
            self.grid.add_random_item()
            return True
        else:
            return False

    @property
    def is_win(self): # decide the win status
        self.win = max(chain(*self.grid.cells)) >= self.win_num
        #check if any number in all cells is >= the win_num
        return self.win

    @property
    def is_over(self): # decide if the game can still be continued
        self.over = not any(self.can_move(
            move) for move in self.action.actions if move != 'restart' and move != 'exit')
        return self.over

    def can_move(self, direction):
        return getattr(self.grid, 'can_move_' + direction)()
    # use getattr to return the value of the named attribute of grid in can_move_left, can_move_right, can_move_up, and can_move_down
    def state_init(self):
        self.reset()
        return 'game'
    # for initialization
    def state_game(self): # different states of the game
        self.screen.draw()
        # display the board and score
        action = self.action.get()
        # get input from the user
        if action == Action.RESTART:
            return 'init'
        if action == Action.EXIT:
            return 'exit'
        if self.move(action):
            if self.is_over:
                return 'over'
            if self.is_win:
                return 'win'
        return 'game'

    def _restart_or_exit(self):
        self.screen.draw()
        return 'exit' if self.action.get() == Action.EXIT else 'init'
    # reset the game or exit the game
    def state_win(self):
        return self._restart_or_exit()
    # return the win state
    def state_over(self):
        return self._restart_or_exit()
    # return the lose state
    def __call__(self, stdscr):
        curses.use_default_colors()
        self.stdscr = stdscr
        self.action = Action(stdscr)
        while self.state != 'exit':
            self.state = getattr(self, 'state_' + self.state)()
            # getattr will get the value of the named attribute in state_init and state_game

if __name__ == "__main__":
    curses.wrapper(GameManager())