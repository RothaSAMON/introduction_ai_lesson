from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QPushButton, QTextEdit
import sys
from PyQt6.QtCore import Qt

# Define a simple agent class
class SimpleAgent:
    # Method to decide action based on environment
    def decide(self, environment):
        price = environment["price"]
        # Buy if price is less than 30
        if price < 30:
            return "Buy"
        # Sell if price is greater than 70
        elif price > 70:
            return "Sell"
        # Wait otherwise
        else:
            return "Wait"

# This AI agent uses basic logic to determine what action to take based on a price value.

# 🔹 Step 2: Create the Main Application Window

# The AIAgentSimulator class inherits from QWidget, creating the main interface:
class AIAgentSimulator(QWidget):
    # Initialize the class
    def __init__(self):
        super().__init__() # Call the constructor of the parent class
        self.setWindowTitle("AI Agent Simulator") # Set window title
        self.setGeometry(100, 100, 400, 300) # Set window size and position

        self.environment = {"price": 50} # Initialize environment with default price
        self.agent = SimpleAgent() # Create an instance of SimpleAgent

        self.create_widgets() # Create UI widgets
        self.layout_widgets() # Arrange widgets in the layout

    # Method to create widgets
    def create_widgets(self):
        self.price_label = QLabel(f"Price: {self.environment['price']}") # Label to display price
        self.price_slider = QSlider(Qt.Orientation.Horizontal) # Slider to adjust price
        self.price_slider.setRange(0, 100) # Set slider range
        self.price_slider.setValue(self.environment['price']) # Set slider default value
        self.price_slider.valueChanged.connect(self.update_price) # Connect slider to update method

        self.buy_button = QPushButton("Buy") # Button to trigger Buy action
        self.buy_button.clicked.connect(lambda: self.manual_action("Buy")) # Connect button to manual action
        self.sell_button = QPushButton("Sell") # Button to trigger Sell action
        self.sell_button.clicked.connect(lambda: self.manual_action("Sell")) # Connect button to manual action
        self.wait_button = QPushButton("Wait") # Button to trigger Wait action
        self.wait_button.clicked.connect(lambda: self.manual_action("Wait")) # Connect button to manual action

        self.action_group = QWidget() # Group widget for action buttons
        self.auto_decide_button = QPushButton("Auto Decide") # Button to trigger automatic decision
        self.auto_decide_button.clicked.connect(self.agent_decision) # Connect button to agent decision method
        self.result_box = QTextEdit() # Text box to display results
        self.result_box.setReadOnly(True) # Set text box to read-only

    # Method to arrange widgets in the layout
    def layout_widgets(self):
        layout = QVBoxLayout() # Create vertical layout
        layout.addWidget(QLabel("Environment Controls")) # Add label to layout
        layout.addWidget(self.price_label) # Add price label to layout
        layout.addWidget(self.price_slider) # Add slider to layout

        h_layout = QHBoxLayout() # Create horizontal layout for buttons
        h_layout.addWidget(self.buy_button) # Add Buy button to layout
        h_layout.addWidget(self.sell_button) # Add Sell button to layout
        h_layout.addWidget(self.wait_button) # Add Wait button to layout
        self.action_group.setLayout(h_layout) # Set layout for action group

        layout.addWidget(self.action_group) # Add action group to main layout
        layout.addWidget(self.auto_decide_button) # Add Auto Decide button to layout
        layout.addWidget(QLabel("Agent Output")) # Add label for output
        layout.addWidget(self.result_box) # Add result box to layout

        self.setLayout(layout) # Set the main layout

    # Method to update price based on slider value
    def update_price(self, value):
        self.environment["price"] = value # Update environment price
        self.price_label.setText(f"Price: {value}") # Update price label

    # Method to handle manual actions
    def manual_action(self, action):
        self.result_box.append(f"🔧 Manual action triggered: {action}") # Append action to result box

    # Method to make agent decision
    def agent_decision(self):
        decision = self.agent.decide(self.environment) # Get decision from agent
        self.result_box.append(f"🤖 Agent decision based on price {self.environment['price']}: {decision}") # Append decision to result box

# Main entry point for the application
if __name__ == "__main__":
    app = QApplication(sys.argv) # Create application instance
    simulator = AIAgentSimulator() # Create simulator instance
    simulator.show() # Show the simulator window
    sys.exit(app.exec()) # Execute the application