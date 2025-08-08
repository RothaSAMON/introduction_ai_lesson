# -*- coding: utf-8 -*-
"""
A simple desktop application for summarizing articles using an AI model.
The application provides a GUI built with PyQt6, uses a pre-trained
transformer model for summarization, and stores history in an SQLite database.

Technology Used:
- Programming Language: Python
- GUI Framework: PyQt6
- AI Model: Hugging Face Transformers (distilbart-cnn-12-6)
- Database: SQLite3
"""

import sys
import sqlite3
from datetime import datetime

# --- PyQt6 Imports ---
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QLabel, QListWidget, QListWidgetItem,
    QMessageBox, QSplitter, QStatusBar, QDialog, QProgressBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt6.QtGui import QFont

# --- AI Model Imports ---
# To prevent freezing the GUI, the model will be run in a separate thread.
from transformers import pipeline, Pipeline

# --- Global Variables ---
DB_NAME = "summarization_history.db"
SUMMARIZER_MODEL = "sshleifer/distilbart-cnn-12-6"

# --- Database Management ---
def initialize_database():
    """Creates the SQLite database and the history table if they don't exist."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_text TEXT NOT NULL,
                summary_text TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        sys.exit(1)

# --- AI Summarization Worker ---
class SummarizerWorker(QObject):
    """
    A worker object that runs the summarization task in a separate thread
    to prevent the GUI from freezing.
    """
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    _summarizer_pipeline: Pipeline = None

    def __init__(self, text_to_summarize):
        super().__init__()
        self.text_to_summarize = text_to_summarize

    def run(self):
        """The main task to be executed by the thread."""
        try:
            # Initialize the pipeline only once and reuse it
            if SummarizerWorker._summarizer_pipeline is None:
                print("Initializing summarization pipeline for the first time...")
                SummarizerWorker._summarizer_pipeline = pipeline("summarization", model=SUMMARIZER_MODEL)
                print("Pipeline initialized successfully.")

            # Perform summarization
            # We calculate min/max length for better results on various text sizes
            words = self.text_to_summarize.split()
            num_words = len(words)
            min_len = max(25, int(num_words * 0.1))
            max_len = min(150, int(num_words * 0.5))

            summary = SummarizerWorker._summarizer_pipeline(
                self.text_to_summarize,
                max_length=max_len,
                min_length=min_len,
                do_sample=False
            )
            
            if summary and isinstance(summary, list):
                self.finished.emit(summary[0]['summary_text'])
            else:
                self.error.emit("Summarization failed to produce a valid result.")

        except Exception as e:
            # Catching all exceptions from the model/pipeline
            error_message = f"An error occurred during summarization:\n{str(e)}"
            self.error.emit(error_message)


# --- Main Application Window ---
class SummarizerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db_conn = None
        self.summarization_thread = None
        self.worker = None
        self.initUI()
        self.load_history()

    def initUI(self):
        """Sets up the user interface."""
        self.setWindowTitle("AI Article Summarizer")
        self.setGeometry(100, 100, 1000, 700)

        # Main widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # --- Left Side: Input and Output ---
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # Input Area
        input_label = QLabel("Paste Article Text Below:")
        input_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("Enter the long article here...")
        self.input_text.setFont(QFont("Arial", 10))

        # Output Area
        output_label = QLabel("Generated Summary:")
        output_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFont(QFont("Arial", 10))
        
        # Use a splitter to make text areas resizable
        text_splitter = QSplitter(Qt.Orientation.Vertical)
        text_splitter.addWidget(self.input_text)
        text_splitter.addWidget(self.output_text)
        text_splitter.setStretchFactor(0, 2) # Input gets 2/3 of space
        text_splitter.setStretchFactor(1, 1) # Output gets 1/3 of space

        # Summarize Button
        self.summarize_button = QPushButton("Summarize Text")
        self.summarize_button.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.summarize_button.setStyleSheet("padding: 10px;")
        self.summarize_button.clicked.connect(self.run_summarization)

        # Add widgets to the left layout
        left_layout.addWidget(input_label)
        left_layout.addWidget(text_splitter)
        left_layout.addWidget(self.summarize_button)

        # --- Right Side: History ---
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        history_label = QLabel("History")
        history_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.history_list = QListWidget()
        self.history_list.itemClicked.connect(self.display_history_item)
        
        right_layout.addWidget(history_label)
        right_layout.addWidget(self.history_list)

        # --- Main Splitter ---
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.addWidget(left_panel)
        main_splitter.addWidget(right_panel)
        main_splitter.setStretchFactor(0, 3) # Left panel gets 3/4 of space
        main_splitter.setStretchFactor(1, 1) # Right panel gets 1/4 of space

        main_layout.addWidget(main_splitter)
        
        # --- Status Bar ---
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready. The first summarization will download the AI model.", 5000)

    def run_summarization(self):
        """Handles the 'Summarize' button click event."""
        article_text = self.input_text.toPlainText().strip()
        if not article_text:
            QMessageBox.warning(self, "Input Error", "Please enter some text to summarize.")
            return

        # Disable button and show status
        self.summarize_button.setEnabled(False)
        self.summarize_button.setText("Summarizing...")
        self.status_bar.showMessage("Processing... This may take a moment, especially the first time.")

        # Create and start the worker thread
        self.summarization_thread = QThread()
        self.worker = SummarizerWorker(article_text)
        self.worker.moveToThread(self.summarization_thread)

        # Connect signals
        self.summarization_thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_summary_complete)
        self.worker.error.connect(self.on_summary_error)
        
        # Clean up after the thread finishes
        self.worker.finished.connect(self.summarization_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.summarization_thread.finished.connect(self.summarization_thread.deleteLater)

        self.summarization_thread.start()

    def on_summary_complete(self, summary):
        """Slot to handle the finished signal from the worker."""
        self.output_text.setText(summary)
        self.save_to_history(self.input_text.toPlainText().strip(), summary)
        self.load_history()
        
        # Re-enable button and clear status
        self.summarize_button.setEnabled(True)
        self.summarize_button.setText("Summarize Text")
        self.status_bar.showMessage("Summarization complete.", 5000)
        QMessageBox.information(self, "Success", "Article has been successfully summarized.")

    def on_summary_error(self, error_message):
        """Slot to handle the error signal from the worker."""
        QMessageBox.critical(self, "Error", error_message)
        
        # Re-enable button and clear status
        self.summarize_button.setEnabled(True)
        self.summarize_button.setText("Summarize Text")
        self.status_bar.showMessage("An error occurred.", 5000)

    def save_to_history(self, original, summary):
        """Saves a new summary record to the database."""
        try:
            self.db_conn = sqlite3.connect(DB_NAME)
            cursor = self.db_conn.cursor()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute(
                "INSERT INTO history (original_text, summary_text, created_at) VALUES (?, ?, ?)",
                (original, summary, timestamp)
            )
            self.db_conn.commit()
            self.db_conn.close()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to save history: {e}")

    def load_history(self):
        """Loads summarization history from the database into the list widget."""
        self.history_list.clear()
        try:
            self.db_conn = sqlite3.connect(DB_NAME)
            cursor = self.db_conn.cursor()
            cursor.execute("SELECT id, summary_text, created_at FROM history ORDER BY id DESC")
            records = cursor.fetchall()
            for record in records:
                item_id, summary_text, created_at = record
                # Create a display text with a snippet of the summary
                display_text = f"{created_at}\n{summary_text[:60]}..."
                list_item = QListWidgetItem(display_text)
                list_item.setData(Qt.ItemDataRole.UserRole, item_id) # Store DB id in the item
                self.history_list.addItem(list_item)
            self.db_conn.close()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load history: {e}")

    def display_history_item(self, item):
        """Fetches and displays the full text of a clicked history item."""
        item_id = item.data(Qt.ItemDataRole.UserRole)
        try:
            self.db_conn = sqlite3.connect(DB_NAME)
            cursor = self.db_conn.cursor()
            cursor.execute("SELECT original_text, summary_text FROM history WHERE id = ?", (item_id,))
            record = cursor.fetchone()
            if record:
                self.input_text.setText(record[0])
                self.output_text.setText(record[1])
            self.db_conn.close()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to retrieve history item: {e}")
            
    def closeEvent(self, event):
        """Handle the window close event."""
        # Ensure thread is properly terminated if app is closed while running
        if self.summarization_thread and self.summarization_thread.isRunning():
            self.summarization_thread.quit()
            self.summarization_thread.wait() # Wait for the thread to finish
        event.accept()


# --- Main Execution ---
if __name__ == '__main__':
    # Ensure the database is ready before starting the app
    initialize_database()

    app = QApplication(sys.argv)
    main_window = SummarizerApp()
    main_window.show()
    sys.exit(app.exec())
    