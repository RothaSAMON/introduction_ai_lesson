from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QLineEdit
import sys

def greet():
    name = name_input.text()
    greeting_label.setText(f"Hello, {name}!")

app = QApplication(sys.argv)
window = QWidget()
window.setWindowTitle("My First PyQt6 App")

# Widgets
name_input = QLineEdit()
name_input.setPlaceholderText("Enter your name")

greet_button = QPushButton("Greet")
greet_button.clicked.connect(greet)

greeting_label = QLabel("")

# Layout
layout = QVBoxLayout()
layout.addWidget(name_input)
layout.addWidget(greet_button)
layout.addWidget(greeting_label)

window.setLayout(layout)
window.show()
sys.exit(app.exec())
