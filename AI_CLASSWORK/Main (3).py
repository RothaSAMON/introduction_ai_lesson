import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QGridLayout, QLineEdit, QPushButton,
    QMessageBox, QHBoxLayout, QVBoxLayout, QLabel
)
from PyQt6.QtGui import QIntValidator
from PyQt6.QtCore import Qt
import random
import copy


class SudokuSolver(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sudoku Solver with PyQt6")
        self.setGeometry(100, 100, 450, 540)

        self.main_layout = QVBoxLayout()

        # Title and instruction
        title_label = QLabel("Sudoku Solver")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instruction_label = QLabel("Fill the Sudoku grid with digits 1-9. Use 'Get Hint' up to 5 times per puzzle.")
        instruction_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.main_layout.addWidget(title_label)
        self.main_layout.addWidget(instruction_label)

        self.grid_layout = QGridLayout()
        self.cells = [[QLineEdit(self) for _ in range(9)] for _ in range(9)]
        self.hint_count = 0
        self.max_hints = 5

        for row in range(9):
            for col in range(9):
                cell = self.cells[row][col]
                cell.setFixedSize(40, 40)
                cell.setAlignment(Qt.AlignmentFlag.AlignCenter)
                cell.setMaxLength(1)
                cell.setStyleSheet("font-size: 16px;")
                cell.setValidator(QIntValidator(1, 9, self))
                self.grid_layout.addWidget(cell, row, col)

        self.hint_button = QPushButton(f"Get Hint ({self.max_hints - self.hint_count} left)")
        self.hint_button.clicked.connect(self.provide_hint)

        solve_button = QPushButton("Solve Sudoku")
        solve_button.clicked.connect(self.solve)

        clear_button = QPushButton("Clear Board")
        clear_button.clicked.connect(self.clear_board)

        new_button = QPushButton("New Game")
        new_button.clicked.connect(self.start_new_game)

        button_layout = QHBoxLayout()
        button_layout.addWidget(solve_button)
        button_layout.addWidget(self.hint_button)
        button_layout.addWidget(clear_button)
        button_layout.addWidget(new_button)

        self.main_layout.addLayout(self.grid_layout)
        self.main_layout.addLayout(button_layout)
        self.setLayout(self.main_layout)

        self.solution = None
        self.start_new_game()

    def get_board(self):
        board = []
        for row in range(9):
            board_row = []
            for col in range(9):
                text = self.cells[row][col].text()
                try:
                    if text == '':
                        board_row.append(0)
                    elif text.isdigit():
                        num = int(text)
                        if 1 <= num <= 9:
                            board_row.append(num)
                        else:
                            raise ValueError
                    else:
                        raise ValueError
                except ValueError:
                    QMessageBox.warning(self, "Invalid Input", f"Cell ({row+1}, {col+1}) contains an invalid entry.")
                    return None
            board.append(board_row)
        return board

    def set_board(self, board):
        for row in range(9):
            for col in range(9):
                self.cells[row][col].setText(str(board[row][col]) if board[row][col] != 0 else "")

    def clear_board(self):
        for row in range(9):
            for col in range(9):
                self.cells[row][col].clear()
                self.cells[row][col].setStyleSheet("font-size: 16px;")
        self.hint_count = 0
        self.hint_button.setText(f"Get Hint ({self.max_hints - self.hint_count} left)")

    def solve(self):
        board = self.get_board()
        if board is None:
            return
        if self.solve_board(board):
            self.set_board(board)
        else:
            QMessageBox.warning(self, "Unsolvable", "This Sudoku puzzle cannot be solved.")

    def solve_board(self, board):
        for row in range(9):
            for col in range(9):
                if board[row][col] == 0:
                    for num in range(1, 10):
                        if self.is_valid(board, row, col, num):
                            board[row][col] = num
                            if self.solve_board(board):
                                return True
                            board[row][col] = 0
                    return False
        return True

    def is_valid(self, board, row, col, num):
        for i in range(9):
            if board[row][i] == num or board[i][col] == num:
                return False
        start_row, start_col = 3 * (row // 3), 3 * (col // 3)
        for i in range(3):
            for j in range(3):
                if board[start_row + i][start_col + j] == num:
                    return False
        return True

    def provide_hint(self):
        if self.hint_count >= self.max_hints:
            QMessageBox.warning(self, "Hint Limit", "No more hints available.")
            return

        board = self.get_board()
        if board is None:
            return

        if self.solution is None:
            board_copy = copy.deepcopy(board)
            if not self.solve_board(board_copy):
                QMessageBox.warning(self, "Unsolvable", "This Sudoku puzzle cannot be solved.")
                return
            self.solution = board_copy

        for row in range(9):
            for col in range(9):
                if board[row][col] == 0:
                    self.cells[row][col].setText(str(self.solution[row][col]))
                    self.hint_count += 1
                    self.hint_button.setText(f"Get Hint ({self.max_hints - self.hint_count} left)")
                    return

    def start_new_game(self):
        self.clear_board()
        full_board = [[0]*9 for _ in range(9)]
        self.solve_board(full_board)

        puzzle = copy.deepcopy(full_board)
        cells_to_remove = 40
        while cells_to_remove > 0:
            row, col = random.randint(0, 8), random.randint(0, 8)
            if puzzle[row][col] != 0:
                puzzle[row][col] = 0
                cells_to_remove -= 1

        self.solution = full_board
        self.set_board(puzzle)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SudokuSolver()
    window.show()
    sys.exit(app.exec())
