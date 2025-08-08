import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QTextEdit, QPushButton, QFileDialog,
    QLabel, QMessageBox
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt

# --- NEW IMPORTS for Summarization ---
# We are replacing gensim with sumy, a library dedicated to summarization.
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer as Summarizer # LSA is a good general-purpose algorithm
from sumy.nlp.stemmers import Stemmer
from sumy.utils import get_stop_words


class TextSummarizerApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # --- Window Configuration ---
        self.setWindowTitle("AI Text Summarizer")
        self.setGeometry(100, 100, 800, 600)
        self.setWindowIcon(QIcon())

        # --- Central Widget and Layout ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # --- Styling ---
        self.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
            }
            QTextEdit {
                background-color: #ffffff;
                border: 1px solid #cccccc;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton {
                background-color: #007BFF;
                color: white;
                border-radius: 5px;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #333333;
            }
        """)

        # --- UI Elements ---
        input_layout = QVBoxLayout()
        input_label = QLabel("Enter Text or Upload a File:")
        self.input_text_edit = QTextEdit()
        self.input_text_edit.setPlaceholderText("Paste your long text here...")
        input_layout.addWidget(input_label)
        input_layout.addWidget(self.input_text_edit)

        button_layout = QHBoxLayout()
        self.upload_button = QPushButton("Upload File (.txt)")
        self.upload_button.clicked.connect(self.upload_file)
        button_layout.addWidget(self.upload_button)

        self.summarize_button = QPushButton("Summarize")
        self.summarize_button.clicked.connect(self.summarize_text)
        button_layout.addWidget(self.summarize_button)

        output_layout = QVBoxLayout()
        output_label = QLabel("Summary:")
        self.output_text_edit = QTextEdit()
        self.output_text_edit.setReadOnly(True)
        output_layout.addWidget(output_label)
        output_layout.addWidget(self.output_text_edit)

        main_layout.addLayout(input_layout, stretch=2)
        main_layout.addLayout(button_layout)
        main_layout.addLayout(output_layout, stretch=1)

    def upload_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open Text File", "", "Text Files (*.txt)")
        if file_name:
            try:
                with open(file_name, 'r', encoding='utf-8') as f:
                    self.input_text_edit.setText(f.read())
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not read file: {e}")

    # --- UPDATED SUMMARIZATION FUNCTION ---
    def summarize_text(self):
        """Performs the text summarization using the sumy library."""
        original_text = self.input_text_edit.toPlainText().strip()

        if not original_text:
            QMessageBox.warning(self, "Input Error", "Please enter or upload some text to summarize.")
            return

        try:
            # Language for summarization
            LANGUAGE = "english"
            # Number of sentences in the summary
            SENTENCES_COUNT = 5

            # 1. Create a parser from the input text
            parser = PlaintextParser.from_string(original_text, Tokenizer(LANGUAGE))
            
            # 2. Create a stemmer (for reducing words to their root form)
            stemmer = Stemmer(LANGUAGE)

            # 3. Instantiate the summarizer algorithm
            summarizer = Summarizer(stemmer)
            summarizer.stop_words = get_stop_words(LANGUAGE)

            # 4. Generate the summary
            summary_sentences = summarizer(parser.document, SENTENCES_COUNT)

            # 5. Join the summary sentences into a single string
            summary = " ".join(str(sentence) for sentence in summary_sentences)
            
            if not summary:
                 summary = "Could not generate a summary. The input text may be too short."

            self.output_text_edit.setText(summary)

        except Exception as e:
            self.output_text_edit.setText(f"An error occurred during summarization.\n\nError: {e}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = TextSummarizerApp()
    main_window.show()
    sys.exit(app.exec())
    