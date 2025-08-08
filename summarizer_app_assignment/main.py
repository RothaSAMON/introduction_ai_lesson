import sys
import sqlite3
import re
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                            QWidget, QPushButton, QTextEdit, QLabel, QListWidget, 
                            QSplitter, QMessageBox, QProgressBar, QLineEdit, QDialog,
                            QDialogButtonBox, QListWidgetItem)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QIcon
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from collections import Counter
import heapq

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
        self.stemmer = PorterStemmer()
        try:
            self.stop_words = set(stopwords.words('english'))
        except LookupError:
            # Download stopwords if not available
            nltk.download('stopwords', quiet=True)
            self.stop_words = set(stopwords.words('english'))
    
    def simple_sentence_split(self, text):
        """Fallback sentence splitting method if NLTK fails"""
        # Simple sentence splitting based on punctuation
        import re
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        return sentences
    
    def simple_word_tokenize(self, text):
        """Fallback word tokenization if NLTK fails"""
        import re
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        return words
    
    def preprocess_text(self, text):
        """Clean and preprocess the text"""
        # Remove extra whitespace and newlines
        text = re.sub(r'\s+', ' ', text.strip())
        return text
    
    def calculate_sentence_scores(self, sentences, word_freq):
        """Calculate scores for each sentence based on word frequencies and position"""
        sentence_scores = {}
        
        for i, sentence in enumerate(sentences):
            try:
                words = word_tokenize(sentence.lower())
            except (LookupError, OSError):
                # Use fallback tokenization
                words = self.simple_word_tokenize(sentence)
            
            words = [word for word in words if word.isalnum() and word not in self.stop_words]
            
            if len(words) > 0:
                # Base score from word frequencies
                score = 0
                for word in words:
                    if word in word_freq:
                        score += word_freq[word]
                
                # Normalize by sentence length
                score = score / len(words)
                
                # Boost score for sentences at beginning and end (often more important)
                position_boost = 1.0
                if i == 0:  # First sentence
                    position_boost = 1.3
                elif i == len(sentences) - 1:  # Last sentence
                    position_boost = 1.2
                elif i < len(sentences) * 0.3:  # First third of text
                    position_boost = 1.1
                
                # Boost score for longer sentences (often contain more information)
                length_boost = min(1.5, len(words) / 15.0) if len(words) > 10 else 0.8
                
                # Check for numbers, proper nouns, and important keywords
                importance_boost = 1.0
                sentence_lower = sentence.lower()
                if any(char.isdigit() for char in sentence):
                    importance_boost += 0.2  # Numbers often indicate important facts
                if any(word[0].isupper() for word in sentence.split() if len(word) > 2):
                    importance_boost += 0.1  # Proper nouns
                
                # Keywords that often indicate important content
                important_keywords = ['significant', 'important', 'contributes', 'produces', 
                                    'economic', 'cultural', 'traditional', 'ecological', 'benefits']
                if any(keyword in sentence_lower for keyword in important_keywords):
                    importance_boost += 0.15
                
                final_score = score * position_boost * length_boost * importance_boost
                sentence_scores[sentence] = final_score
        
        return sentence_scores
    
    def summarize(self, text, ratio=0.4, min_sentences=2, max_sentences=8):
        """
        Summarize text using extractive summarization
        
        Args:
            text (str): Input text to summarize
            ratio (float): Proportion of sentences to keep (0.1 to 0.8)
            min_sentences (int): Minimum sentences in summary
            max_sentences (int): Maximum sentences in summary
        
        Returns:
            str: Summarized text
        """
        if not text or len(text.strip()) < 100:
            return "Text too short to summarize effectively."
        
        # Preprocess text
        text = self.preprocess_text(text)
        
        try:
            # Tokenize into sentences - ensure NLTK data is available
            sentences = sent_tokenize(text)
        except (LookupError, OSError) as e:
            # If NLTK fails, try to download data or use fallback
            try:
                if 'punkt' in str(e):
                    nltk.download('punkt', quiet=True)
                    sentences = sent_tokenize(text)
                else:
                    raise e
            except:
                # Use simple fallback method
                sentences = self.simple_sentence_split(text)
        
        if len(sentences) < 3:
            return text  # Return original if too few sentences
        
        try:
            # Calculate word frequencies
            words = word_tokenize(text.lower())
        except (LookupError, OSError) as e:
            # If NLTK fails, try to download data or use fallback
            try:
                if 'punkt' in str(e):
                    nltk.download('punkt', quiet=True)
                    words = word_tokenize(text.lower())
                else:
                    raise e
            except:
                # Use simple fallback method
                words = self.simple_word_tokenize(text)
        words = [word for word in words if word.isalnum() and word not in self.stop_words]
        word_freq = Counter(words)
        
        # Normalize word frequencies
        max_freq = max(word_freq.values())
        for word in word_freq:
            word_freq[word] = word_freq[word] / max_freq
        
        # Calculate sentence scores
        sentence_scores = self.calculate_sentence_scores(sentences, word_freq)
        
        # Determine number of sentences for summary
        num_sentences = max(min_sentences, 
                          min(max_sentences, 
                              int(len(sentences) * ratio)))
        
        # Select top sentences
        top_sentences = heapq.nlargest(num_sentences, sentence_scores, 
                                     key=sentence_scores.get)
        
        # Maintain original order
        summary_sentences = []
        for sentence in sentences:
            if sentence in top_sentences:
                summary_sentences.append(sentence)
        
        return ' '.join(summary_sentences)

