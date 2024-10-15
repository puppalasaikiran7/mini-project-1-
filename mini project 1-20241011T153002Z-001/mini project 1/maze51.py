from tkinter import *
from tkinter import font
from tkinter import messagebox
from functools import partial
from operator import attrgetter
import webbrowser
import numpy
import random
import math
import os

"""
@author Nikos Kanargias
E-mail: nkana@tee.gr
@version 5.1

The software solves and visualizes the robot motion planning problem,
by implementing variants of DFS, BFS and A* algorithms, as described
by E. Keravnou in her book: "Artificial Intelligence and Expert Systems",
Hellenic Open University,  Patra 2000 (in Greek)
as well as the Greedy search algorithm, as a special case of A*.

The software also implements Dijkstra's algorithm,
as just described in the relevant article in Wikipedia.
http://en.wikipedia.org/wiki/Dijkstra%27s_algorithm

The superiority of  A* and Dijkstra's algorithms against the other three becomes obvious.

The user can change the number of the grid cells, indicating
the desired number of rows and columns.

The user can add as many obstacles he/she wants, as he/she
would "paint" free curves with a drawing program.

Individual obstacles can be removed by clicking them.

The position of the robot and/or the target can be changed by dragging with the mouse.

Jump from search in "Step-by-Step" way to "Animation" way and vice versa is done
by pressing the corresponding button, even when the search is in progress.

The speed of a search can be changed, even if the search is in progress.
It is sufficient to place the slider "Speed" in the new desired position
and then press the "Animation" button.

The application considers that the robot itself has some volume.
Therefore it can’t move diagonally to a free cell passing between two obstacles
adjacent to one apex.

When 'Step-by-Step' or 'Animation' search is underway it is not possible to change the position of obstacles,
robot and target, as well as the search algorithm.

When 'Real-Time' search is underway the position of obstacles, robot and target can be changed.

Drawing of arrows to predecessors, when requested, is performed only at the end of the search.
"""


