import sys
import heapq
import itertools

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QComboBox, QLabel, QGraphicsView, QGraphicsScene,
    QGraphicsRectItem, QGraphicsSimpleTextItem
)
from PyQt6.QtGui import QColor, QFont, QPainter
from PyQt6.QtCore import QRectF, Qt, QTimer

CELL_SIZE = 25
GRID_ROWS = 20
GRID_COLS = 30

pq_counter = itertools.count()

class GridCells(QGraphicsRectItem):
    """
    Represents an individual cell in the grid for pathfinding visualization.
    Inherits from QGraphicsRectItem to be drawn in a QGraphicsScene.
    """
    def __init__(self, row, col, parent=None):
        super().__init__(0, 0, CELL_SIZE, CELL_SIZE, parent)
        self.row = row
        self.col = col
        self.setPos(col * CELL_SIZE, row * CELL_SIZE)
        self.setBrush(QColor('white'))
        self.setPen(QColor('black'))
        self.type = 'empty'
        self.text_item = QGraphicsSimpleTextItem('', self)
        self.text_item.setPos(3, 3)
        self.text_item.setFont(QFont("Arial", 8))
        self.text_item.setBrush(QColor("black"))
        self.setAcceptHoverEvents(True)
        self.hover_text = None

    def set_type(self, cell_type):
        """
        Sets the type of the cell and updates its color.
        """
        color_map = {
            'empty': 'white',
            'wall': 'black',
            'start': 'green',
            'goal': 'red',
            'visited': 'lightblue',
            'path': 'yellow'
        }
        self.type = cell_type
        self.setBrush(QColor(color_map.get(cell_type, 'white')))
        if cell_type not in ('start', 'goal'):
            self.text_item.setText("")

    def setText(self, text):
        self.text_item.setText(text)

    def hoverEnterEvent(self, event):
        if self.type in ('empty', 'start', 'goal', 'wall'):
            if self.hover_text is None or self.hover_text.scene() is None:
                self.hover_text = QGraphicsSimpleTextItem(f"({self.row}, {self.col})", self)
                self.hover_text.setFont(QFont("Arial", 10))
                self.hover_text.setBrush(QColor("blue"))
                self.hover_text.setPos(self.boundingRect().topRight().x() + 5, self.boundingRect().topRight().y() - 15)
                self.scene().addItem(self.hover_text)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        """
        Handles mouse hover leave event to remove cell coordinates.
        """
        if self.hover_text and self.hover_text.scene() is not None:
            self.scene().removeItem(self.hover_text)
            self.hover_text = None
        super().hoverLeaveEvent(event)

    def set_step_label(self, text):
        """
        Sets a step number label on the cell.
        """
        self.text_item.setText(str(text))


class Grid:
    """
    Manages the grid of cells, including initialization, resetting, and cell access.
    """
    def __init__(self, scene):
        self.scene = scene
        self.cells = []
        for r in range(GRID_ROWS):
            row_cells = []
            for c in range(GRID_COLS):
                cell = GridCells(r, c)
                self.scene.addItem(cell)
                row_cells.append(cell)
            self.cells.append(row_cells)
        self.start = None
        self.goal = None

    def reset(self):
        """
        Resets all cells to their default 'empty' state.
        """
        for row in self.cells:
            for cell in row:
                cell.set_type('empty')
                cell.setText('')
        self.start = None
        self.goal = None

    def clear_all(self):
        """
        Clears all cells to 'empty' and removes start/goal nodes.
        """
        for row in self.cells:
            for cell in row:
                cell.set_type('empty')
                cell.setText("")
        self.start = None
        self.goal = None

    def get_cell(self, row, col):
        """
        Returns the cell at the given row and column.
        """
        if 0 <= row < GRID_ROWS and 0 <= col < GRID_COLS:
            return self.cells[row][col]
        return None

    def get_neighbors(self, cell):
        """
        Returns a list of valid neighboring cells (up, down, left, right).
        """
        neighbors_list = []
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        for dr, dc in directions:
            new_row, new_col = cell.row + dr, cell.col + dc
            if 0 <= new_row < GRID_ROWS and 0 <= new_col < GRID_COLS and \
                self.cells[new_row][new_col].type != 'wall':
                neighbors_list.append(self.cells[new_row][new_col])
        return neighbors_list