class SummarizationWorker(QThread):
    """Worker thread for text summarization to prevent UI freezing"""
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
    """Handle SQLite database operations"""
    
    def __init__(self, db_name="article_summaries.db"):
        self.db_name = db_name
        self.init_database()
    
    def init_database(self):
        """Initialize the database and create tables"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                original_text TEXT NOT NULL,
                summary_text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                word_count_original INTEGER,
                word_count_summary INTEGER
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_summary(self, title, original_text, summary_text):
        """Save a summary to the database"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        word_count_original = len(original_text.split())
        word_count_summary = len(summary_text.split())
        
        cursor.execute('''
            INSERT INTO summaries (title, original_text, summary_text, 
                                 word_count_original, word_count_summary)
            VALUES (?, ?, ?, ?, ?)
        ''', (title, original_text, summary_text, word_count_original, word_count_summary))
        
        conn.commit()
        conn.close()
        return cursor.lastrowid
    
    def get_all_summaries(self):
        """Retrieve all summaries from the database"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, title, created_at, word_count_original, word_count_summary
            FROM summaries ORDER BY created_at DESC
        ''')
        
        summaries = cursor.fetchall()
        conn.close()
        return summaries
    
    def get_summary_by_id(self, summary_id):
        """Get a specific summary by ID"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM summaries WHERE id = ?
        ''', (summary_id,))
        
        summary = cursor.fetchone()
        conn.close()
        return summary
    
    def delete_summary(self, summary_id):
        """Delete a summary from the database"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM summaries WHERE id = ?', (summary_id,))
        conn.commit()
        conn.close()

class ArticleSummarizerApp(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.db_manager = DatabaseManager()
        self.current_summary_id = None
        self.summarization_worker = None
        
        self.setWindowTitle("Article Summarizer")
        self.setGeometry(100, 100, 1200, 800)
        
        self.init_ui()
        self.load_saved_summaries()
    
    def init_ui(self):
        """Initialize the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel - Saved summaries
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - Main working area
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter proportions
        splitter.setSizes([300, 900])
    
    def create_left_panel(self):
        """Create the left panel with saved summaries"""
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Title
        title_label = QLabel("Saved Summaries")
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        left_layout.addWidget(title_label)
        
        # Summary list
        self.summary_list = QListWidget()
        self.summary_list.itemClicked.connect(self.load_selected_summary)
        left_layout.addWidget(self.summary_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.load_saved_summaries)
        button_layout.addWidget(self.refresh_btn)
        
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self.delete_selected_summary)
        button_layout.addWidget(self.delete_btn)
        
        left_layout.addLayout(button_layout)
        
        return left_widget
    
    def create_right_panel(self):
        """Create the right panel with main functionality"""
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # Title input
        title_layout = QHBoxLayout()
        title_layout.addWidget(QLabel("Title:"))
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Enter article title...")
        title_layout.addWidget(self.title_input)
        right_layout.addLayout(title_layout)
        
        # Original text input
        right_layout.addWidget(QLabel("Original Article:"))
        self.original_text = QTextEdit()
        self.original_text.setPlaceholderText("Paste your article here...")
        self.original_text.setMinimumHeight(200)
        right_layout.addWidget(self.original_text)
        
        # Control buttons
        control_layout = QHBoxLayout()
        
        self.summarize_btn = QPushButton("Summarize Article")
        self.summarize_btn.clicked.connect(self.summarize_article)
        control_layout.addWidget(self.summarize_btn)
        
        self.save_btn = QPushButton("Save Summary")
        self.save_btn.clicked.connect(self.save_current_summary)
        self.save_btn.setEnabled(False)
        control_layout.addWidget(self.save_btn)
        
        self.clear_btn = QPushButton("Clear All")
        self.clear_btn.clicked.connect(self.clear_all_fields)
        control_layout.addWidget(self.clear_btn)
        
        right_layout.addLayout(control_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        right_layout.addWidget(self.progress_bar)
        
        # Summary output
        right_layout.addWidget(QLabel("Summary:"))
        self.summary_text = QTextEdit()
        self.summary_text.setPlaceholderText("Summary will appear here...")
        self.summary_text.setMinimumHeight(200)
        right_layout.addWidget(self.summary_text)
        
        # Statistics
        self.stats_label = QLabel("")
        right_layout.addWidget(self.stats_label)
        
        return right_widget
    
    def summarize_article(self):
        """Summarize the input article"""
        text = self.original_text.toPlainText().strip()
        
        if not text:
            QMessageBox.warning(self, "Warning", "Please enter some text to summarize.")
            return
        
        if len(text) < 100:
            QMessageBox.warning(self, "Warning", "Text is too short. Please enter at least 100 characters.")
            return
        
        # Disable button and show progress
        self.summarize_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        
        # Start summarization in worker thread
        self.summarization_worker = SummarizationWorker(text, 0.4)
        self.summarization_worker.finished.connect(self.on_summarization_finished)
        self.summarization_worker.error.connect(self.on_summarization_error)
        self.summarization_worker.start()
    
    def on_summarization_finished(self, summary):
        """Handle completed summarization"""
        self.summary_text.setPlainText(summary)
        self.save_btn.setEnabled(True)
        
        # Update statistics
        original_words = len(self.original_text.toPlainText().split())
        summary_words = len(summary.split())
        reduction = ((original_words - summary_words) / original_words) * 100
        
        stats_text = f"Original: {original_words} words | Summary: {summary_words} words | Reduction: {reduction:.1f}%"
        self.stats_label.setText(stats_text)
        
        # Re-enable button and hide progress
        self.summarize_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
    
    def on_summarization_error(self, error_msg):
        """Handle summarization error"""
        QMessageBox.critical(self, "Error", f"Summarization failed: {error_msg}")
        self.summarize_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
    
    def save_current_summary(self):
        """Save the current summary to database"""
        title = self.title_input.text().strip()
        original = self.original_text.toPlainText().strip()
        summary = self.summary_text.toPlainText().strip()
        
        if not title:
            title = f"Summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if not original or not summary:
            QMessageBox.warning(self, "Warning", "Cannot save: missing original text or summary.")
            return
        
        try:
            summary_id = self.db_manager.save_summary(title, original, summary)
            QMessageBox.information(self, "Success", "Summary saved successfully!")
            self.load_saved_summaries()
            self.save_btn.setEnabled(False)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save summary: {e}")
    
    def load_saved_summaries(self):
        """Load saved summaries into the list"""
        self.summary_list.clear()
        summaries = self.db_manager.get_all_summaries()
        
        for summary in summaries:
            summary_id, title, created_at, orig_words, summ_words = summary
            item_text = f"{title}\n{created_at[:16]} | {orig_words}→{summ_words} words"
            
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, summary_id)
            self.summary_list.addItem(item)
    
    def load_selected_summary(self, item):
        """Load selected summary into the text fields"""
        summary_id = item.data(Qt.ItemDataRole.UserRole)
        summary_data = self.db_manager.get_summary_by_id(summary_id)
        
        if summary_data:
            _, title, original, summary, _, _, _ = summary_data
            
            self.title_input.setText(title)
            self.original_text.setPlainText(original)
            self.summary_text.setPlainText(summary)
            
            # Update statistics
            original_words = len(original.split())
            summary_words = len(summary.split())
            reduction = ((original_words - summary_words) / original_words) * 100
            
            stats_text = f"Original: {original_words} words | Summary: {summary_words} words | Reduction: {reduction:.1f}%"
            self.stats_label.setText(stats_text)
            
            self.current_summary_id = summary_id
            self.save_btn.setEnabled(False)
    
    def delete_selected_summary(self):
        """Delete the selected summary"""
        current_item = self.summary_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Warning", "Please select a summary to delete.")
            return
        
        reply = QMessageBox.question(self, "Confirm Delete", 
                                   "Are you sure you want to delete this summary?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            summary_id = current_item.data(Qt.ItemDataRole.UserRole)
            try:
                self.db_manager.delete_summary(summary_id)
                self.load_saved_summaries()
                QMessageBox.information(self, "Success", "Summary deleted successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete summary: {e}")
    
    def clear_all_fields(self):
        """Clear all input fields"""
        self.title_input.clear()
        self.original_text.clear()
        self.summary_text.clear()
        self.stats_label.clear()
        self.save_btn.setEnabled(False)
        self.current_summary_id = None

def main():
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Article Summarizer")
    app.setApplicationVersion("1.0")
    
    # Create and show main window
    window = ArticleSummarizerApp()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
