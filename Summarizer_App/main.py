import sys
import sqlite3
import re
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
                             QWidget, QPushButton, QTextEdit, QLabel, QListWidget,
                             QSplitter, QMessageBox, QProgressBar, QLineEdit, QDialog,
                             QDialogButtonBox, QListWidgetItem)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QIcon
import nltk
import qtawesome as qta  # --- NEW: Import qtawesome for icons ---

# --- All your backend classes (TextSummarizer, SummarizationWorker, DatabaseManager) remain unchanged ---
# --- I'm collapsing them here for brevity, but they are still part of the full script. ---

#<editor-fold desc="Backend Classes (Unchanged)">
# Download required NLTK data (run once)
def download_nltk_data():
    """Download required NLTK data with proper error handling"""
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        print("Downloading NLTK punkt tokenizer...")
        nltk.download('punkt', quiet=True)

    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        print("Downloading NLTK stopwords...")
        nltk.download('stopwords', quiet=True)

# Ensure NLTK data is available
download_nltk_data()

class TextSummarizer:
    """Local AI model for text summarization using extractive approach"""
    def __init__(self):
        from nltk.corpus import stopwords
        from nltk.stem import PorterStemmer
        self.stemmer = PorterStemmer()
        try:
            self.stop_words = set(stopwords.words('english'))
        except LookupError:
            nltk.download('stopwords', quiet=True)
            self.stop_words = set(stopwords.words('english'))

    def simple_sentence_split(self, text):
        import re
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]

    def simple_word_tokenize(self, text):
        import re
        return re.findall(r'\b[a-zA-Z]+\b', text.lower())

    def preprocess_text(self, text):
        return re.sub(r'\s+', ' ', text.strip())

    def calculate_sentence_scores(self, sentences, word_freq):
        from nltk.tokenize import word_tokenize
        sentence_scores = {}
        for i, sentence in enumerate(sentences):
            try:
                words = word_tokenize(sentence.lower())
            except (LookupError, OSError):
                words = self.simple_word_tokenize(sentence)
            words = [word for word in words if word.isalnum() and word not in self.stop_words]
            if len(words) > 0:
                score = sum(word_freq.get(word, 0) for word in words) / len(words)
                position_boost = 1.3 if i == 0 else 1.2 if i == len(sentences) - 1 else 1.1 if i < len(sentences) * 0.3 else 1.0
                length_boost = min(1.5, len(words) / 15.0) if len(words) > 10 else 0.8
                importance_boost = 1.0
                if any(char.isdigit() for char in sentence): importance_boost += 0.2
                if any(word[0].isupper() for word in sentence.split() if len(word) > 2): importance_boost += 0.1
                important_keywords = ['significant', 'important', 'contributes', 'produces', 'economic', 'cultural', 'traditional', 'ecological', 'benefits']
                if any(keyword in sentence.lower() for keyword in important_keywords): importance_boost += 0.15
                final_score = score * position_boost * length_boost * importance_boost
                sentence_scores[sentence] = final_score
        return sentence_scores

    def summarize(self, text, ratio=0.4, min_sentences=2, max_sentences=8):
        from nltk.tokenize import sent_tokenize, word_tokenize
        from collections import Counter
        import heapq
        if not text or len(text.strip()) < 100: return "Text too short to summarize effectively."
        text = self.preprocess_text(text)
        try:
            sentences = sent_tokenize(text)
        except (LookupError, OSError):
            try: nltk.download('punkt', quiet=True); sentences = sent_tokenize(text)
            except: sentences = self.simple_sentence_split(text)
        if len(sentences) < 3: return text
        try:
            words = word_tokenize(text.lower())
        except (LookupError, OSError):
            try: nltk.download('punkt', quiet=True); words = word_tokenize(text.lower())
            except: words = self.simple_word_tokenize(text)
        words = [word for word in words if word.isalnum() and word not in self.stop_words]
        word_freq = Counter(words)
        if not word_freq: return "Could not find significant words to summarize."
        max_freq = max(word_freq.values())
        word_freq = {word: freq / max_freq for word, freq in word_freq.items()}
        sentence_scores = self.calculate_sentence_scores(sentences, word_freq)
        num_sentences = max(min_sentences, min(max_sentences, int(len(sentences) * ratio)))
        top_sentences = heapq.nlargest(num_sentences, sentence_scores, key=sentence_scores.get)
        summary_sentences = [sentence for sentence in sentences if sentence in top_sentences]
        return ' '.join(summary_sentences)