class CustomGraphicsView(QGraphicsView):
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.pathfinding_app = None

    def mousePressEvent(self, event):
        """
        Handles mouse press events on the QGraphicsView.
        Delegates the handling to the PathfindingApp.
        """
        if self.pathfinding_app:
            self.pathfinding_app.handle_view_mouse_press(event)
        super().mousePressEvent(event)

class PathfindingApp(QMainWindow):
    """
    Main application window for the pathfinding visualizer.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pathfinding Visualizer")
        self.setGeometry(100, 100, CELL_SIZE * GRID_COLS + 250, CELL_SIZE * GRID_ROWS + 100)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)
        self.top_bar_layout = QHBoxLayout()

        self.scene = QGraphicsScene()

        self.view = CustomGraphicsView(self.scene)
        self.view.pathfinding_app = self
        self.layout.addWidget(self.view)

        self.grid = Grid(self.scene)

        self.algo_label = QLabel("Algorithm:")
        self.top_bar_layout.addWidget(self.algo_label)
        self.algo_combo = QComboBox()
        self.algo_combo.addItem("A* Algorithm")
        self.algo_combo.addItem("Greedy Best-First Search")
        self.top_bar_layout.addWidget(self.algo_combo)

        self.run_button = QPushButton("Run Algorithm")
        self.run_button.clicked.connect(self.run_algorithm)
        self.top_bar_layout.addWidget(self.run_button)

        self.reset_button = QPushButton("Reset Grid")
        self.reset_button.clicked.connect(self.grid.reset)
        self.top_bar_layout.addWidget(self.reset_button)

        self.clear_button = QPushButton("Clear All")
        self.clear_button.clicked.connect(self.grid.clear_all)
        self.top_bar_layout.addWidget(self.clear_button)

        self.step_label = QLabel("Steps: 0")
        self.top_bar_layout.addWidget(self.step_label)

        self.layout.addLayout(self.top_bar_layout)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.step_visualization)
        self.path = []
        self.steps = []
        self.step_counter = 0
        self.algorithm_running = False

        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.view.setSceneRect(QRectF(0, 0, CELL_SIZE * GRID_COLS, CELL_SIZE * GRID_ROWS))

    def handle_view_mouse_press(self, event):
        if event.type() == event.type().MouseButtonPress:
            pos = self.view.mapToScene(event.pos())
            col = int(pos.x() // CELL_SIZE)
            row = int(pos.y() // CELL_SIZE)

            if 0 <= row < GRID_ROWS and 0 <= col < GRID_COLS:
                clicked_cell = self.grid.get_cell(row, col)

                if self.algorithm_running:
                    self.clear_visualization_steps()

                if event.button() == Qt.MouseButton.LeftButton:
                    if self.grid.start is None:
                        if clicked_cell.type == 'wall':
                            clicked_cell.set_type('empty')
                        clicked_cell.set_type('start')
                        self.grid.start = clicked_cell
                    elif self.grid.goal is None and clicked_cell != self.grid.start:
                        if clicked_cell.type == 'wall':
                            clicked_cell.set_type('empty')
                        clicked_cell.set_type('goal')
                        self.grid.goal = clicked_cell
                    elif clicked_cell != self.grid.start and clicked_cell != self.grid.goal:
                        if clicked_cell.type == 'wall':
                            clicked_cell.set_type('empty')
                        else:
                            clicked_cell.set_type('wall')
                elif event.button() == Qt.MouseButton.RightButton:
                    if clicked_cell == self.grid.start:
                        self.grid.start = None
                    elif clicked_cell == self.grid.goal:
                        self.grid.goal = None
                    clicked_cell.set_type('empty')
                    clicked_cell.setText("") 

    def run_algorithm(self):
        """
        Executes the selected pathfinding algorithm.
        """
        if self.grid.start is None or self.grid.goal is None:
            self.statusBar().showMessage("Please set start and goal nodes!", 3000)
            return

        self.clear_visualization_steps()
        self.algorithm_running = True
        self.timer.stop()

        algorithm = self.algo_combo.currentText()
        came_from = {}
        cost_so_far = {}

        if algorithm == "A* Algorithm":
            self.steps, came_from = self.a_star_search(self.grid.start, self.grid.goal)
        elif algorithm == "Greedy Best-First Search":
            self.steps, came_from = self.greedy_best_first_search(self.grid.start, self.grid.goal)
        else:
            self.statusBar().showMessage("Unknown algorithm selected!", 3000)
            self.algorithm_running = False
            return

        if self.grid.goal in came_from:
            self.path = self.reconstruct_path(self.grid.start, self.grid.goal, came_from)
            if self.grid.goal in self.steps:
                self.steps.remove(self.grid.goal)
        else:
            self.path = []
            self.statusBar().showMessage("No path found!", 3000)

        self.step_counter = 0
        if self.steps or self.path:
            self.timer.start(50)
        else:
            self.statusBar().showMessage("No steps to visualize (start/goal might be adjacent or no path).", 3000)
            self.algorithm_running = False


    def clear_visualization_steps(self):
        """
        Clears previous visualization steps and resets cell colors.
        """
        self.timer.stop()
        self.step_counter = 0
        self.step_label.setText("Steps: 0")
        for row in self.grid.cells:
            for cell in row:
                if cell.type in ('visited', 'path'):
                    cell.set_type('empty')
                if cell.type not in ('start', 'goal'):
                    cell.setText("")
        self.path = []
        self.steps = []
        self.algorithm_running = False

    def step_visualization(self):
        """
        Visualizes the pathfinding process step by step.
        """
        if self.step_counter < len(self.steps):
            current_cell = self.steps[self.step_counter]
            if current_cell.type != 'start' and current_cell.type != 'goal':
                current_cell.set_type('visited')
            current_cell.set_step_label(self.step_counter)
            self.step_counter += 1
            self.step_label.setText(f"Steps: {self.step_counter}")
        elif len(self.path) > 0:
            current_path_cell = self.path.pop(0)
            if current_path_cell.type != 'start' and current_path_cell.type != 'goal':
                current_path_cell.set_type('path')
        else:
            self.timer.stop()
            self.statusBar().showMessage("Pathfinding visualization complete!", 3000)
            self.algorithm_running = False

    def heuristic(self, a, b):
        return abs(a.row - b.row) + abs(a.col - b.col)

    def a_star_search(self, start, goal):
        frontier = []

        heapq.heappush(frontier, (0, next(pq_counter), start))
        came_from = {start: None}
        cost_so_far = {start: 0}
        visited_order = []

        while frontier:
            current_priority, _, current = heapq.heappop(frontier)

            if current == goal:
                break

            if current != start and current != goal:
                visited_order.append(current)

            for next_node in self.grid.get_neighbors(current):
                new_cost = cost_so_far[current] + 1
                if next_node not in cost_so_far or new_cost < cost_so_far[next_node]:
                    cost_so_far[next_node] = new_cost
                    priority = new_cost + self.heuristic(goal, next_node)
                    heapq.heappush(frontier, (priority, next(pq_counter), next_node))
                    came_from[next_node] = current
        return visited_order, came_from

    def greedy_best_first_search(self, start, goal):
        """
        Implements the Greedy Best-First Search algorithm.
        Returns a list of visited nodes and a dictionary of came_from pointers.
        """
        frontier = []
        heapq.heappush(frontier, (0, next(pq_counter), start))
        came_from = {start: None}
        visited_order = []

        while frontier:
            current_priority, _, current = heapq.heappop(frontier)

            if current == goal:
                break

            if current != start and current != goal:
                visited_order.append(current)

            for next_node in self.grid.get_neighbors(current):
                if next_node not in came_from:
                    priority = self.heuristic(goal, next_node)
                    heapq.heappush(frontier, (priority, next(pq_counter), next_node))
                    came_from[next_node] = current
        return visited_order, came_from

    def reconstruct_path(self, start, goal, came_from):
        """
        Reconstructs the path from goal to start using the came_from dictionary.
        """
        current = goal
        path = []
        while current != start:
            if current is None:
                break
            path.insert(0, current)
            current = came_from.get(current)
        return path

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PathfindingApp()
    window.show()
    sys.exit(app.exec())