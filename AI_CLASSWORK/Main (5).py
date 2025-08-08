import sys
import time
import logging

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton,
    QLabel, QHBoxLayout, QLineEdit, QTableWidget, QDialog, QFormLayout,
    QGraphicsScene, QGraphicsItem, QGraphicsView, QMenu, QComboBox,
    QTableWidgetItem
)

from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QFontMetrics, QIcon
from PyQt6.QtCore import Qt, QRectF, QPointF, QTimer, QTime

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


class ColorCell(QGraphicsItem):
    def __init__(self, color_name, colors_list, parent_window, i, j, cell_size, parent=None):
        super().__init__(parent)
        self.original_color_name = color_name
        self.display_color = self.get_color_rgb(color_name)
        self.default_color = self.display_color
        self.selected_color_name = None
        self.colors_list = colors_list
        self.parent_window = parent_window
        self.i = i
        self.j = j
        self.cell_size = cell_size
        self.toggle_state = False
        self.timer = QTimer()
        self.timer.timeout.connect(self.toggle_flash_color)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)
        self.setAcceptHoverEvents(True)

    def get_color_rgb(self, color_name):
        color_map = {
            "red": "#FF0000", "orange": "#FFA500", "yellow": "#FFFF00",
            "green": "#00FF00", "blue": "#0000FF", "purple": "#800080",
            "black": "#000000", "white": "#FFFFFF", "brown": "#A52A2A" # Corrected brown hex
        }
        # Default to a light gray if color_name is not found or empty
        return QColor(color_map.get(color_name.lower(), "#ADD8E6"))

    def boundingRect(self):
        return QRectF(-self.cell_size / 2, -self.cell_size / 2, self.cell_size, self.cell_size)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        pen = QPen(Qt.GlobalColor.black, 1.5)
        painter.setPen(pen)

        painter.setBrush(QBrush(self.display_color))
        rect = self.boundingRect()
        painter.drawRoundedRect(rect, 10, 10) # 10 for rounded corners

        display_text = self.selected_color_name if self.selected_color_name else ""
        if display_text:
            painter.setPen(QPen(Qt.GlobalColor.black))
            font = QFont("Segoe UI", int(self.cell_size * 0.2), QFont.Weight.Medium)
            painter.setFont(font)
            metrics = QFontMetrics(font)
            text_width = metrics.horizontalAdvance(display_text)
            painter.drawText(QPointF(-text_width / 2, 5), display_text)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            scene_pos = event.scenePos()
            # The original code's itemAt and transform logic here is typically for picking
            # an item at a scene position if there could be multiple items overlapping.
            # In this context, 'self' is already the item that received the click.
            # item = self.scene().itemAt(scene_pos, self.parent_window.view.transform())
            # if item: # This check is redundant for the item that received the event.
            logging.debug(f"Cell clicked at ({self.i}, {self.j}), scene coordinates ({scene_pos.x():.2f}, {scene_pos.y():.2f})")

            menu = QMenu()
            for color in self.colors_list:
                action = menu.addAction(color)
                action.triggered.connect(lambda checked, c=color: self.set_selected_color(c))
            menu.exec(event.screenPos())
            event.accept()

    def set_selected_color(self, color_name):
        logging.debug(f"Setting selected color '{color_name}' for cell ({self.i}, {self.j})")
        self.selected_color_name = color_name
        self.display_color = self.get_color_rgb(color_name)
        self.update()
        if self.parent_window:
            self.parent_window.update_cell(self.i, self.j, color_name)

    def evaluate_match(self, correct_color):
        if self.selected_color_name == correct_color:
            self.display_color = self.get_color_rgb(self.original_color_name) # Revert to original
            self.update()
            self.stop_flash()
        else:
            self.start_flash()

    def start_flash(self):
        if not self.timer.isActive():
            self.toggle_state = False # Ensure it starts from default color then flashes
            self.timer.start(500) # Flash every 500 milliseconds

    def stop_flash(self):
        if self.timer.isActive():
            self.timer.stop()
            self.display_color = self.get_color_rgb(self.original_color_name) # Ensure it stops on original color
            self.update()

    def toggle_flash_color(self):
        if self.toggle_state:
            self.display_color = QColor("#FF6347") # Red for mismatch
        else:
            self.display_color = QColor("#90EE90") # Green for match attempt/flash indication
        self.toggle_state = not self.toggle_state
        self.update()

    def hoverEnterEvent(self, event):
        logging.debug(f"Mouse entered ColorCell at ({self.i}, {self.j})")
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        logging.debug(f"Mouse left ColorCell at ({self.i}, {self.j})")
        self.update()
        super().hoverLeaveEvent(event)