class SummarizationWorker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    def __init__(self, text, ratio=0.3):
        super().__init__()
        self.text = text
        self.ratio = ratio
        self.summarizer = TextSummarizer()

    def run(self):
        try:
            summary = self.summarizer.summarize(self.text, self.ratio)
            self.finished.emit(summary)
        except Exception as e:
            self.error.emit(str(e))

class DatabaseManager:
    def __init__(self, db_name="article_summaries.db"):
        self.db_name = db_name
        self.init_database()

    def init_database(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL,
                original_text TEXT NOT NULL, summary_text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                word_count_original INTEGER, word_count_summary INTEGER)''')
        conn.commit()
        conn.close()

    def save_summary(self, title, original_text, summary_text):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        word_count_original = len(original_text.split())
        word_count_summary = len(summary_text.split())
        cursor.execute('INSERT INTO summaries (title, original_text, summary_text, word_count_original, word_count_summary) VALUES (?, ?, ?, ?, ?)',
                       (title, original_text, summary_text, word_count_original, word_count_summary))
        conn.commit()
        last_id = cursor.lastrowid
        conn.close()
        return last_id

    def get_all_summaries(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT id, title, created_at, word_count_original, word_count_summary FROM summaries ORDER BY created_at DESC')
        summaries = cursor.fetchall()
        conn.close()
        return summaries

    def get_summary_by_id(self, summary_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM summaries WHERE id = ?', (summary_id,))
        summary = cursor.fetchone()
        conn.close()
        return summary

    def delete_summary(self, summary_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM summaries WHERE id = ?', (summary_id,))
        conn.commit()
        conn.close()
#</editor-fold>

class ArticleSummarizerApp(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.db_manager = DatabaseManager()
        self.current_summary_id = None
        self.summarization_worker = None
        
        self.setWindowTitle("Article Summarizer")
        self.setGeometry(100, 100, 1200, 800)
        self.setWindowIcon(qta.icon('fa5s.robot', color='#61afef')) # --- NEW: Set a window icon

        self.init_ui()
        self.load_saved_summaries()

    def init_ui(self):
        """Initialize the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0) # --- NEW: Use full window space
        main_layout.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        splitter.setSizes([350, 850])
        # --- NEW: Style the splitter handle ---
        splitter.setStyleSheet("QSplitter::handle { background-color: #3a3f4b; }")

    def create_left_panel(self):
        """Create the left panel with saved summaries"""
        left_widget = QWidget()
        left_widget.setObjectName("leftPanel") # --- NEW: Object name for styling
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(20, 20, 20, 20)
        left_layout.setSpacing(15)

        title_label = QLabel("Saved Summaries")
        title_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        left_layout.addWidget(title_label)
        
        self.summary_list = QListWidget()
        self.summary_list.itemClicked.connect(self.load_selected_summary)
        left_layout.addWidget(self.summary_list)
        
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        # --- NEW: Add icons to buttons ---
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setIcon(qta.icon('fa5s.sync-alt', color='white'))
        self.refresh_btn.clicked.connect(self.load_saved_summaries)
        button_layout.addWidget(self.refresh_btn)
        
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.setIcon(qta.icon('fa5s.trash-alt', color='white'))
        self.delete_btn.clicked.connect(self.delete_selected_summary)
        button_layout.addWidget(self.delete_btn)
        
        left_layout.addLayout(button_layout)
        
        return left_widget
    
    def create_right_panel(self):
        """Create the right panel with main functionality"""
        right_widget = QWidget()
        right_widget.setObjectName("rightPanel") # --- NEW: Object name for styling
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(20, 20, 20, 20)
        right_layout.setSpacing(15)

        # --- NEW: Use a bolder font for labels ---
        title_label = QLabel("Article Title:")
        title_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Enter a title for your summary...")
        right_layout.addWidget(title_label)
        right_layout.addWidget(self.title_input)

        original_label = QLabel("Original Article:")
        original_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.original_text = QTextEdit()
        self.original_text.setPlaceholderText("Paste your long article here to begin...")
        right_layout.addWidget(original_label)
        right_layout.addWidget(self.original_text)
        
        control_layout = QHBoxLayout()
        control_layout.setSpacing(10)
        
        # --- NEW: Add icons to buttons and set object names for styling ---
        self.summarize_btn = QPushButton("Summarize Article")
        self.summarize_btn.setIcon(qta.icon('fa5s.magic', color='white'))
        self.summarize_btn.setObjectName("summarizeButton")
        self.summarize_btn.clicked.connect(self.summarize_article)
        control_layout.addWidget(self.summarize_btn)
        
        self.save_btn = QPushButton("Save Summary")
        self.save_btn.setIcon(qta.icon('fa5s.save', color='white'))
        self.save_btn.clicked.connect(self.save_current_summary)
        self.save_btn.setEnabled(False)
        control_layout.addWidget(self.save_btn)
        
        self.clear_btn = QPushButton("Clear All")
        self.clear_btn.setIcon(qta.icon('fa5s.broom', color='white'))
        self.clear_btn.clicked.connect(self.clear_all_fields)
        control_layout.addWidget(self.clear_btn)
        
        right_layout.addLayout(control_layout)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(False)
        right_layout.addWidget(self.progress_bar)
        
        summary_label = QLabel("Summary:")
        summary_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.summary_text = QTextEdit()
        self.summary_text.setPlaceholderText("Your generated summary will appear here...")
        self.summary_text.setReadOnly(True) # --- NEW: Make summary read-only ---
        right_layout.addWidget(summary_label)
        right_layout.addWidget(self.summary_text)
        
        self.stats_label = QLabel("")
        self.stats_label.setObjectName("statsLabel")
        right_layout.addWidget(self.stats_label)
        
        return right_widget

    # --- All logic methods (summarize_article, on_summarization_finished, etc.) are unchanged ---
    #<editor-fold desc="Logic Methods (Unchanged)">
    def summarize_article(self):
        text = self.original_text.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Warning", "Please enter some text to summarize.")
            return
        if len(text) < 100:
            QMessageBox.warning(self, "Warning", "Text is too short. Please enter at least 100 characters.")
            return
        self.summarize_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.summarization_worker = SummarizationWorker(text, 0.4)
        self.summarization_worker.finished.connect(self.on_summarization_finished)
        self.summarization_worker.error.connect(self.on_summarization_error)
        self.summarization_worker.start()

    def on_summarization_finished(self, summary):
        self.summary_text.setPlainText(summary)
        self.save_btn.setEnabled(True)
        try:
            original_words = len(self.original_text.toPlainText().split())
            summary_words = len(summary.split())
            reduction = ((original_words - summary_words) / original_words) * 100 if original_words > 0 else 0
            stats_text = f"Original: {original_words} words  |  Summary: {summary_words} words  |  Reduction: {reduction:.1f}%"
            self.stats_label.setText(stats_text)
        except ZeroDivisionError:
             self.stats_label.setText("Could not calculate statistics.")
        self.summarize_btn.setEnabled(True)
        self.progress_bar.setVisible(False)

    def on_summarization_error(self, error_msg):
        QMessageBox.critical(self, "Error", f"Summarization failed: {error_msg}")
        self.summarize_btn.setEnabled(True)
        self.progress_bar.setVisible(False)

    def save_current_summary(self):
        title = self.title_input.text().strip()
        original = self.original_text.toPlainText().strip()
        summary = self.summary_text.toPlainText().strip()
        if not title:
            title = f"Summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        if not original or not summary:
            QMessageBox.warning(self, "Warning", "Cannot save: missing original text or summary.")
            return
        try:
            self.db_manager.save_summary(title, original, summary)
            QMessageBox.information(self, "Success", "Summary saved successfully!")
            self.load_saved_summaries()
            self.save_btn.setEnabled(False)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save summary: {e}")

    def load_saved_summaries(self):
        self.summary_list.clear()
        summaries = self.db_manager.get_all_summaries()
        for summary in summaries:
            summary_id, title, created_at, orig_words, summ_words = summary
            item = QListWidgetItem()
            
            # --- NEW: Custom widget for better list item display ---
            item_widget = QWidget()
            item_layout = QVBoxLayout(item_widget)
            item_layout.setContentsMargins(5, 5, 5, 5)
            item_layout.setSpacing(2)

            title_label = QLabel(title)
            title_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))

            details_text = f"{created_at[:16]} | {orig_words}→{summ_words} words"
            details_label = QLabel(details_text)
            details_label.setObjectName("detailsLabel")

            item_layout.addWidget(title_label)
            item_layout.addWidget(details_label)
            
            item.setSizeHint(item_widget.sizeHint())
            item.setData(Qt.ItemDataRole.UserRole, summary_id)
            
            self.summary_list.addItem(item)
            self.summary_list.setItemWidget(item, item_widget)


    def load_selected_summary(self, item):
        summary_id = item.data(Qt.ItemDataRole.UserRole)
        summary_data = self.db_manager.get_summary_by_id(summary_id)
        if summary_data:
            _, title, original, summary, _, _, _ = summary_data
            self.title_input.setText(title)
            self.original_text.setPlainText(original)
            self.summary_text.setPlainText(summary)
            try:
                original_words = len(original.split())
                summary_words = len(summary.split())
                reduction = ((original_words - summary_words) / original_words) * 100 if original_words > 0 else 0
                stats_text = f"Original: {original_words} words  |  Summary: {summary_words} words  |  Reduction: {reduction:.1f}%"
                self.stats_label.setText(stats_text)
            except ZeroDivisionError:
                self.stats_label.setText("Could not calculate statistics.")
            self.current_summary_id = summary_id
            self.save_btn.setEnabled(False)

    def delete_selected_summary(self):
        current_item = self.summary_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Warning", "Please select a summary to delete.")
            return
        reply = QMessageBox.question(self, "Confirm Delete", "Are you sure you want to delete this summary?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            summary_id = current_item.data(Qt.ItemDataRole.UserRole)
            try:
                self.db_manager.delete_summary(summary_id)
                self.load_saved_summaries()
                self.clear_all_fields()
                QMessageBox.information(self, "Success", "Summary deleted successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete summary: {e}")

    def clear_all_fields(self):
        self.title_input.clear()
        self.original_text.clear()
        self.summary_text.clear()
        self.stats_label.clear()
        self.save_btn.setEnabled(False)
        self.current_summary_id = None
        self.summary_list.clearSelection()
    #</editor-fold>

# --- NEW: Define a modern stylesheet (QSS) ---
MODERN_STYLESHEET = """
QWidget {
    font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
    font-size: 14px;
    color: #abb2bf; /* Light gray text */
}
/* Style the main panels */
QWidget#leftPanel {
    background-color: #21252b; /* Slightly lighter than main bg */
}
QWidget#rightPanel {
    background-color: #282c34; /* Main background color */
}
QLabel {
    color: #abb2bf;
}
QLabel#detailsLabel {
    color: #6a7384; /* Dimmer color for details */
    font-size: 12px;
}
QLabel#statsLabel {
    color: #6a7384;
    font-size: 12px;
}
QLineEdit, QTextEdit {
    background-color: #21252b;
    border: 1px solid #3a3f4b;
    border-radius: 8px;
    padding: 8px;
    color: #abb2bf;
}
QLineEdit:focus, QTextEdit:focus {
    border-color: #61afef; /* Blue accent on focus */
}
QPushButton {
    background-color: #3a3f4b;
    color: #dbe0e8;
    border: none;
    padding: 10px 15px;
    border-radius: 8px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #4b5263;
}
QPushButton:pressed {
    background-color: #323842;
}
QPushButton:disabled {
    background-color: #282c34;
    color: #6a7384;
}
/* Special style for the main action button */
QPushButton#summarizeButton {
    background-color: #61afef; /* Blue accent */
    color: white;
}
QPushButton#summarizeButton:hover {
    background-color: #7abcfd;
}
QPushButton#summarizeButton:disabled {
    background-color: #282c34;
    color: #6a7384;
}

QListWidget {
    background-color: #21252b;
    border: none;
}
/* Use setItemWidget for styling items now */

QProgressBar {
    border: 1px solid #3a3f4b;
    border-radius: 8px;
    background-color: #21252b;
    height: 6px;
}
QProgressBar::chunk {
    background-color: #61afef;
    border-radius: 3px;
}
QMessageBox {
    background-color: #282c34;
}
"""

def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(MODERN_STYLESHEET) # --- NEW: Apply the stylesheet to the entire app ---
    
    app.setApplicationName("Article Summarizer")
    app.setApplicationVersion("1.1")
    
    window = ArticleSummarizerApp()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
    