class Maze51:

    class CreateToolTip(object):
        """
        Helper class that creates a tooltip for a given widget
        """
        # from https://stackoverflow.com/questions/3221956/what-is-the-simplest-way-to-make-tooltips-in-tkinter
        def __init__(self, widget, text='widget info'):
            self.waittime = 500  # milliseconds
            self.wraplength = 180  # pixels
            self.widget = widget
            self.text = text
            self.widget.bind("<Enter>", self.enter)
            self.widget.bind("<Leave>", self.leave)
            self.widget.bind("<ButtonPress>", self.leave)
            self._id = None
            self.tw = None

        def enter(self, event=None):
            self.schedule()

        def leave(self, event=None):
            self.unschedule()
            self.hidetip()

        def schedule(self):
            self.unschedule()
            self._id = self.widget.after(self.waittime, self.showtip)

        def unschedule(self):
            _id = self._id
            self._id = None
            if _id:
                self.widget.after_cancel(_id)

        def showtip(self, event=None):
            x, y, cx, cy = self.widget.bbox("insert")
            x += self.widget.winfo_rootx() + 25
            y += self.widget.winfo_rooty() + 20
            # creates a toplevel window
            self.tw = Toplevel(self.widget)
            # Leaves only the label and removes the app window
            self.tw.wm_overrideredirect(True)
            self.tw.wm_geometry("+%d+%d" % (x, y))
            label = Label(self.tw, text=self.text, justify='left', background="#ffffff",
                          relief='solid', borderwidth=1, wraplength=self.wraplength)
            label.pack(ipadx=1)

        def hidetip(self):
            tw = self.tw
            self.tw = None
            if tw:
                tw.destroy()

    class MyMaze(object):
        """
        Helper class that creates a random, perfect (without cycles) maze
        """
        # The code of the class is an adaptation, with the original commentary, of the answer given
        # by user DoubleMx2 on August 25, 2013 to a question posted by user nazar_art at stackoverflow.com:
        # http://stackoverflow.com/questions/18396364/maze-generation-arrayindexoutofboundsexception

        def __init__(self, x_dimension, y_dimension):
            self.dimensionX = x_dimension              # dimension of maze
            self.dimensionY = y_dimension
            self.gridDimensionX = x_dimension * 2 + 1  # dimension of output grid
            self.gridDimensionY = y_dimension * 2 + 1
            # output grid
            self.mazeGrid = [[' ' for y in range(self.gridDimensionY)] for x in range(self.gridDimensionX)]
            # 2d array of Cells
            self.cells = [[self.Cell(x, y, False) for y in range(self.dimensionY)] for x in range(self.dimensionX)]
            self.generate_maze()
            self.update_grid()

        class Cell(object):
            """
            inner class to represent a cell
            """
            def __init__(self, x, y, is_wall=True):
                self.neighbors = []  # cells this cell is connected to
                self.open = True     # if true, has yet to be used in generation
                self.x = x           # coordinates
                self.y = y
                self.wall = is_wall  # impassable cell

            def add_neighbor(self, other):
                """
                add a neighbor to this cell, and this cell as a neighbor to the other
                """
                if other not in self.neighbors:  # avoid duplicates
                    self.neighbors.append(other)
                if self not in other.neighbors:  # avoid duplicates
                    other.neighbors.append(self)

            def is_cell_below_neighbor(self):
                """
                used in update_grid()
                """
                return self.__class__(self.x, self.y + 1) in self.neighbors

            def is_cell_right_neighbor(self):
                """
                used in update_grid()
                """
                return self.__class__(self.x + 1, self.y) in self.neighbors

            def __eq__(self, other):
                """
                useful Cell equivalence
                """
                if isinstance(other, self.__class__):
                    return self.x == other.x and self.y == other.y
                else:
                    return False

        def generate_maze(self):
            """
            generate the maze from upper left (In computing the y increases down often)
            """
            start_at = self.get_cell(0, 0)
            start_at.open = False  # indicate cell closed for generation
            cells = [start_at]
            while cells:
                # this is to reduce but not completely eliminate the number
                # of long twisting halls with short easy to detect branches
                # which results in easy mazes
                if random.randint(0, 9) == 0:
                    cell = cells.pop(random.randint(0, cells.__len__()) - 1)
                else:
                    cell = cells.pop(cells.__len__() - 1)
                # for collection
                neighbors = []
                # cells that could potentially be neighbors
                potential_neighbors = [self.get_cell(cell.x + 1, cell.y), self.get_cell(cell.x, cell.y + 1),
                                       self.get_cell(cell.x - 1, cell.y), self.get_cell(cell.x, cell.y - 1)]
                for other in potential_neighbors:
                    # skip if outside, is a wall or is not opened
                    if other is None or other.wall or not other.open:
                        continue
                    neighbors.append(other)
                if not neighbors:
                    continue
                # get random cell
                selected = neighbors[random.randint(0, neighbors.__len__()) - 1]
                # add as neighbor
                selected.open = False  # indicate cell closed for generation
                cell.add_neighbor(selected)
                cells.append(cell)
                cells.append(selected)

        def get_cell(self, x, y):
            """
            used to get a Cell at x, y; returns None out of bounds
            """
            if x < 0 or y < 0:
                return None
            try:
                return self.cells[x][y]
            except IndexError:  # catch out of bounds
                return None

        def update_grid(self):
            """
            draw the maze
            """
            back_char = ' '
            wall_char = 'X'
            cell_char = ' '
            # fill background
            for x in range(self.gridDimensionX):
                for y in range(self.gridDimensionY):
                    self.mazeGrid[x][y] = back_char
            # build walls
            for x in range(self.gridDimensionX):
                for y in range(self.gridDimensionY):
                    if x % 2 == 0 or y % 2 == 0:
                        self.mazeGrid[x][y] = wall_char
            # make meaningful representation
            for x in range(self.dimensionX):
                for y in range(self.dimensionY):
                    current = self.get_cell(x, y)
                    grid_x = x * 2 + 1
                    grid_y = y * 2 + 1
                    self.mazeGrid[grid_x][grid_y] = cell_char
                    if current.is_cell_below_neighbor():
                        self.mazeGrid[grid_x][grid_y + 1] = cell_char
                    if current.is_cell_right_neighbor():
                        self.mazeGrid[grid_x + 1][grid_y] = cell_char

    class Cell(object):
        """
        Helper class that represents the cell of the grid
        """

        def __init__(self, row, col):
            self.row = row  # the row number of the cell(row 0 is the top)
            self.col = col  # the column number of the cell (column 0 is the left)
            self.g = 0      # the value of the function g of A* and Greedy algorithms
            self.h = 0      # the value of the function h of A* and Greedy algorithms
            self.f = 0      # the value of the function f of A* and Greedy algorithms
            # the distance of the cell from the initial position of the robot
            # Ie the label that updates the Dijkstra's algorithm
            self.dist = 0
            # Each state corresponds to a cell
            # and each state has a predecessor which
            # stored in this variable
            self.prev = self.__class__

        def __eq__(self, other):
            """
            useful Cell equivalence
            """
            if isinstance(other, self.__class__):
                return self.row == other.row and self.col == other.col
            else:
                return False

    #######################################
    #                                     #
    #      Constants of Maze42 class      #
    #                                     #
    #######################################
    INFINITY = sys.maxsize  # The representation of the infinite
    EMPTY = 0       # empty cell
    OBST = 1        # cell with obstacle
    ROBOT = 2       # the position of the robot
    TARGET = 3      # the position of the target
    FRONTIER = 4    # cells that form the frontier (OPEN SET)
    CLOSED = 5      # cells that form the CLOSED SET
    ROUTE = 6       # cells that form the robot-to-target path

    MSG_DRAW_AND_SELECT = "\"Paint\" obstacles, then click 'Real-Time' or 'Step-by-Step' or 'Animation'"
    MSG_SELECT_STEP_BY_STEP_ETC = "Click 'Step-by-Step' or 'Animation' or 'Clear'"
    MSG_NO_SOLUTION = "There is no path to the target !!!"

    def __init__(self, maze):
        """
        Constructor
        """
        self.center(maze)

        self.rows = 41                             # the number of rows of the grid
        self.columns = 41                          # the number of columns of the grid
        self.square_size = int(500/self.rows)      # the cell size in pixels
        self.arrow_size = int(self.square_size/2)  # the size of the tips of the arrow pointing the predecessor cell

        self.openSet = []    # the OPEN SET
        self.closedSet = []  # the CLOSED SET
        self.graph = []      # the set of vertices of the graph to be explored by Dijkstra's algorithm

        self.robotStart = self.Cell(self.rows - 2, 1)    # the initial position of the robot
        self.targetPos = self.Cell(1, self.columns - 2)  # the position of the target

        self.grid = [[]]            # the grid
        self.realTime = False       # Solution is displayed instantly
        self.found = False          # flag that the goal was found
        self.searching = False      # flag that the search is in progress
        self.endOfSearch = False    # flag that the search came to an end
        self.animation = False      # flag that the animation is running
        self.delay = 500            # time delay of animation (in msec)
        self.expanded = 0           # the number of nodes that have been expanded
        self.selected_algo = "DFS"  # DFS is initially selected

        self.array = numpy.array([0] * (83 * 83))
        self.cur_row = self.cur_col = self.cur_val = 0
        app_highlight_font = font.Font(app, family='Helvetica', size=10, weight='bold')

        ##########################################
        #                                        #
        #   the widgets of the user interface    #
        #                                        #
        ##########################################
        self.message = Label(app, text=self.MSG_DRAW_AND_SELECT, width=55, anchor='center',
                             font=('Helvetica', 12), fg="BLUE")
        self.message.place(x=5, y=510)

        rows_lbl = Label(app, text="# of rows (5-83):", width=16, anchor='e', font=("Helvetica", 9))
        rows_lbl.place(x=530, y=5)

        validate_rows_cmd = (app.register(self.validate_rows), '%P')
        invalid_rows_cmd = (app.register(self.invalid_rows))

        self.rows_var = StringVar()
        self.rows_var.set(41)
        self.rowsSpinner = Spinbox(app, width=3, from_=5, to=83, textvariable=self.rows_var, validate='focus',
                                   validatecommand=validate_rows_cmd, invalidcommand=invalid_rows_cmd)
        self.rowsSpinner.place(x=652, y=5)

        cols_lbl = Label(app, text="# of columns (5-83):", width=16, anchor='e', font=("Helvetica", 9))
        cols_lbl.place(x=530, y=35)

        validate_cols_cmd = (app.register(self.validate_cols), '%P')
        invalid_cols_cmd = (app.register(self.invalid_cols))

        self.cols_var = StringVar()
        self.cols_var.set(41)
        self.colsSpinner = Spinbox(app, width=3, from_=5, to=83, textvariable=self.cols_var, validate='focus',
                                   validatecommand=validate_cols_cmd, invalidcommand=invalid_cols_cmd)
        self.colsSpinner.place(x=652, y=35)

        self.buttons = list()
        buttons_tool_tips = ("Clears and redraws the grid according to the given rows and columns",
                             "Creates a random maze",
                             "First click: clears search, Second click: clears obstacles",
                             "Position of obstacles, robot and target can be changed when search is underway",
                             "The search is performed step-by-step for every click",
                             "The search is performed automatically")
        for i, action in enumerate(("New grid", "Maze", "Clear", "Real-Time", "Step-by-Step", "Animation")):
            btn = Button(app, text=action,  width=20, font=app_highlight_font,  bg="light grey",
                         command=partial(self.select_action, action))
            btn.place(x=515, y=65+30*i)
            self.CreateToolTip(btn, buttons_tool_tips[i])
            self.buttons.append(btn)

        time_delay = Label(app, text="Delay (msec)", width=27, anchor='center', font=("Helvetica", 8))
        time_delay.place(x=515, y=243)
        slider_value = IntVar()
        slider_value.set(500)
        self.slider = Scale(app, orient=HORIZONTAL, length=165, width=10, from_=0, to=1000,
                            showvalue=1, variable=slider_value,)
        self.slider.place(x=515, y=260)
        self.CreateToolTip(self.slider, "Regulates the delay for each step (0 to 1000 msec)")

        self.frame = LabelFrame(app, text="Algorithms", width=170, height=100)
        self.frame.place(x=515, y=300)
        self.radio_buttons = list()
        radio_buttons_tool_tips = ("Depth First Search algorithm",
                                   "Breadth First Search algorithm",
                                   "A* algorithm",
                                   "Greedy search algorithm",
                                   "Dijkstra's algorithm")
        for i, algorithm in enumerate(("DFS", "BFS", "A*", "Greedy", "Dijkstra")):
            btn = Radiobutton(self.frame, text=algorithm,  font=app_highlight_font, value=i + 1,
                              command=partial(self.select_algo, algorithm))
            btn.place(x=10 if i % 2 == 0 else 90, y=int(i/2)*25)
            self.CreateToolTip(btn, radio_buttons_tool_tips[i])
            btn.deselect()
            self.radio_buttons.append(btn)
        self.radio_buttons[0].select()

        self.diagonal = IntVar()
        self.diagonalBtn = Checkbutton(app, text="Diagonal movements", font=app_highlight_font,
                                       variable=self.diagonal)
        self.diagonalBtn.place(x=515, y=405)
        self.CreateToolTip(self.diagonalBtn, "Diagonal movements are also allowed")

        self.drawArrows = IntVar()
        self.drawArrowsBtn = Checkbutton(app, text="Arrows to predecessors", font=app_highlight_font,
                                         variable=self.drawArrows)
        self.drawArrowsBtn.place(x=515, y=430)
        self.CreateToolTip(self.drawArrowsBtn, "Draw arrows to predecessors")

        memo_colors = ("RED", "GREEN", "BLUE", "CYAN")
        for i, memo in enumerate(("Robot", "Target", "Frontier", "Closed set")):
            label = Label(app, text=memo,  width=8, anchor='center', fg=memo_colors[i], font=("Helvetica", 11))
            label.place(x=515 if i % 2 == 0 else 605, y=460+int(i/2)*20)

        self.about_button = Button(app, text='About Maze', width=20, font=app_highlight_font, bg="light grey",
                                   command=self.about_click)
        self.about_button.place(x=515, y=505)

        self.canvas = Canvas(app, bd=0, highlightthickness=0)
        self.canvas.bind("<Button-1>", self.left_click)
        self.canvas.bind("<B1-Motion>", self.drag)

        self.initialize_grid(False)

    def validate_rows(self, entry):
        """
        Validates entry in rowsSpinner

        :param entry: the value entered by the user
        :return:      True, if entry is valid
        """
        try:
            value = int(entry)
            valid = value in range(5, 84)
        except ValueError:
            valid = False
        if not valid:
            app.bell()
            # The following line is due to user PRMoureu of stackoverflow. See:
            # https://stackoverflow.com/questions/46861236/widget-validation-in-tkinter/46863849?noredirect=1#comment80675412_46863849
            self.rowsSpinner.after_idle(lambda: self.rowsSpinner.config(validate='focusout'))
        return valid

    def invalid_rows(self):
        """
        Sets default value to rowsSpinner in case of invalid entry
        """
        self.rows_var.set(41)

    def validate_cols(self, entry):
        """
        Validates entry in colsSpinner

        :param entry: the value entered by the user
        :return:      True, if entry is valid
        """
        try:
            value = int(entry)
            valid = value in range(5, 84)
        except ValueError:
            valid = False
        if not valid:
            app.bell()
            self.colsSpinner.after_idle(lambda: self.colsSpinner.config(validate='focusout'))
        return valid

    def invalid_cols(self):
        """
        Sets default value to colsSpinner in case of invalid entry
        """
        self.cols_var.set(41)

    def select_action(self, action):
        if action == "New grid":
            self.reset_click()
        elif action == "Maze":
            self.maze_click()
        elif action == "Clear":
            self.clear_click()
        elif action == "Real-Time":
            self.real_time_click()
        elif action == "Step-by-Step":
            self.step_by_step_click()
        elif action == "Animation":
            self.animation_click()

    def select_algo(self, algorithm):
        self.selected_algo = algorithm

    def left_click(self, event):
        """
        Handles clicks of left mouse button as we add or remove obstacles
        """
        row = int(event.y/self.square_size)
        col = int(event.x/self.square_size)
        if row in range(self.rows) and col in range(self.columns):
            if True if self.realTime else (not self.found and not self.searching):
                if self.realTime:
                    self.fill_grid()
                self.cur_row = row
                self.cur_col = col
                self.cur_val = self.grid[row][col]
                if self.cur_val == self.EMPTY:
                    self.grid[row][col] = self.OBST
                    self.paint_cell(row, col, "BLACK")
                if self.cur_val == self.OBST:
                    self.grid[row][col] = self.EMPTY
                    self.paint_cell(row, col, "WHITE")
                if self.realTime and self.selected_algo == "Dijkstra":
                    self.initialize_dijkstra()
            if self.realTime:
                self.real_Time_action()

    def drag(self, event):
        """
        Handles mouse movements as we "paint" obstacles or move the robot and/or target.
        """
        row = int(event.y/self.square_size)
        col = int(event.x/self.square_size)
        if row in range(self.rows) and col in range(self.columns):
            if True if self.realTime else (not self.found and not self.searching):
                if self.realTime:
                    self.fill_grid()
                if self.Cell(row, col) != self.Cell(self.cur_row, self.cur_col) and\
                        self.cur_val in [self.ROBOT, self.TARGET]:
                    new_val = self.grid[row][col]
                    if new_val == self.EMPTY:
                        self.grid[row][col] = self.cur_val
                        if self.cur_val == self.ROBOT:
                            self.grid[self.robotStart.row][self.robotStart.col] = self.EMPTY
                            self.paint_cell(self.robotStart.row, self.robotStart.col, "WHITE")
                            self.robotStart.row = row
                            self.robotStart.col = col
                            self.grid[self.robotStart.row][self.robotStart.col] = self.ROBOT
                            self.paint_cell(self.robotStart.row, self.robotStart.col, "RED")
                        else:
                            self.grid[self.targetPos.row][self.targetPos.col] = self.EMPTY
                            self.paint_cell(self.targetPos.row, self.targetPos.col, "WHITE")
                            self.targetPos.row = row
                            self.targetPos.col = col
                            self.grid[self.targetPos.row][self.targetPos.col] = self.TARGET
                            self.paint_cell(self.targetPos.row, self.targetPos.col, "GREEN")
                        self.cur_row = row
                        self.cur_col = col
                        self.cur_val = self.grid[row][col]
                elif self.grid[row][col] != self.ROBOT and self.grid[row][col] != self.TARGET:
                    self.grid[row][col] = self.OBST
                    self.paint_cell(row, col, "BLACK")
                if self.realTime and self.selected_algo == "Dijkstra":
                    self.initialize_dijkstra()
            if self.realTime:
                self.real_Time_action()

    def initialize_grid(self, make_maze):
        """
        Creates a new clean grid or a new maze

        :param make_maze: flag that indicates the creation of a random maze
        """
        self.rows = int(self.rowsSpinner.get())
        self.columns = int(self.colsSpinner.get())
        if make_maze and self.rows % 2 == 0:
            self.rows -= 1
        if make_maze and self.columns % 2 == 0:
            self.columns -= 1
        self.square_size = int(500/(self.rows if self.rows > self.columns else self.columns))
        self.arrow_size = int(self.square_size/2)
        self.grid = self.array[:self.rows*self.columns]
        self.grid = self.grid.reshape(self.rows, self.columns)
        self.canvas.configure(width=self.columns*self.square_size+1, height=self.rows*self.square_size+1)
        self.canvas.place(x=10, y=10)
        self.canvas.create_rectangle(0, 0, self.columns*self.square_size+1,
                                     self.rows*self.square_size+1, width=0, fill="DARK GREY")
        for r in list(range(self.rows)):
            for c in list(range(self.columns)):
                self.grid[r][c] = self.EMPTY
        self.robotStart = self.Cell(self.rows-2, 1)
        self.targetPos = self.Cell(1, self.columns-2)
        self.fill_grid()
        if make_maze:
            maze = self.MyMaze(int(self.rows/2), int(self.columns/2))
            for x in range(maze.gridDimensionX):
                for y in range(maze.gridDimensionY):
                    if maze.mazeGrid[x][y] == 'X':  # maze.wall_char:
                        self.grid[x][y] = self.OBST
        self.repaint()

    def fill_grid(self):
        """
        Gives initial values ​​for the cells in the grid.
        """
        # With the first click on button 'Clear' clears the data
        # of any search was performed (Frontier, Closed Set, Route)
        # and leaves intact the obstacles and the robot and target positions
        # in order to be able to run another algorithm
        # with the same data.
        # With the second click removes any obstacles also.
        if self.searching or self.endOfSearch:
            for r in list(range(self.rows)):
                for c in list(range(self.columns)):
                    if self.grid[r][c] in [self.FRONTIER, self.CLOSED, self.ROUTE]:
                        self.grid[r][c] = self.EMPTY
                    if self.grid[r][c] == self.ROBOT:
                        self.robotStart = self.Cell(r, c)
            self.searching = False
        else:
            for r in list(range(self.rows)):
                for c in list(range(self.columns)):
                    self.grid[r][c] = self.EMPTY
            self.robotStart = self.Cell(self.rows-2, 1)
            self.targetPos = self.Cell(1, self.columns-2)
        if self.selected_algo in ["A*", "Greedy"]:
            self.robotStart.g = 0
            self.robotStart.h = 0
            self.robotStart.f = 0
        self.expanded = 0
        self.found = False
        self.searching = False
        self.endOfSearch = False

        self.openSet.clear()
        self.closedSet.clear()
        self.openSet = [self.robotStart]
        self.closedSet = []

        self.grid[self.targetPos.row][self.targetPos.col] = self.TARGET
        self.grid[self.robotStart.row][self.robotStart.col] = self.ROBOT
        self.message.configure(text=self.MSG_DRAW_AND_SELECT)

        self.repaint()

    def repaint(self):
        """
        Repaints the grid
        """
        color = ""
        for r in list(range(self.rows)):
            for c in list(range(self.columns)):
                if self.grid[r][c] == self.EMPTY:
                    color = "WHITE"
                elif self.grid[r][c] == self.ROBOT:
                    color = "RED"
                elif self.grid[r][c] == self.TARGET:
                    color = "GREEN"
                elif self.grid[r][c] == self.OBST:
                    color = "BLACK"
                elif self.grid[r][c] == self.FRONTIER:
                    color = "BLUE"
                elif self.grid[r][c] == self.CLOSED:
                    color = "CYAN"
                elif self.grid[r][c] == self.ROUTE:
                    color = "YELLOW"
                self.paint_cell(r, c, color)

    def paint_cell(self, row, col, color):
        """
        Paints a particular cell

        :param row:   # the row of the cell
        :param col:   # the column of the cell
        :param color: # the color of the cell
        """
        self.canvas.create_rectangle(1 + col * self.square_size, 1 + row * self.square_size,
                                     1 + (col + 1) * self.square_size - 1, 1 + (row + 1) * self.square_size - 1,
                                     width=0, fill=color)

    def reset_click(self):
        """
        Action performed when user clicks "New grid" button
        """
        self.animation = False
        self.realTime = False
        for but in self.buttons:
            but.configure(state="normal")
        self.buttons[3].configure(fg="BLACK")  # Real-Time button
        self.slider.configure(state="normal")
        for but in self.radio_buttons:
            but.configure(state="normal")
        self.diagonalBtn.configure(state="normal")
        self.drawArrowsBtn.configure(state="normal")
        self.initialize_grid(False)

    def maze_click(self):
        """
        Action performed when user clicks "Maze" button
        """
        self.animation = False
        self.realTime = False
        for but in self.buttons:
            but.configure(state="normal")
        self.buttons[3].configure(fg="BLACK")  # Real-Time button
        self.slider.configure(state="normal")
        for but in self.radio_buttons:
            but.configure(state="normal")
        self.diagonalBtn.configure(state="normal")
        self.drawArrowsBtn.configure(state="normal")
        self.initialize_grid(True)

    def clear_click(self):
        """
        Action performed when user clicks "Clear" button
        """
        self.animation = False
        self.realTime = False
        for but in self.buttons:
            but.configure(state="normal")
        self.buttons[3].configure(fg="BLACK")  # Real-Time button
        self.slider.configure(state="normal")
        for but in self.radio_buttons:
            but.configure(state="normal")
        self.diagonalBtn.configure(state="normal")
        self.drawArrowsBtn.configure(state="normal")
        self.fill_grid()

    def real_time_click(self):
        """
        Action performed when user clicks "Real-Time" button
        """
        if self.realTime:
            return
        self.realTime = True
        self.searching = True
        # The Dijkstra's initialization should be done just before the
        # start of search, because obstacles must be in place.
        if self.selected_algo == "Dijkstra":
            self.initialize_dijkstra()
        self.buttons[3].configure(fg="RED") # Real-Time button
        self.slider.configure(state="disabled")
        for but in self.radio_buttons:
            but.configure(state="disabled")
        self.diagonalBtn.configure(state="disabled")
        self.drawArrowsBtn.configure(state="disabled")
        self.real_Time_action()

    def real_Time_action(self):
        """
        Action performed during real-time search
        """
        while not self.endOfSearch:
            self.check_termination()

    def step_by_step_click(self):
        """
        Action performed when user clicks "Step-by-Step" button
        """
        if self.found or self.endOfSearch:
            return
        if not self.searching and self.selected_algo == "Dijkstra":
            self.initialize_dijkstra()
        self.animation = False
        self.searching = True
        self.message.configure(text=self.MSG_SELECT_STEP_BY_STEP_ETC)
        self.buttons[3].configure(state="disabled") # Real-Time button
        for but in self.radio_buttons:
            but.configure(state="disabled")
        self.diagonalBtn.configure(state="disabled")
        self.drawArrowsBtn.configure(state="disabled")
        self.check_termination()

    def animation_click(self):
        """
        Action performed when user clicks "Animation" button
        """
        self.animation = True
        if not self.searching and self.selected_algo == "Dijkstra":
            self.initialize_dijkstra()
        self.searching = True
        self.message.configure(text=self.MSG_SELECT_STEP_BY_STEP_ETC)
        self.buttons[3].configure(state="disabled") # Real-Time button
        for but in self.radio_buttons:
            but.configure(state="disabled")
        self.diagonalBtn.configure(state="disabled")
        self.drawArrowsBtn.configure(state="disabled")
        self.delay = self.slider.get()
        self.animation_action()

    def animation_action(self):
        """
        The action periodically performed during searching in animation mode
        """
        if self.animation:
            self.check_termination()
            if self.endOfSearch:
                return
            self.canvas.after(self.delay, self.animation_action)

    def about_click(self):
        """
        Action performed when user clicks "About Maze" button
        """
        about_box = Toplevel(master=app)
        about_box.title("")
        about_box.geometry("340x160")
        about_box.resizable(False, False)
        self.center(about_box)
        about_box.transient(app)  # only one window in the task bar
        about_box.grab_set()      # modal

        title = Label(about_box, text="Maze", width=20, anchor='center', fg='SANDY BROWN', font=("Helvetica", 20))
        title.place(x=0, y=0)
        version = Label(about_box, text="Version: 5.1", width=35, anchor='center', font=("Helvetica", 11, 'bold'))
        version.place(x=0, y=35)
        programmer = Label(about_box, text="Designer: Nikos Kanargias", width=35, anchor='center',
                           font=("Helvetica", 12))
        programmer.place(x=0, y=60)
        email = Label(about_box, text="E-mail: nkana@tee.gr", width=40, anchor='center', font=("Helvetica", 10))
        email.place(x=0, y=80)
        source_code = Label(about_box, text="Code and documentation", fg="blue", cursor="hand2", width=35,
                            anchor='center',
                            font=("Helvetica", 12))
        f = font.Font(source_code, source_code.cget("font"))
        f.configure(underline=True)
        source_code.configure(font=f)
        source_code.place(x=0, y=100)
        source_code.bind("<Button-1>", self.source_code_callback)
        self.CreateToolTip(source_code, "Click this link to retrieve code and documentation from DropBox")
        video = Label(about_box, text="Watch demo video on YouTube", fg="blue", cursor="hand2", width=35,
                      anchor='center')
        video.configure(font=f)
        video.place(x=0, y=125)
        video.bind("<Button-1>", self.video_callback)
        self.CreateToolTip(video, "Click this link to watch a demo video on YouTube")

    def check_termination(self):
        """
        Checks if search is completed
        """
        # Here we decide whether we can continue the search or not.
        # In the case of DFS, BFS, A* and Greedy algorithms
        # here we have the second step:
        # 2. If OPEN SET = [], then terminate. There is no solution.
        if (self.selected_algo == "Dijkstra" and not self.graph) or\
                self.selected_algo != "Dijkstra" and not self.openSet:
            self.endOfSearch = True
            self.grid[self.robotStart.row][self.robotStart.col] = self.ROBOT
            self.message.configure(text=self.MSG_NO_SOLUTION)
            self.buttons[4].configure(state="disabled")     # Step-by-Step button
            self.buttons[5].configure(state="disabled")     # Animation button
            self.slider.configure(state="disabled")
            self.repaint()
            if self.drawArrows.get():
                self.draw_arrows()
        else:
            self.expand_node()
            if self.found:
                self.endOfSearch = True
                self.plot_route()
                self.buttons[4].configure(state="disabled")  # Step-by-Step button
                self.buttons[5].configure(state="disabled")  # Animation button
                self.slider.configure(state="disabled")

    def expand_node(self):
        """
        Expands a node and creates his successors
        """
        # Dijkstra's algorithm to handle separately
        if self.selected_algo == "Dijkstra":
            # 11: while Q is not empty:
            if not self.graph:
                return
            # 12:  u := vertex in Q (graph) with smallest distance in dist[] ;
            # 13:  remove u from Q (graph);
            u = self.graph.pop(0)
            # Add vertex u in closed set
            self.closedSet.append(u)
            # If target has been found ...
            if u == self.targetPos:
                self.found = True
                return
            # Counts nodes that have expanded.
            self.expanded += 1
            # Update the color of the cell
            self.grid[u.row][u.col] = self.CLOSED
            # paint the cell
            self.paint_cell(u.row, u.col, "CYAN")
            # 14: if dist[u] = infinity:
            if u.dist == self.INFINITY:
                # ... then there is no solution.
                # 15: break;
                return
                # 16: end if
            # Create the neighbors of u
            neighbors = self.create_successors(u, False)
            # 18: for each neighbor v of u:
            for v in neighbors:
                # 20: alt := dist[u] + dist_between(u, v) ;
                alt = u.dist + self.dist_between(u, v)
                # 21: if alt < dist[v]:
                if alt < v.dist:
                    # 22: dist[v] := alt ;
                    v.dist = alt
                    # 23: previous[v] := u ;
                    v.prev = u
                    # Update the color of the cell
                    self.grid[v.row][v.col] = self.FRONTIER
                    # paint the cell
                    self.paint_cell(v.row, v.col, "BLUE")
                    # 24: decrease-key v in Q;
                    # (sort list of nodes with respect to dist)
                    self.graph.sort(key=attrgetter("dist"))
        # The handling of the other four algorithms
        else:
            if self.selected_algo in ["DFS", "BFS"]:
                # Here is the 3rd step of the algorithms DFS and BFS
                # 3. Remove the first state, Si, from OPEN SET ...
                current = self.openSet.pop(0)
            else:
                # Here is the 3rd step of the algorithms A* and Greedy
                # 3. Remove the first state, Si, from OPEN SET,
                # for which f(Si) ≤ f(Sj) for all other
                # open states Sj  ...
                # (sort first OPEN SET list with respect to 'f')
                self.openSet.sort(key=attrgetter("f"))
                current = self.openSet.pop(0)
            # ... and add it to CLOSED SET.
            self.closedSet.insert(0, current)
            # Update the color of the cell
            self.grid[current.row][current.col] = self.CLOSED
            # paint the cell
            self.paint_cell(current.row, current.col, "CYAN")
            # If the selected node is the target ...
            if current == self.targetPos:
                # ... then terminate etc
                last = self.targetPos
                last.prev = current.prev
                self.closedSet.append(last)
                self.found = True
                return
            # Count nodes that have been expanded.
            self.expanded += 1
            # Here is the 4rd step of the algorithms
            # 4. Create the successors of Si, based on actions
            #    that can be implemented on Si.
            #    Each successor has a pointer to the Si, as its predecessor.
            #    In the case of DFS and BFS algorithms, successors should not
            #    belong neither to the OPEN SET nor the CLOSED SET.
            successors = self.create_successors(current, False)
            # Here is the 5th step of the algorithms
            # 5. For each successor of Si, ...
            for cell in successors:
                # ... if we are running DFS ...
                if self.selected_algo == "DFS":
                    # ... add the successor at the beginning of the list OPEN SET
                    self.openSet.insert(0, cell)
                    # Update the color of the cell
                    self.grid[cell.row][cell.col] = self.FRONTIER
                    # paint the cell
                    self.paint_cell(cell.row, cell.col, "BLUE")
                # ... if we are runnig BFS ...
                elif self.selected_algo == "BFS":
                    # ... add the successor at the end of the list OPEN SET
                    self.openSet.append(cell)
                    # Update the color of the cell
                    self.grid[cell.row][cell.col] = self.FRONTIER
                    # paint the cell
                    self.paint_cell(cell.row, cell.col, "BLUE")
                # ... if we are running A* or Greedy algorithms (step 5 of A* algorithm) ...
                elif self.selected_algo in ["A*", "Greedy"]:
                    # ... calculate the value f(Sj) ...
                    dxg = current.col - cell.col
                    dyg = current.row - cell.row
                    dxh = self.targetPos.col - cell.col
                    dyh = self.targetPos.row - cell.row
                    if self.diagonal.get():
                        # with diagonal movements, calculate the Euclidean distance
                        if self.selected_algo == "Greedy":
                            # especially for the Greedy ...
                            cell.g = 0
                        else:
                            cell.g = current.g + math.sqrt(dxg*dxg + dyg*dyg)
                        cell.h = math.sqrt(dxh*dxh + dyh*dyh)
                    else:
                        # without diagonal movements, calculate the Manhattan distance
                        if self.selected_algo == "Greedy":
                            # especially for the Greedy ...
                            cell.g = 0
                        else:
                            cell.g = current.g + abs(dxg) + abs(dyg)
                        cell.h = abs(dxh) + abs(dyh)
                    cell.f = cell.g+cell.h
                    # ... If Sj is neither in the OPEN SET nor in the CLOSED SET states ...
                    if cell not in self.openSet and cell not in self.closedSet:
                        # ... then add Sj in the OPEN SET ...
                        # ... evaluated as f(Sj)
                        self.openSet.append(cell)
                        # Update the color of the cell
                        self.grid[cell.row][cell.col] = self.FRONTIER
                        # paint the cell
                        self.paint_cell(cell.row, cell.col, "BLUE")
                    # Else ...
                    else:
                        # ... if already belongs to the OPEN SET, then ...
                        if cell in self.openSet:
                            open_index = self.openSet.index(cell)
                            # ... compare the new value assessment with the old one.
                            # If old <= new ...
                            if self.openSet[open_index].f <= cell.f:
                                # ... then eject the new node with state Sj.
                                # (ie do nothing for this node).
                                pass
                            # Else, ...
                            else:
                                # ... remove the element (Sj, old) from the list
                                # to which it belongs ...
                                self.openSet.pop(open_index)
                                # ... and add the item (Sj, new) to the OPEN SET.
                                self.openSet.append(cell)
                                # Update the color of the cell
                                self.grid[cell.row][cell.col] = self.FRONTIER
                                # paint the cell
                                self.paint_cell(cell.row, cell.col, "BLUE")
                        # ... if already belongs to the CLOSED SET, then ...
                        elif cell in self.closedSet:
                            closed_index = self.closedSet.index(cell)
                            # ... compare the new value assessment with the old one.
                            # If old <= new ...
                            if self.closedSet[closed_index].f <= cell.f:
                                # ... then eject the new node with state Sj.
                                # (ie do nothing for this node).
                                pass
                            # Else, ...
                            else:
                                # ... remove the element (Sj, old) from the list
                                # to which it belongs ...
                                self.closedSet.pop(closed_index)
                                # ... and add the item (Sj, new) to the OPEN SET.
                                self.openSet.append(cell)
                                # Update the color of the cell
                                self.grid[cell.row][cell.col] = self.FRONTIER
                                # paint the cell
                                self.paint_cell(cell.row, cell.col, "BLUE")

    def create_successors(self, current, make_connected):
        """
        Creates the successors of a state/cell

        :param current:        the cell for which we ask successors
        :param make_connected: flag that indicates that we are interested only on the coordinates
                               of cells and not on the label 'dist' (concerns only Dijkstra's)
        :return:               the successors of the cell as a list
        """
        r = current.row
        c = current.col
        # We create an empty list for the successors of the current cell.
        temp = []
        # With diagonal movements priority is:
        # 1: Up 2: Up-right 3: Right 4: Down-right
        # 5: Down 6: Down-left 7: Left 8: Up-left

        # Without diagonal movements the priority is:
        # 1: Up 2: Right 3: Down 4: Left

        # If not at the topmost limit of the grid
        # and the up-side cell is not an obstacle
        # and (only in the case are not running the A* or Greedy)
        # not already belongs neither to the OPEN SET nor to the CLOSED SET ...
        if r > 0 and self.grid[r-1][c] != self.OBST and\
                (self.selected_algo in ["A*", "Greedy", "Dijkstra"] or
                 (self.selected_algo in ["DFS", "BFS"]
                 and not self.Cell(r-1, c) in self.openSet and not self.Cell(r-1, c) in self.closedSet)):
            cell = self.Cell(r-1, c)
            # In the case of Dijkstra's algorithm we can not append to
            # the list of successors the "naked" cell we have just created.
            # The cell must be accompanied by the label 'dist',
            # so we need to track it down through the list 'graph'
            # and then copy it back to the list of successors.
            # The flag makeConnected is necessary to be able
            # the present method create_succesors() to collaborate
            # with the method find_connected_component(), which creates
            # the connected component when Dijkstra's initializes.
            if self.selected_algo == "Dijkstra":
                if make_connected:
                    temp.append(cell)
                elif cell in self.graph:
                    graph_index = self.graph.index(cell)
                    temp.append(self.graph[graph_index])
            else:
                # ... update the pointer of the up-side cell so it points the current one ...
                cell.prev = current
                # ... and add the up-side cell to the successors of the current one.
                temp.append(cell)

        if self.diagonal.get():
            # If we are not even at the topmost nor at the rightmost border of the grid
            # and the up-right-side cell is not an obstacle
            # and one of the upper side or right side cells are not obstacles
            # (because it is not reasonable to allow the robot to pass through a "slot")
            # and (only in the case are not running the A* or Greedy)
            # not already belongs neither to the OPEN SET nor CLOSED SET ...
            if r > 0 and c < self.columns-1 and self.grid[r-1][c+1] != self.OBST and \
                    (self.grid[r-1][c] != self.OBST or self.grid[r][c+1] != self.OBST) and \
                    (self.selected_algo in ["A*", "Greedy", "Dijkstra"] or
                     (self.selected_algo in ["DFS", "BFS"]
                     and not self.Cell(r-1, c+1) in self.openSet and not self.Cell(r-1, c+1) in self.closedSet)):
                cell = self.Cell(r-1, c+1)
                if self.selected_algo == "Dijkstra":
                    if make_connected:
                        temp.append(cell)
                    elif cell in self.graph:
                        graph_index = self.graph.index(cell)
                        temp.append(self.graph[graph_index])
                else:
                    # ... update the pointer of the up-right-side cell so it points the current one ...
                    cell.prev = current
                    # ... and add the up-right-side cell to the successors of the current one.
                    temp.append(cell)

        # If not at the rightmost limit of the grid
        # and the right-side cell is not an obstacle ...
        # and (only in the case are not running the A* or Greedy)
        # not already belongs neither to the OPEN SET nor to the CLOSED SET ...
        if c < self.columns-1 and self.grid[r][c+1] != self.OBST and\
                (self.selected_algo in ["A*", "Greedy", "Dijkstra"] or
                 (self.selected_algo in ["DFS", "BFS"]
                 and not self.Cell(r, c+1) in self.openSet and not self.Cell(r, c+1) in self.closedSet)):
            cell = self.Cell(r, c+1)
            if self.selected_algo == "Dijkstra":
                if make_connected:
                    temp.append(cell)
                elif cell in self.graph:
                    graph_index = self.graph.index(cell)
                    temp.append(self.graph[graph_index])
            else:
                # ... update the pointer of the right-side cell so it points the current one ...
                cell.prev = current
                # ... and add the right-side cell to the successors of the current one.
                temp.append(cell)

        if self.diagonal.get():
            # If we are not even at the lowermost nor at the rightmost border of the grid
            # and the down-right-side cell is not an obstacle
            # and one of the down-side or right-side cells are not obstacles
            # and (only in the case are not running the A* or Greedy)
            # not already belongs neither to the OPEN SET nor to the CLOSED SET ...
            if r < self.rows-1 and c < self.columns-1 and self.grid[r+1][c+1] != self.OBST and \
                    (self.grid[r+1][c] != self.OBST or self.grid[r][c+1] != self.OBST) and \
                    (self.selected_algo in ["A*", "Greedy", "Dijkstra"] or
                     (self.selected_algo in ["DFS", "BFS"]
                     and not self.Cell(r+1, c+1) in self.openSet and not self.Cell(r+1, c+1) in self.closedSet)):
                cell = self.Cell(r+1, c+1)
                if self.selected_algo == "Dijkstra":
                    if make_connected:
                        temp.append(cell)
                    elif cell in self.graph:
                        graph_index = self.graph.index(cell)
                        temp.append(self.graph[graph_index])
                else:
                    # ... update the pointer of the downr-right-side cell so it points the current one ...
                    cell.prev = current
                    # ... and add the down-right-side cell to the successors of the current one.
                    temp.append(cell)

        # If not at the lowermost limit of the grid
        # and the down-side cell is not an obstacle
        # and (only in the case are not running the A* or Greedy)
        # not already belongs neither to the OPEN SET nor to the CLOSED SET ...
        if r < self.rows-1 and self.grid[r+1][c] != self.OBST and \
                (self.selected_algo in ["A*", "Greedy", "Dijkstra"] or
                 (self.selected_algo in ["DFS", "BFS"]
                 and not self.Cell(r+1, c) in self.openSet and not self.Cell(r+1, c) in self.closedSet)):
            cell = self.Cell(r+1, c)
            if self.selected_algo == "Dijkstra":
                if make_connected:
                    temp.append(cell)
                elif cell in self.graph:
                    graph_index = self.graph.index(cell)
                    temp.append(self.graph[graph_index])
            else:
                # ... update the pointer of the down-side cell so it points the current one ...
                cell.prev = current
                # ... and add the down-side cell to the successors of the current one.
                temp.append(cell)

        if self.diagonal.get():
            # If we are not even at the lowermost nor at the leftmost border of the grid
            # and the down-left-side cell is not an obstacle
            # and one of the down-side or left-side cells are not obstacles
            # and (only in the case are not running the A* or Greedy)
            # not already belongs neither to the OPEN SET nor to the CLOSED SET ...
            if r < self.rows-1 and c > 0 and self.grid[r+1][c-1] != self.OBST and \
                    (self.grid[r+1][c] != self.OBST or self.grid[r][c-1] != self.OBST) and \
                    (self.selected_algo in ["A*", "Greedy", "Dijkstra"] or
                     (self.selected_algo in ["DFS", "BFS"]
                     and not self.Cell(r+1, c-1) in self.openSet and not self.Cell(r+1, c-1) in self.closedSet)):
                cell = self.Cell(r+1, c-1)
                if self.selected_algo == "Dijkstra":
                    if make_connected:
                        temp.append(cell)
                    elif cell in self.graph:
                        graph_index = self.graph.index(cell)
                        temp.append(self.graph[graph_index])
                else:
                    # ... update the pointer of the down-left-side cell so it points the current one ...
                    cell.prev = current
                    # ... and add the down-left-side cell to the successors of the current one.
                    temp.append(cell)

        # If not at the leftmost limit of the grid
        # and the left-side cell is not an obstacle
        # and (only in the case are not running the A* or Greedy)
        # not already belongs neither to the OPEN SET nor to the CLOSED SET ...
        if c > 0 and self.grid[r][c-1] != self.OBST and \
                (self.selected_algo in ["A*", "Greedy", "Dijkstra"] or
                 (self.selected_algo in ["DFS", "BFS"]
                 and not self.Cell(r, c-1) in self.openSet and not self.Cell(r, c-1) in self.closedSet)):
            cell = self.Cell(r, c-1)
            if self.selected_algo == "Dijkstra":
                if make_connected:
                    temp.append(cell)
                elif cell in self.graph:
                    graph_index = self.graph.index(cell)
                    temp.append(self.graph[graph_index])
            else:
                # ... update the pointer of the left-side cell so it points the current one ...
                cell.prev = current
                # ... and add the left-side cell to the successors of the current one.
                temp.append(cell)

        if self.diagonal.get():
            # If we are not even at the topmost nor at the leftmost border of the grid
            # and the up-left-side cell is not an obstacle
            # and one of the up-side or left-side cells are not obstacles
            # and (only in the case are not running the A* or Greedy)
            # not already belongs neither to the OPEN SET nor to the CLOSED SET ...
            if r > 0 and c > 0 and self.grid[r-1][c-1] != self.OBST and \
                    (self.grid[r-1][c] != self.OBST or self.grid[r][c-1] != self.OBST) and \
                    (self.selected_algo in ["A*", "Greedy", "Dijkstra"] or
                     (self.selected_algo in ["DFS", "BFS"]
                     and not self.Cell(r-1, c-1) in self.openSet and not self.Cell(r-1, c-1) in self.closedSet)):
                cell = self.Cell(r-1, c-1)
                if self.selected_algo == "Dijkstra":
                    if make_connected:
                        temp.append(cell)
                    elif cell in self.graph:
                        graph_index = self.graph.index(cell)
                        temp.append(self.graph[graph_index])
                else:
                    # ... update the pointer of the up-left-side cell so it points the current one ...
                    cell.prev = current
                    # ... and add the up-left-side cell to the successors of the current one.
                    temp.append(cell)

        # When DFS algorithm is in use, cells are added one by one at the beginning of the
        # OPEN SET list. Because of this, we must reverse the order of successors formed,
        # so the successor corresponding to the highest priority, to be placed the first in the list.
        # For the Greedy, A* and Dijkstra's no issue, because the list is sorted
        # according to 'f' or 'dist' before extracting the first element of.
        if self.selected_algo == "DFS":
            return reversed(temp)
        else:
            return temp

    def dist_between(self, u, v):
        """
        Returns the distance between two cells

        :param u: the first cell
        :param v: the other cell
        :return:  the distance between the cells u and v
        """
        dx = u.col - v.col
        dy = u.row - v.row
        if self.diagonal.get():
            # with diagonal movements calculate the Euclidean distance
            return math.sqrt(dx*dx + dy*dy)
        else:
            # without diagonal movements calculate the Manhattan distance
            return abs(dx) + abs(dy)

    def plot_route(self):
        """
        Calculates the path from the target to the initial position of the robot,
        counts the corresponding steps and measures the distance traveled.
        """
        self.repaint()
        self.searching = False
        steps = 0
        distance = 0.0
        index = self.closedSet.index(self.targetPos)
        cur = self.closedSet[index]
        self.grid[cur.row][cur.col] = self.TARGET
        self.paint_cell(cur.row, cur.col, "GREEN")
        while cur != self.robotStart:
            steps += 1
            if self.diagonal.get():
                dx = cur.col - cur.prev.col
                dy = cur.row - cur.prev.row
                distance += math.sqrt(dx*dx + dy*dy)
            else:
                distance += 1
            cur = cur.prev
            self.grid[cur.row][cur.col] = self.ROUTE
            self.paint_cell(cur.row, cur.col, "YELLOW")

        self.grid[self.robotStart.row][self.robotStart.col] = self.ROBOT
        self.paint_cell(self.robotStart.row, self.robotStart.col, "RED")

        if self.drawArrows.get():
            self.draw_arrows()

        msg = "Nodes expanded: {0}, Steps: {1}, Distance: {2:.3f}".format(self.expanded, steps, distance)
        self.message.configure(text=msg)

    def find_connected_component(self, v):
        """
        Appends to the list containing the nodes of the graph only
        the cells belonging to the same connected component with node v.

        :param v: the starting node
        """
        # This is a Breadth First Search of the graph starting from node v.
        stack = [v]
        self.graph.append(v)
        while stack:
            v = stack.pop()
            successors = self.create_successors(v, True)
            for c in successors:
                if c not in self.graph:
                    stack.append(c)
                    self.graph.append(c)

    def initialize_dijkstra(self):
        """
        Initialization of Dijkstra's algorithm
        """
        # When one thinks of Wikipedia pseudocode, observe that the
        # algorithm is still looking for his target while there are still
        # nodes in the queue Q.
        # Only when we run out of queue and the target has not been found,
        # can answer that there is no solution.
        # As is known, the algorithm models the problem as a connected graph
        # It is obvious that no solution exists only when the graph is not
        # connected and the target is in a different connected component
        # of this initial position of the robot
        # To be thus possible negative response from the algorithm,
        # should search be made ONLY in the coherent component to which the
        # initial position of the robot belongs.

        # First create the connected component
        # to which the initial position of the robot belongs.
        self.graph.clear()
        self.find_connected_component(self.robotStart)
        # Here is the initialization of Dijkstra's algorithm
        # 2: for each vertex v in Graph;
        for v in self.graph:
            # 3: dist[v] := infinity ;
            v.dist = self.INFINITY
            # 5: previous[v] := undefined ;
            v.prev = None
        # 8: dist[source] := 0;
        self.graph[self.graph.index(self.robotStart)].dist = 0
        # 9: Q := the set of all nodes in Graph;
        # Instead of the variable Q we will use the list
        # 'graph' itself, which has already been initialised.

        # Sorts the list of nodes with respect to 'dist'.
        self.graph.sort(key=attrgetter("dist"))
        # Initializes the list of closed nodes
        self.closedSet.clear()

    def draw_arrows(self):
        """
        Draws the arrows to predecessors
        """
        # We draw black arrows from each open or closed state to its predecessor.
        for r in range(self.rows):
            for c in range(self.columns):
                tail = head = cell = self.Cell(r, c)
                # If the current cell is an open state, or is a closed state
                # but not the initial position of the robot
                if self.grid[r][c] in [self.FRONTIER, self.CLOSED] and not cell == self.robotStart:
                    # The tail of the arrow is the current cell, while
                    # the arrowhead is the predecessor cell.
                    if self.grid[r][c] == self.FRONTIER:
                        if self.selected_algo == "Dijkstra":
                            tail = self.graph[self.graph.index(cell)]
                            head = tail.prev
                        else:
                            tail = self.openSet[self.openSet.index(cell)]
                            head = tail.prev
                    elif self.grid[r][c] == self.CLOSED:
                        tail = self.closedSet[self.closedSet.index(cell)]
                        head = tail.prev

                    self.draw_arrow(tail, head, self.arrow_size, "BLACK", 2 if self.square_size >= 25 else 1)

        if self.found:
            # We draw red arrows along the path from robotStart to targetPos.
            # index = self.closedSet.index(self.targetPos)
            cur = self.closedSet[self.closedSet.index(self.targetPos)]
            while cur != self.robotStart:
                head = cur
                cur = cur.prev
                tail = cur
                self.draw_arrow(tail, head, self.arrow_size, "RED", 2 if self.square_size >= 25 else 1)

    def draw_arrow(self, tail, head, a, color, width):
        """
        Draws an arrow from center of tail cell to center of head cell

        :param tail:   the tail of the arrow
        :param head:   the head of the arrow
        :param a:      size of arrow tips
        :param color:  color of the arrow
        :param width:  thickness of the lines
        """
        # The coordinates of the center of the tail cell
        x1 = 1 + tail.col * self.square_size + self.square_size / 2
        y1 = 1 + tail.row * self.square_size + self.square_size / 2
        # The coordinates of the center of the head cell
        x2 = 1 + head.col * self.square_size + self.square_size / 2
        y2 = 1 + head.row * self.square_size + self.square_size / 2

        sin20 = math.sin(20*math.pi/180)
        cos20 = math.cos(20*math.pi/180)
        sin25 = math.sin(25*math.pi/180)
        cos25 = math.cos(25*math.pi/180)
        u3 = v3 = u4 = v4 = 0

        if x1 == x2 and y1 > y2:  # up
            u3 = x2 - a*sin20
            v3 = y2 + a*cos20
            u4 = x2 + a*sin20
            v4 = v3
        elif x1 < x2 and y1 > y2:  # up-right
            u3 = x2 - a*cos25
            v3 = y2 + a*sin25
            u4 = x2 - a*sin25
            v4 = y2 + a*cos25
        elif x1 < x2 and y1 == y2:  # right
            u3 = x2 - a*cos20
            v3 = y2 - a*sin20
            u4 = u3
            v4 = y2 + a*sin20
        elif x1 < x2 and y1 < y2:  # righr-down
            u3 = x2 - a*cos25
            v3 = y2 - a*sin25
            u4 = x2 - a*sin25
            v4 = y2 - a*cos25
        elif x1 == x2 and y1 < y2:  # down
            u3 = x2 - a*sin20
            v3 = y2 - a*cos20
            u4 = x2 + a*sin20
            v4 = v3
        elif x1 > x2 and y1 < y2:  # left-down
            u3 = x2 + a*sin25
            v3 = y2 - a*cos25
            u4 = x2 + a*cos25
            v4 = y2 - a*sin25
        elif x1 > x2 and y1 == y2:  # left
            u3 = x2 + a*cos20
            v3 = y2 - a*sin20
            u4 = u3
            v4 = y2 + a*sin20
        elif x1 > x2 and y1 > y2:  # left-up
            u3 = x2 + a*sin25
            v3 = y2 + a*cos25
            u4 = x2 + a*cos25
            v4 = y2 + a*sin25

        self.canvas.create_line(x1, y1, x2, y2, fill=color, width=width)
        self.canvas.create_line(x2, y2, u3, v3, fill=color, width=width)
        self.canvas.create_line(x2, y2, u4, v4, fill=color, width=width)

    @staticmethod
    def center(window):
        """
        Places a window at the center of the screen
        """
        window.update_idletasks()
        w = window.winfo_screenwidth()
        h = window.winfo_screenheight()
        size = tuple(int(_) for _ in window.geometry().split('+')[0].split('x'))
        x = w / 2 - size[0] / 2
        y = h / 2 - size[1] / 2
        window.geometry("%dx%d+%d+%d" % (size + (x, y)))

    @staticmethod
    def source_code_callback(self):
        webbrowser.open_new(r"https://goo.gl/tRaLfe")

    @staticmethod
    def video_callback(self):
        webbrowser.open_new(r"https://youtu.be/7GLqy61X2oU")


def on_closing():
    if messagebox.askokcancel("Quit", "Do you want to quit?"):
        os._exit(0)


if __name__ == '__main__':
    app = Tk()
    app.protocol("WM_DELETE_WINDOW", on_closing)
    app.title("Maze 5.1")
    app.geometry("693x545")
    app.resizable(False, False)
    Maze51(app)
    app.mainloop()