class TimeUpdater:
    def __init__(self, label):
        self.label = label
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000) # Update every 1 second
        self.update_time() # Initial call to set the time immediately

    def update_time(self):
        current_time = time.strftime("%I:%M:%S %p %d, %Y", time.localtime())
        self.label.setText(f"CSP Color Matching Game - {current_time}")


class AdminDialog(QDialog):
    def __init__(self, init_colors_from_main, all_colors_list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Admin Color Entry")
        self.parent = parent
        self.init_colors = init_colors_from_main
        self.all_colors_list = all_colors_list # All possible colors for dropdowns

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # Input for colors (comma-separated)
        self.colors_input = QLineEdit(",".join(init_colors_from_main))
        form_layout.addRow("Colors (comma-separated):", self.colors_input)
        layout.addLayout(form_layout)

        # Grid for initial colors with dropdowns
        self.init_grid = QTableWidget(self.parent.size, self.parent.size)
        self.init_grid.setHorizontalHeaderLabels([str(i) for i in range(self.parent.size)])
        self.init_grid.setVerticalHeaderLabels([str(i) for i in range(self.parent.size)])
        
        # Populate the table with ComboBoxes
        for i in range(self.parent.size):
            for j in range(self.parent.size):
                combo = QComboBox()
                combo.addItems(self.all_colors_list) # Add all available colors
                
                # Set initial selection for the combo box
                if self.init_colors and i < len(self.init_colors) and j < len(self.init_colors[i]):
                    try:
                        index = combo.findText(self.init_colors[i][j], Qt.MatchFlag.MatchExactly)
                        if index != -1:
                            combo.setCurrentIndex(index)
                        else:
                            combo.setCurrentText("white") # Default if initial color not in list
                    except Exception as e:
                        logging.warning(f"Error setting initial color for combo at ({i},{j}): {e}")
                        combo.setCurrentText("white") # Fallback
                else:
                    combo.setCurrentText("white") # Default if no initial colors provided

                self.init_grid.setCellWidget(i, j, combo)
        layout.addWidget(self.init_grid)

        # Save button
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_and_generate)
        layout.addWidget(self.save_button)

    def save_and_generate(self):
        size, colors, init_colors = self.get_data()
        self.parent.size = size
        self.parent.colors = colors
        self.parent.init_colors = init_colors
        
        # Initialize user_grid with None for the new game
        self.parent.user_grid = [[None for _ in range(self.parent.size)] for _ in range(self.parent.size)]
        
        self.parent.generate_game() # Regenerate the game with new settings
        self.accept() # Close the dialog

    def get_data(self):
        # Default size is 3 if input is empty
        size = 3 
        
        # Get colors from the comma-separated input field
        colors_text = self.colors_input.text()
        colors = [c.strip() for c in colors_text.split(',') if c.strip()]
        if not colors: # Fallback if no colors are entered
            colors = ["red", "green", "blue", "yellow", "white", "black", "brown", "orange"]

        # Get initial colors from the QTableWidget combo boxes
        init_colors = []
        for i in range(self.parent.size):
            row = []
            for j in range(self.parent.size):
                combo = self.init_grid.cellWidget(i, j)
                if isinstance(combo, QComboBox):
                    color = combo.currentText()
                else:
                    color = "white" # Fallback if not a QComboBox
                row.append(color)
            init_colors.append(row)
        
        return size, colors, init_colors


class ColorMatchingWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CSP Color Matching Game")
        self.setGeometry(100, 100, 600, 600)
        self.setWindowIcon(QIcon("icon.png")) # Ensure 'icon.png' exists or remove this line

        self.size = 3  # Default grid size
        self.colors = []  # Available colors for selection
        self.init_colors = []  # Initial colors of the grid cells (the target configuration)
        self.user_grid = []  # User's selected colors for the grid
        self.cells = []  # References to ColorCell QGraphicsItems

        self.setStyleSheet("""
            QLabel#HeaderLabel {
                font-size: 20px;
                font-weight: bold;
                padding: 10px;
                color: #333333;
            }
            QLabel#StatusLabel {
                font-size: 14px;
                padding: 6px;
                color: #444444;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 14px;
                font-size: 14px;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QGraphicsView {
                border: 2px solid #999999;
                border-radius: 10px;
                background-color: #F9F9F9;
            }
        """)
        self.init_ui()
        self.time_updater = TimeUpdater(self.header_label) # Initialize TimeUpdater here
        
        # Automatically show admin settings on startup if no initial colors are set
        if not self.init_colors:
             self.show_admin_dialog()


    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.header_label = QLabel("CSP Color Matching Game - {current_time}") # Placeholder for TimeUpdater
        self.header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.header_label.setObjectName("HeaderLabel")
        layout.addWidget(self.header_label)

        self.admin_btn = QPushButton("Admin Settings")
        self.admin_btn.clicked.connect(self.show_admin_dialog)
        layout.addWidget(self.admin_btn)

        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        layout.addWidget(self.view)

        button_layout = QHBoxLayout()
        self.check_btn = QPushButton("Check Matching")
        self.check_btn.clicked.connect(self.check_csp)
        self.check_btn.setEnabled(False) # Disable until game is generated
        
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.clear_grid)
        self.clear_btn.setEnabled(False) # Disable until game is generated
        
        self.new_game_btn = QPushButton("New Game")
        self.new_game_btn.clicked.connect(self.new_game)
        self.new_game_btn.setEnabled(False) # Disable until game is generated

        button_layout.addStretch()
        button_layout.addWidget(self.check_btn)
        button_layout.addWidget(self.clear_btn)
        button_layout.addWidget(self.new_game_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        self.status_label = QLabel("Welcome! Use Admin Settings to configure.")
        self.status_label.setObjectName("StatusLabel")
        layout.addWidget(self.status_label)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Recalculate cell positions and sizes if necessary after resize
        if self.init_colors: # Only regenerate if a game is active
             self.generate_game()


    def show_admin_dialog(self):
        # Provide a default list of all possible colors to the AdminDialog
        all_possible_colors = ["red", "orange", "yellow", "green", "blue", "purple", "black", "white", "brown", "pink", "teal", "lime", "gray"]
        
        # Pass self.init_colors for editing, and the full list for dropdowns
        dialog = AdminDialog(self.init_colors, all_possible_colors, self)
        if dialog.exec():
            # Data is already saved and game generated via save_and_generate in AdminDialog
            self.status_label.setText("Grid generated. Click cells to select colors.")
            self.check_btn.setEnabled(True)
            self.clear_btn.setEnabled(True)
            self.new_game_btn.setEnabled(True)
        else:
            logging.info("Admin Dialog cancelled.")


    def generate_game(self):
        if not self.init_colors:
            logging.warning("No initial colors set. Cannot generate game.")
            return

        self.scene.clear()
        self.cells = [[None for _ in range(self.size)] for _ in range(self.size)]
        self.user_grid = [[None for _ in range(self.size)] for _ in range(self.size)]

        view_width = self.view.viewport().width()
        view_height = self.view.viewport().height()
        
        # Calculate available space for the grid, considering the smaller dimension
        available_size = min(view_width, view_height)
        
        spacing = 10 # Spacing between cells
        
        # Calculate total size needed for all cells and their spacing
        total_grid_dimension = self.size * (self.cell_size + spacing) - spacing
        
        # Dynamically calculate cell_size based on view size and number of cells
        # Ensure there's space for spacing
        
        # Calculate cell_size to fit within the view, with spacing
        # available_size = self.size * cell_size + (self.size - 1) * spacing
        # cell_size = (available_size - (self.size - 1) * spacing) / self.size
        # The above logic is better if you want exact fit. The code snippet had it slightly differently.
        # Let's use the snippet's logic for now, adjusting for the calculated available_size.

        # Recalculate cell_size to fit all cells and spacing within available_size
        self.cell_size = (available_size - (self.size + 1) * spacing) / self.size # Original logic was (available_size - total_spacing) / self.size, total_spacing is (self.size + 1) * spacing
        if self.cell_size <= 0: # Prevent negative or zero cell size
            self.cell_size = 50 # Default minimum size

        total_grid_width = self.size * (self.cell_size + spacing)
        total_grid_height = self.size * (self.cell_size + spacing)

        # Center the grid in the view
        x_offset = (view_width - total_grid_width) / 2 + self.cell_size / 2
        y_offset = (view_height - total_grid_height) / 2 + self.cell_size / 2


        for i in range(self.size):
            for j in range(self.size):
                color_name = self.init_colors[i][j] if self.init_colors else "white"
                
                # Pass self.colors (all available colors for context menu)
                cell = ColorCell(color_name, self.colors, self, i, j, self.cell_size)
                
                # Calculate position based on cell's center being at the grid point
                x = j * (self.cell_size + spacing) + x_offset
                y = i * (self.cell_size + spacing) + y_offset
                cell.setPos(x, y)
                
                self.scene.addItem(cell)
                self.cells[i][j] = cell
                self.user_grid[i][j] = None # Reset user's choice for new game

        self.scene.setSceneRect(0, 0, view_width, view_height) # Set scene rect to match view

    def update_cell(self, i, j, selected_color_name):
        self.user_grid[i][j] = selected_color_name
        # Here you might want to call check_csp automatically or enable the button

    def clear_grid(self):
        for i in range(self.size):
            for j in range(self.size):
                cell = self.cells[i][j]
                cell.selected_color_name = None
                cell.display_color = cell.get_color_rgb(cell.original_color_name)
                cell.stop_flash() # Stop any flashing
                cell.update()
                self.user_grid[i][j] = None
        self.status_label.setText("Grid cleared. Click cells to select colors.")
        self.check_btn.setEnabled(True) # Re-enable check button

    def new_game(self):
        # Clears current game and prompts for new settings
        self.clear_grid()
        self.show_admin_dialog() # This will generate a new game upon dialog acceptance

    def check_csp(self):
        consistent = True
        score = 0
        for i in range(self.size):
            for j in range(self.size):
                cell = self.cells[i][j]
                correct_color = self.init_colors[i][j] # The original correct color
                
                if self.user_grid[i][j] == correct_color:
                    score += 1
                else:
                    consistent = False
                
                cell.evaluate_match(correct_color) # This will handle flashing/displaying original color

        result_dialog = QDialog(self)
        result_dialog.setWindowTitle("CSP Matching Result")
        result_layout = QVBoxLayout(result_dialog)

        result_label = QLabel(f"CSP Evaluation Result: {'Consistent' if consistent else 'Inconsistent'}")
        result_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        result_layout.addWidget(result_label)

        score_label = QLabel(f"Matching Score: {score} / {self.size * self.size}")
        score_label.setStyleSheet("font-size: 14px;")
        result_layout.addWidget(score_label)

        close_button = QPushButton("Close")
        close_button.clicked.connect(result_dialog.accept)
        result_layout.addWidget(close_button)

        result_dialog.exec()


def main():
    app = QApplication(sys.argv)
    window = ColorMatchingWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()