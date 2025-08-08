import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QGridLayout, QLabel, QVBoxLayout
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

ROWS, COLS = 10, 10

class MazeSolver(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Maze Solver (BFS, DFS, UCS, DLS, IDDFS)")
        self.resize(800, 750)

        self.buttons = []
        self.state = []
        self.start_pos = None
        self.goal_pos = None

        self.create_widgets()
        self.layout_widgets()
        self.build_grid()

    def create_widgets(self):
        self.grid_layout = QGridLayout()
        self.info_label = QLabel("Click to set Start, Goal, and Walls")
        self.info_label.setFont(QFont("Arial", 14))

        self.bfs_btn = QPushButton("Solve with BFS")
        self.dfs_btn = QPushButton("Solve with DFS")
        self.ucs_btn = QPushButton("Solve with UCS")
        self.dls_btn = QPushButton("Solve with DLS")
        self.iddfs_btn = QPushButton("Solve with IDDFS")
        self.clear_btn = QPushButton("Clear Grid")

        self.bfs_btn.clicked.connect(self.solve_bfs)
        self.dfs_btn.clicked.connect(self.solve_dfs)
        self.ucs_btn.clicked.connect(self.solve_ucs)
        self.dls_btn.clicked.connect(self.solve_dls)
        self.iddfs_btn.clicked.connect(self.solve_iddfs)
        self.clear_btn.clicked.connect(self.clear_grid)

    def layout_widgets(self):
        layout = QVBoxLayout()
        layout.addWidget(self.info_label)
        layout.addWidget(self.bfs_btn)
        layout.addWidget(self.dfs_btn)
        layout.addWidget(self.ucs_btn)
        layout.addWidget(self.dls_btn)
        layout.addWidget(self.iddfs_btn)
        layout.addWidget(self.clear_btn)
        layout.addLayout(self.grid_layout)
        self.setLayout(layout)

    def build_grid(self):
        for row in range(ROWS):
            row_buttons = []
            for col in range(COLS):
                btn = QPushButton("")
                btn.setFixedSize(40, 40)
                self.grid_layout.addWidget(btn, row, col)
                row_buttons.append(btn)
            self.buttons.append(row_buttons)

    def solve_bfs(self):
        print("Solving with BFS...")

    def solve_dfs(self):
        print("Solving with DFS...")

    def solve_ucs(self):
        print("Solving with UCS...")

    def solve_dls(self):
        print("Solving with DLS...")

    def solve_iddfs(self):
        print("Solving with IDDFS...")
import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QGridLayout, QLabel, QVBoxLayout
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from collections import deque
import heapq

ROWS, COLS = 10, 10

class MazeSolver(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Maze Solver (BFS, DFS, UCS)")
        self.resize(800, 750)

        self.buttons = []
        self.state = [[0 for _ in range(COLS)] for _ in range(ROWS)]
        self.start_pos = None
        self.goal_pos = None
        self.click_stage = 0
        self.wall_count = 0

        self.create_widgets()
        self.layout_widgets()
        self.build_grid()

    def create_widgets(self):
        self.grid_layout = QGridLayout()
        self.info_label = QLabel("Click to set Start, Goal, and Walls")
        self.info_label.setFont(QFont("Arial", 14))

        self.bfs_btn = QPushButton("Solve with BFS")
        self.dfs_btn = QPushButton("Solve with DFS")
        self.ucs_btn = QPushButton("Solve with UCS")
        self.clear_btn = QPushButton("Clear Grid")

        self.bfs_btn.clicked.connect(self.solve_bfs)
        self.dfs_btn.clicked.connect(self.solve_dfs)
        self.ucs_btn.clicked.connect(self.solve_ucs)
        self.clear_btn.clicked.connect(self.clear_grid)

    def layout_widgets(self):
        layout = QVBoxLayout()
        layout.addWidget(self.info_label)
        layout.addWidget(self.bfs_btn)
        layout.addWidget(self.dfs_btn)
        layout.addWidget(self.ucs_btn)
        layout.addWidget(self.clear_btn)
        layout.addLayout(self.grid_layout)
        self.setLayout(layout)

    def build_grid(self):
        for row in range(ROWS):
            row_buttons = []
            for col in range(COLS):
                btn = QPushButton("")
                btn.setFixedSize(40, 40)
                btn.setStyleSheet("background-color: white")
                btn.clicked.connect(lambda checked, r=row, c=col: self.cell_clicked(r, c))
                btn.setFont(QFont("Arial", 12, QFont.Weight.Bold))
                row_buttons.append(btn)
                self.grid_layout.addWidget(btn, row, col)
            self.buttons.append(row_buttons)

    def cell_clicked(self, row, col):
        if self.click_stage == 0:
            self.start_pos = (row, col)
            self.state[row][col] = 2
            self.buttons[row][col].setStyleSheet("background-color: green; color: white")
            self.buttons[row][col].setText("S")
            self.info_label.setText("Click to set Goal position.")
            self.click_stage = 1
        elif self.click_stage == 1 and (row, col) != self.start_pos:
            self.goal_pos = (row, col)
            self.state[row][col] = 3
            self.buttons[row][col].setStyleSheet("background-color: red; color: white")
            self.buttons[row][col].setText("G")
            self.info_label.setText("Click to place walls.")
            self.click_stage = 2
        elif self.click_stage >= 2:
            if (row, col) == self.start_pos or (row, col) == self.goal_pos:
                return
            if self.state[row][col] != 1:
                self.state[row][col] = 1
                self.buttons[row][col].setStyleSheet("background-color: black; color: white")
                self.buttons[row][col].setText("")
                self.wall_count += 1
                self.info_label.setText(f"Walls placed: {self.wall_count}")

    def get_neighbors(self, pos):
        r, c = pos
        for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < ROWS and 0 <= nc < COLS and self.state[nr][nc] != 1:
                yield (nr, nc)

    def draw_path_with_steps(self, parent, algorithm_name):
        path = []
        current = self.goal_pos
        while current != self.start_pos:
            path.append(current)
            current = parent[current]
        path.append(self.start_pos)
        path.reverse()

        # Reset all except walls first
        for r in range(ROWS):
            for c in range(COLS):
                if self.state[r][c] == 0:
                    self.buttons[r][c].setStyleSheet("background-color: white; color: black")
                    self.buttons[r][c].setText("")

        # Show start and goal clearly again
        sr, sc = self.start_pos
        gr, gc = self.goal_pos
        self.buttons[sr][sc].setStyleSheet("background-color: green; color: white")
        self.buttons[sr][sc].setText("S")
        self.buttons[gr][gc].setStyleSheet("background-color: red; color: white")
        self.buttons[gr][gc].setText("G")

        # Number the path steps starting from 1
        for step_num, (r, c) in enumerate(path):
            if (r, c) != self.start_pos and (r, c) != self.goal_pos:
                self.buttons[r][c].setStyleSheet("background-color: lightblue; color: black")
                self.buttons[r][c].setText(str(step_num))

        steps = len(path) - 1  # excluding start cell
        self.info_label.setText(
            f"Path found with {algorithm_name}! Steps: {steps} | Walls: {self.wall_count}"
        )

    def solve_bfs(self):
        self.clear_path()
        if not self.start_pos or not self.goal_pos:
            self.info_label.setText("Please set both Start and Goal positions.")
            return

        queue = deque([self.start_pos])
        visited = {self.start_pos}
        parent = {}

        while queue:
            current = queue.popleft()
            if current == self.goal_pos:
                self.draw_path_with_steps(parent, "BFS")
                return
            for neighbor in self.get_neighbors(current):
                if neighbor not in visited:
                    visited.add(neighbor)
                    parent[neighbor] = current
                    queue.append(neighbor)

        self.info_label.setText("No path found with BFS.")

    def solve_dfs(self):
        self.clear_path()
        if not self.start_pos or not self.goal_pos:
            self.info_label.setText("Please set both Start and Goal positions.")
            return

        stack = [self.start_pos]
        visited = {self.start_pos}
        parent = {}

        while stack:
            current = stack.pop()
            if current == self.goal_pos:
                self.draw_path_with_steps(parent, "DFS")
                return
            for neighbor in self.get_neighbors(current):
                if neighbor not in visited:
                    visited.add(neighbor)
                    parent[neighbor] = current
                    stack.append(neighbor)

        self.info_label.setText("No path found with DFS.")

    def solve_ucs(self):
        self.clear_path()
        if not self.start_pos or not self.goal_pos:
            self.info_label.setText("Please set both Start and Goal positions.")
            return

        heap = [(0, self.start_pos)]
        visited = set()
        parent = {}

        while heap:
            cost, current = heapq.heappop(heap)
            if current == self.goal_pos:
                self.draw_path_with_steps(parent, "UCS")
                return
            if current in visited:
                continue
            visited.add(current)
            for neighbor in self.get_neighbors(current):
                if neighbor not in visited:
                    heapq.heappush(heap, (cost + 1, neighbor))
                    if neighbor not in parent:
                        parent[neighbor] = current

        self.info_label.setText("No path found with UCS.")

    def clear_path(self):
        # Clear all path and reset buttons that are not walls/start/goal
        for r in range(ROWS):
            for c in range(COLS):
                if self.state[r][c] == 0:
                    self.buttons[r][c].setStyleSheet("background-color: white; color: black")
                    self.buttons[r][c].setText("")

    def clear_grid(self):
        self.state = [[0 for _ in range(COLS)] for _ in range(ROWS)]
        self.start_pos = None
        self.goal_pos = None
        self.click_stage = 0
        self.wall_count = 0
        self.info_label.setText("Click to set Start, Goal, and Walls")
        for r in range(ROWS):
            for c in range(COLS):
                self.buttons[r][c].setStyleSheet("background-color: white; color: black")
                self.buttons[r][c].setText("")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MazeSolver()
    window.show()
    sys.exit(app.exec())

    def clear_grid(self):
        print("Clearing grid...")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MazeSolver()
    window.show()
    sys.exit(app.exec())
