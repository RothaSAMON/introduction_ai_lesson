from PyQt6.QtWidgets import (
    QApplication, QTextEdit, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QPushButton, QSlider, QGroupBox
)
from PyQt6.QtCore import Qt
import sys

class SimpleAgent:
    """
    A VERY BASIC RULE-BASED AI AGENT.
    """
    def decide(self, environment):
        price = environment["price"]
        if price < 30:
            return "buy"
        elif price > 70:
            return "sell"
        else:
            return "wait"

class AIAgentSimulator(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Agent Simulator")
        self.setGeometry(100, 100, 400, 300)

        self.environment = {"price": 50}
        self.agent = SimpleAgent()

        self.create_widgets()
        self.layout_widgets()

    def create_widgets(self):
        self.price_label = QLabel(f"Price: {self.environment['price']}")
        self.price_slider = QSlider(Qt.Orientation.Horizontal)
        self.price_slider.setRange(0, 100)
        self.price_slider.setValue(self.environment['price'])
        self.price_slider.valueChanged.connect(self.update_price)

        self.action_group = QGroupBox("Trigger Agent Action")
        self.buy_button = QPushButton("Buy")
        self.sell_button = QPushButton("Sell")
        self.wait_button = QPushButton("Wait")

        self.buy_button.clicked.connect(lambda: self.manual_action("buy"))
        self.sell_button.clicked.connect(lambda: self.manual_action("sell"))
        self.wait_button.clicked.connect(lambda: self.manual_action("wait"))

        self.result_box = QTextEdit()
        self.result_box.setReadOnly(True)

        self.auto_decide_button = QPushButton("Auto Decide")
        self.auto_decide_button.clicked.connect(self.agent_decision)

    def layout_widgets(self):
        main_layout = QVBoxLayout()

        main_layout.addWidget(self.price_label)
        main_layout.addWidget(self.price_slider)

        action_layout = QHBoxLayout()
        action_layout.addWidget(self.buy_button)
        action_layout.addWidget(self.sell_button)
        action_layout.addWidget(self.wait_button)

        self.action_group.setLayout(action_layout)
        main_layout.addWidget(self.action_group)

        main_layout.addWidget(self.auto_decide_button)
        main_layout.addWidget(self.result_box)

        self.setLayout(main_layout)

    def update_price(self, value):
        self.environment["price"] = value
        self.price_label.setText(f"Price: {value}")

    def manual_action(self, action):
        self.result_box.append(f"Manual action: {action}")

    def agent_decision(self):
        decision = self.agent.decide(self.environment)
        self.result_box.append(f"Agent decided to: {decision}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AIAgentSimulator()
    window.show()
    sys.exit(app.exec())
