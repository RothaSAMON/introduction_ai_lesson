import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QGridLayout, QLabel, QVBoxLayout, QHBoxLayout
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from collections import deque

ROWS, COLS = 10, 10

class MazeSolver(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Maze Solver (BFS, DFS, UCS, DLS, IDDFS)")
        self.resize(500, 450)

        self.buttons = []
        self.state = [['empty' for _ in range(COLS)] for _ in range(ROWS)]
        self.start_pos = None
        self.goal_pos = None
        self.setting_mode = 'start'

        self.create_widgets()
        self.layout_widgets()
        self.build_grid()

    def create_widgets(self):
        self.grid_layout = QGridLayout()
        self.info_label = QLabel("Click to set Start, Goal, and Walls")
        self.info_label.setFont(QFont("Arial", 14))

        # Create solve buttons
        self.bfs_btn = QPushButton("Solve with BFS")
        self.dfs_btn = QPushButton("Solve with DFS")
        self.ucs_btn = QPushButton("Solve with UCS")
        self.dls_btn = QPushButton("Solve with DLS")
        self.iddfs_btn = QPushButton("Solve with IDDFS")
        self.clear_btn = QPushButton("Clear Grid")

        # Connect button signals
        self.bfs_btn.clicked.connect(self.solve_bfs)
        self.dfs_btn.clicked.connect(self.solve_dfs)
        self.ucs_btn.clicked.connect(self.solve_ucs)
        self.dls_btn.clicked.connect(self.solve_dls)
        self.iddfs_btn.clicked.connect(self.solve_iddfs)
        self.clear_btn.clicked.connect(self.clear_grid)

    def layout_widgets(self):
        # Main vertical layout
        main_layout = QVBoxLayout()

        # Add info label
        main_layout.addWidget(self.info_label)

        # Add grid layout
        main_layout.addLayout(self.grid_layout)

        # Create a horizontal layout for solve buttons
        solve_buttons_layout = QHBoxLayout()
        solve_buttons_layout.addWidget(self.bfs_btn)
        solve_buttons_layout.addWidget(self.dfs_btn)
        solve_buttons_layout.addWidget(self.ucs_btn)
        solve_buttons_layout.addWidget(self.dls_btn)
        solve_buttons_layout.addWidget(self.iddfs_btn)
        solve_buttons_layout.addWidget(self.clear_btn)

        # Add solve buttons layout to main layout
        main_layout.addLayout(solve_buttons_layout)

        # Set the main layout
        self.setLayout(main_layout)

    def build_grid(self):
        for row in range(ROWS):
            row_buttons = []
            for col in range(COLS):
                btn = QPushButton("")
                btn.setFixedSize(40, 40)  # Adjust cell size
                btn.setStyleSheet("background-color: white; border: 1px solid gray;")
                btn.clicked.connect(lambda _, r=row, c=col: self.cell_clicked(r, c))
                self.grid_layout.addWidget(btn, row, col)
                row_buttons.append(btn)
            self.buttons.append(row_buttons)

    def cell_clicked(self, row, col):
        if self.setting_mode == 'start':
            if self.start_pos:
                self.update_cell(*self.start_pos, 'empty')
            self.start_pos = (row, col)
            self.update_cell(row, col, 'start')
            self.setting_mode = 'goal'
            self.info_label.setText("Click to set Goal position")
        elif self.setting_mode == 'goal':
            if self.goal_pos:
                self.update_cell(*self.goal_pos, 'empty')
            self.goal_pos = (row, col)
            self.update_cell(row, col, 'goal')
            self.setting_mode = 'wall'
            self.info_label.setText("Click to add/remove walls")
        elif self.setting_mode == 'wall':
            current = self.state[row][col]
            if current == 'wall':
                self.update_cell(row, col, 'empty')
            else:
                self.update_cell(row, col, 'wall')


    def update_cell(self, row, col, value):
        self.state[row][col] = value
        color_map = {
            'empty': 'white',
            'start': 'green',
            'goal': 'red',
            'wall': 'black',
            'visited': 'lightblue',
            'path': 'yellow'
        }
        self.buttons[row][col].setStyleSheet(f"background-color: {color_map[value]}; border: 1px solid gray;")

    def solve_bfs(self):
        if not self.start_pos or not self.goal_pos:
            self.info_label.setText("Start and Goal must be set!")
            return

        print("Solving with BFS...")
        visited = [[False for _ in range(COLS)] for _ in range(ROWS)]
        prev = [[None for _ in range(COLS)] for _ in range(ROWS)]

        q = deque()
        q.append(self.start_pos)
        visited[self.start_pos[0]][self.start_pos[1]] = True

        found = False

        while q:
            row, col = q.popleft()
            if (row, col) != self.start_pos and (row, col) != self.goal_pos:
                self.update_cell(row, col, 'visited')
                QApplication.processEvents()

            if (row, col) == self.goal_pos:
                found = True
                break

            for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
                r, c = row + dr, col + dc
                if 0 <= r < ROWS and 0 <= c < COLS and not visited[r][c] and self.state[r][c] != 'wall':
                    q.append((r, c))
                    visited[r][c] = True
                    prev[r][c] = (row, col)

        if found:
            self.reconstruct_path(prev)
            self.info_label.setText("Path found!")
        else:
            self.info_label.setText("No path found!")

    def reconstruct_path(self, prev):
        row, col = self.goal_pos
        while (row, col) != self.start_pos:
            row, col = prev[row][col]
            if (row, col) != self.start_pos:
                self.update_cell(row, col, 'path')
                QApplication.processEvents()

    def solve_dfs(self):
        self.info_label.setText("DFS not yet implemented.")

    def solve_ucs(self):
        self.info_label.setText("UCS not yet implemented.")

    def solve_dls(self):
        self.info_label.setText("DLS not yet implemented.")

    def solve_iddfs(self):
        self.info_label.setText("IDDFS not yet implemented.")

    def clear_grid(self):
        for row in range(ROWS):
            for col in range(COLS):
                self.update_cell(row, col, 'empty')
        self.start_pos = None
        self.goal_pos = None
        self.setting_mode = 'start'
        self.info_label.setText("Click to set Start, Goal, and Walls")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MazeSolver()
    window.show()
    sys.exit(app.exec())
