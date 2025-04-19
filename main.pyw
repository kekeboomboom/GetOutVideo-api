import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QProgressBar, QTextEdit, QFileDialog, QMessageBox,
                             QComboBox, QSlider) # Import QComboBox
from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QFont, QColor
from datetime import datetime
from pytube import Playlist
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai
import re
import logging
import os
from dotenv import load_dotenv
from builtins import KeyError
load_dotenv(".env")


class MainWindow(QMainWindow):
    DEFAULT_CHUNK_SIZE = 70000 # Define default chunk size as a class variable

    def __init__(self):
        super().__init__()
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.prompts = {

            "Balanced and Detailed": """Turn the following unorganized text into a well-structured, readable format while retaining EVERY detail, context, and nuance of the original content.
            Refine the text to improve clarity, grammar, and coherence WITHOUT cutting, summarizing, or omitting any information.
            The goal is to make the content easier to read and process by:

            - Organizing the content into logical sections with appropriate subheadings.
            - Using bullet points or numbered lists where applicable to present facts, stats, or comparisons.
            - Highlighting key terms, names, or headings with bold text for emphasis.
            - Preserving the original tone, humor, and narrative style while ensuring readability.
            - Adding clear separators or headings for topic shifts to improve navigation.

            Ensure the text remains informative, capturing the original intent, tone,
            and details while presenting the information in a format optimized for analysis by both humans and AI.
            REMEMBER that Details are important, DO NOT overlook Any details, even small ones.
            All output must be generated entirely in [Language]. Do not use any other language at any point in the response. Do not include this unorganized text into your response.
            Text:
            """,

            "Summary": """Summarize the following transcript into a concise and informative summary. 
            Identify the core message, main arguments, and key pieces of information presented in the video.
            The summary should capture the essence of the video's content in a clear and easily understandable way.
            Aim for a summary that is shorter than the original transcript but still accurately reflects its key points.  
            Focus on conveying the most important information and conclusions.
All output must be generated entirely in [Language]. Do not use any other language at any point in the response. Do not include this unorganized text into your response.
Text: """,
            "Educational": """Transform the following transcript into a comprehensive educational text, resembling a textbook chapter. Structure the content with clear headings, subheadings, and bullet points to enhance readability and organization for educational purposes.

Crucially, identify any technical terms, jargon, or concepts that are mentioned but not explicitly explained within the transcript. For each identified term, provide a concise definition (no more than two sentences) formatted as a blockquote.  Integrate these definitions strategically within the text, ideally near the first mention of the term, to enhance understanding without disrupting the flow.

Ensure the text is highly informative, accurate, and retains all the original details and nuances of the transcript. The goal is to create a valuable educational resource that is easy to study and understand.

All output must be generated entirely in [Language]. Do not use any other language at any point in the response. Do not use any other language at any point in the response. Do not include this unorganized text into your response.

Text:""",
            "Narrative Rewriting": """Rewrite the following transcript into an engaging narrative or story format. Transform the factual or conversational content into a more captivating and readable piece, similar to a short story or narrative article.

While rewriting, maintain a close adherence to the original subjects and information presented in the video. Do not deviate significantly from the core topics or introduce unrelated elements.  The goal is to enhance engagement and readability through storytelling techniques without altering the fundamental content or message of the video.  Use narrative elements like descriptive language, scene-setting (if appropriate), and a compelling flow to make the information more accessible and enjoyable.

All output must be generated entirely in [Language]. Do not use any other language at any point in the response. Do not include this unorganized text into your response.

Text:""",
            "Q&A Generation": """Generate a set of questions and answers based on the following transcript for self-assessment or review.  For each question, create a corresponding answer.

Format each question as a level 3 heading using Markdown syntax (### Question Text). Immediately following each question, provide the answer.  This format is designed for foldable sections, allowing users to easily hide and reveal answers for self-testing.

Ensure the questions are relevant to the key information and concepts in the transcript and that the answers are accurate and comprehensive based on the video content.

All output must be generated entirely in [Language]. Do not use any other language at any point in the response. Do not include this unorganized text into your response.

Text:"""
        }
        self.category_chunk_sizes = {
            "Balanced and Detailed": self.DEFAULT_CHUNK_SIZE,
            "Summary": self.DEFAULT_CHUNK_SIZE, # Standardize all suggestions
            "Educational": self.DEFAULT_CHUNK_SIZE,
            "Narrative Rewriting": self.DEFAULT_CHUNK_SIZE,
            "Q&A Generation": self.DEFAULT_CHUNK_SIZE
        }
        self.selected_category = "Balanced and Detailed" # Default Category
        

        self.extraction_thread = None
        self.gemini_thread = None
        self.is_processing = False
        self.available_models = ["gemini-2.5-flash-preview-04-17", "gemini-2.5-pro-preview-03-25", "gpt-4.1-mini"] # Static model list
        self.selected_model_name = "gemini-2.5-flash-preview-04-17" # Default model

        # Set the class variable default chunk size using the constant
        GeminiProcessingThread.chunk_size = self.DEFAULT_CHUNK_SIZE

        self.initUI()

        
        
    def get_combobox_style(self):
        return """
            QComboBox {
                background-color: #34495e;
                border: 2px solid #3498db;
                border-radius: 5px;
                color: #ecf0f1;
                padding: 0px;
                font-size: 10pt;
            }
            QComboBox:!editable, QComboBox::drop-down:editable {
                 background: #34495e;
            }

            QComboBox:on { /* shift the text when the popup opens */
                border-bottom-left-radius: 0px;
                border-bottom-right-radius: 0px;
            }

            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;

                border-left-width: 1px;
                border-left-color: darkgray;
                border-left-style: solid; /* just a single line */
                border-top-right-radius: 3px; /* same radius as the QComboBox */
                border-bottom-right-radius: 3px;
            }

            QComboBox::down-arrow {
                image: url(down_arrow.png); /* Replace with your arrow image if you want a custom one */
            }

            QComboBox::down-arrow:on { /* shift the arrow when popup is open */
                top: 1px;
                left: 1px;
            }

            QComboBox QAbstractItemView {
                border: 2px solid #3498db;
                border-radius: 5px;
                background-color: #2c3e50;
                color: #ecf0f1;
                selection-background-color: #3498db;
                selection-color: #ecf0f1;
            }
        """

    def category_changed(self, index):
        category_name = self.category_combo.itemText(index) # Get selected category name
        self.selected_category = category_name # Update selected category
        # Always suggest the default chunk size now when category changes
        suggested_chunk_size = self.DEFAULT_CHUNK_SIZE
        self.chunk_size_slider.setValue(suggested_chunk_size) # Set slider value
        self.update_chunk_size_label(suggested_chunk_size) # Update label

    @pyqtSlot(int) # Indicate it's a slot and expects an integer (slider value)
    def update_chunk_size_label(self, value):
        self.chunk_size_value_label.setText(str(value)) # Update the label text with the new slider value


    def initUI(self):
        
        self.setWindowTitle("YouTube Playlist Transcript & Gemini Refinement Extractor")
        self.setMinimumSize(900, 850)
        self.apply_dark_mode()
        self.showFullScreen()

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Title Section
        title_label = QLabel("YouTube Playlist Transcript & Gemini Refinement Extractor")
        title_label.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            color: #2ecc71;
            padding: 10px;
            border-radius: 8px;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #2c3e50, stop:1 #3498db);
        """)
        main_layout.addWidget(title_label)

        # Input Container
        input_container = QWidget()
        input_container.setStyleSheet("background-color: #2c3e50; border-radius: 10px; padding: 10px;")
        input_layout = QVBoxLayout(input_container)
        input_layout.setSpacing(1)

        # Playlist URL Input
        url_layout = QVBoxLayout()
        url_label = QLabel("YouTube URL (Playlist or Video):")
        url_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        url_label.setStyleSheet("color: #ecf0f1;")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter YouTube playlist or video URL (e.g., https://www.youtube.com/playlist?list=... or https://www.youtube.com/watch?v=...)")
        self.url_input.setFont(QFont("Segoe UI", 9))
        self.url_input.setStyleSheet(self.get_input_style())
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        input_layout.addLayout(url_layout)

        # Language Input
        language_layout = QVBoxLayout()
        language_label = QLabel("Output Language:")
        language_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        language_label.setStyleSheet("color: #ecf0f1;")
        self.language_input = QLineEdit()
        self.language_input.setPlaceholderText("e.g., English, Spanish, French")
        self.language_input.setFont(QFont("Segoe UI", 9))
        self.language_input.setStyleSheet(self.get_input_style())

        self.language_input.setText(os.environ.get("LANGUAGE", ""))
        language_layout.addWidget(language_label)
        language_layout.addWidget(self.language_input)
        input_layout.addLayout(language_layout)

        # Start/End Video Index Input (NEW)
        index_layout = QHBoxLayout() # Use QHBoxLayout for side-by-side inputs

        start_index_layout = QVBoxLayout()
        start_label = QLabel("Start Video Index:")
        start_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        start_label.setStyleSheet("color: #ecf0f1;")
        self.start_index_input = QLineEdit()
        self.start_index_input.setPlaceholderText("1") # Default to 1
        self.start_index_input.setText("1")
        self.start_index_input.setFont(QFont("Segoe UI", 9))
        self.start_index_input.setStyleSheet(self.get_input_style())
        self.start_index_input.setFixedWidth(80) # Make it smaller
        start_index_layout.addWidget(start_label)
        start_index_layout.addWidget(self.start_index_input)

        end_index_layout = QVBoxLayout()
        end_label = QLabel("End Video Index (0 for all):")
        end_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        end_label.setStyleSheet("color: #ecf0f1;")
        self.end_index_input = QLineEdit()
        self.end_index_input.setPlaceholderText("0") # Default to 0 (meaning all)
        self.end_index_input.setText("0")
        self.end_index_input.setFont(QFont("Segoe UI", 9))
        self.end_index_input.setStyleSheet(self.get_input_style())
        self.end_index_input.setFixedWidth(80) # Make it smaller
        end_index_layout.addWidget(end_label)
        end_index_layout.addWidget(self.end_index_input)

        index_layout.addLayout(start_index_layout)
        index_layout.addLayout(end_index_layout)
        index_layout.addStretch(1) # Push inputs to the left

        input_layout.addLayout(index_layout) # Add the combined layout

        # Style Selection
        category_layout = QVBoxLayout()
        category_label = QLabel("Refinement Style:")
        category_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        category_label.setStyleSheet("color: #ecf0f1;")
        self.category_combo = QComboBox()
        self.category_combo.addItems(list(self.prompts.keys())) 
        self.category_combo.setCurrentText(self.selected_category) 
        self.category_combo.currentIndexChanged.connect(self.category_changed) 
        self.category_combo.setStyleSheet(self.get_combobox_style())
        category_layout.addWidget(category_label)
        category_layout.addWidget(self.category_combo)
        input_layout.addLayout(category_layout)
        # Chunk Size Slider Section
        chunk_size_layout = QVBoxLayout()

        
        chunk_size_layout.setSpacing(2)  
        chunk_size_layout.setContentsMargins(5, 5, 5, 5)  

        chunk_size_label = QLabel("Chunk Size:")
        chunk_size_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        chunk_size_label.setStyleSheet("color: #ecf0f1; margin-bottom: 4px;")  
        chunk_size_layout.addWidget(chunk_size_label)

        self.chunk_size_slider = QSlider(Qt.Horizontal)
        self.chunk_size_slider.setMinimum(5000) # Increased minimum slightly
        self.chunk_size_slider.setMaximum(500000) # <<< Increased maximum significantly
        self.chunk_size_slider.setValue(self.DEFAULT_CHUNK_SIZE) # <<< Use constant for initial value
        self.chunk_size_slider.valueChanged.connect(self.update_chunk_size_label)
        self.chunk_size_slider.setStyleSheet("""
            QSlider {
                padding: 0px;  # Reduced padding
            }
            QSlider::groove:horizontal {
                height: 4px;
                margin: 2px 0;  # Add vertical margin
            }
            QSlider::handle:horizontal {
                width: 12px;
                margin: -6px 0px;
            }
        """)
        chunk_size_layout.addWidget(self.chunk_size_slider)

        self.chunk_size_value_label = QLabel(str(self.DEFAULT_CHUNK_SIZE)) # <<< Use constant for initial label
        self.chunk_size_value_label.setFont(QFont("Segoe UI", 10))
        self.chunk_size_value_label.setStyleSheet("color: #ecf0f1; margin-top: 4px;")
        chunk_size_layout.addWidget(self.chunk_size_value_label)

        # Updated description text referencing the default value
        chunk_size_description = QLabel(f"(Maximum number of words given to Gemini per API call. Default: {self.DEFAULT_CHUNK_SIZE} words, approx 1/10 of 1M tokens context window). Adjust based on task and content length. Larger chunks may be faster but risk API limits or losing detail for some tasks.")
        chunk_size_description.setFont(QFont("Segoe UI", 8))
        chunk_size_description.setStyleSheet("""
            color: #bdc3c7;
            margin-top: 18px;  
            padding: 2px;
        """)
        chunk_size_description.setWordWrap(True)
        chunk_size_layout.addWidget(chunk_size_description)

        input_layout.addLayout(chunk_size_layout)



        


        # File Inputs
        self.create_file_input(input_layout, "   Transcript Output:", "Choose File",
                             "transcript_file_input", self.select_transcript_output_file)
        self.create_file_input(input_layout, "   Gemini Output:", "Choose File",
                             "gemini_file_input", self.select_gemini_output_file)

        # API Key Input
        api_key_layout = QVBoxLayout()
        api_key_label = QLabel("Gemini API Key:")
        api_key_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        api_key_label.setStyleSheet("color: #ecf0f1;")
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Enter your Gemini API key")
        self.api_key_input.setFont(QFont("Segoe UI", 9))
        self.api_key_input.setStyleSheet(self.get_input_style())
        self.api_key_input.setEchoMode(QLineEdit.Password)

        self.api_key_input.setText(os.environ.get("API_KEY", ""))

        api_key_layout.addWidget(api_key_label)
        api_key_layout.addWidget(self.api_key_input)
        input_layout.addLayout(api_key_layout)

        main_layout.addWidget(input_container)

        # Progress Section
        progress_container = QWidget()
        progress_container.setStyleSheet("background-color: #34495e; border-radius: 10px; padding: 10px;")
        progress_layout = QVBoxLayout(progress_container)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background: #2c3e50;
                border: 2px solid #3498db;
                border-radius: 5px;
                text-align: center;
                color: white;
                font-size: 12px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3498db, stop:1 #2ecc71);
                border-radius: 3px;
            }
        """)
        progress_layout.addWidget(self.progress_bar)

        # Status Display
        self.status_display = QTextEdit()
        self.status_display.setReadOnly(True)
        self.status_display.setStyleSheet("""
            background-color: #2c3e50;
            border: 2px solid #3498db;
            border-radius: 5px;
            color: #ecf0f1;
            font-size: 12px;
            padding: 8px;
        """)
        progress_layout.addWidget(self.status_display)
        main_layout.addWidget(progress_container)

        # Control Buttons
        control_layout = QHBoxLayout()
        control_layout.setSpacing(20)

        self.extract_button = QPushButton("Start Processing")
        self.extract_button.setStyleSheet(self.get_button_style("#2ecc71", "#27ae60"))
        self.extract_button.clicked.connect(self.start_extraction_and_refinement)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setStyleSheet(self.get_button_style("#e74c3c", "#c0392b"))
        self.cancel_button.clicked.connect(self.cancel_processing)
        self.cancel_button.setEnabled(False)

        control_layout.addStretch(1)
        control_layout.addWidget(self.extract_button)
        control_layout.addWidget(self.cancel_button)
        control_layout.addStretch(1)
        main_layout.addLayout(control_layout)

        self.central_widget.setLayout(main_layout)
        self.center()

    def create_file_input(self, parent_layout, label_text, button_text, field_name, handler):
        layout = QHBoxLayout()
        
        
        input_field = QLineEdit()
        input_field.setObjectName(field_name)
        input_field.setReadOnly(True)
        input_field.setPlaceholderText(f"Select {label_text.split(':')[0]} file")
        input_field.setStyleSheet(self.get_input_style())

        button = QPushButton(button_text)
        button.setStyleSheet(self.get_button_style("#3498db", "#2980b9"))
        button.clicked.connect(handler)

        layout.addWidget(input_field)
        layout.addWidget(button)

        font = QFont("Segoe UI", 10, QFont.Bold)
        label = QLabel(label_text)
        font = QFont("Segoe UI", 10, QFont.Bold)  # Family, size, weight
        label.setFont(font)


        
        label.setStyleSheet("padding: 0px;")

        parent_layout.addWidget(label)
        parent_layout.addLayout(layout)


        setattr(self, field_name, input_field)

    def get_input_style(self):
        return """
            QLineEdit {
                background: #34495e;
                border: 2px solid #3498db;
                border-radius: 5px;
                color: #ecf0f1;
                padding: 2px;
            }
            QLineEdit:disabled {
                background: #2c3e50;
                border-color: #7f8c8d;
            }
        """

    def get_button_style(self, color1, color2):
        return f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {color1}, stop:1 {color2});
                color: white;
                border: none;
                border-radius: 5px;
                padding: 12px 24px;
                font-size: 15px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {color2}, stop:1 {color1});
            }}
            QPushButton:disabled {{
                background: #95a5a6;
                color: #7f8c8d;
            }}
        """

    def apply_dark_mode(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2c3e50;
            }
            QLabel {
                color: #ecf0f1;
            }
        """)

    def center(self):
        frame = self.frameGeometry()
        center_point = QApplication.primaryScreen().availableGeometry().center()
        frame.moveCenter(center_point)
        self.move(frame.topLeft())

    def validate_inputs(self):
        url_text = self.url_input.text() 
        
        if not (url_text.startswith("https://www.youtube.com/playlist") or
            url_text.startswith("https://www.youtube.com/watch?v=")):

            msg_box = QMessageBox()
            msg_box.setStyleSheet("color: #ecf0f1; background-color: #34495e;") # Style QMessageBox
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setText("Please enter a valid YouTube playlist URL")
            msg_box.setWindowTitle("Invalid URL")
            msg_box.exec_()
            return False

        if not self.transcript_file_input.text().endswith(".txt"):
            msg_box = QMessageBox()
            msg_box.setStyleSheet("color: #ecf0f1; background-color: #34495e;") # Style QMessageBox
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setText("Transcript output file must be a .txt file")
            msg_box.setWindowTitle("Invalid File")
            msg_box.exec_()
            return False

        if not self.gemini_file_input.text().endswith(".txt"):
            msg_box = QMessageBox()
            msg_box.setStyleSheet("color: #ecf0f1; background-color: #34495e;") # Style QMessageBox
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setText("Gemini output file must be a .txt file")
            msg_box.setWindowTitle("Invalid File")
            msg_box.exec_()
            return False

        if not self.api_key_input.text().strip():
            msg_box = QMessageBox()
            msg_box.setStyleSheet("color: #ecf0f1; background-color: #34495e;") # Style QMessageBox
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setText("Please enter your Gemini API key")
            msg_box.setWindowTitle("API Key Required")
            msg_box.exec_()
            return False

        if not self.language_input.text().strip(): # Validate Language Input
            msg_box = QMessageBox()
            msg_box.setStyleSheet("color: #ecf0f1; background-color: #34495e;") # Style QMessageBox
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setText("Please specify the output language")
            msg_box.setWindowTitle("Language Required")
            msg_box.exec_()
            return False

        # Validate Start/End Index (NEW)
        try:
            start_index_str = self.start_index_input.text().strip()
            self.start_index = int(start_index_str) if start_index_str else 1 # Default to 1 if empty
            if self.start_index < 1:
                raise ValueError("Start index must be 1 or greater.")

            end_index_str = self.end_index_input.text().strip()
            self.end_index = int(end_index_str) if end_index_str else 0 # Default to 0 if empty
            if self.end_index != 0 and self.end_index < self.start_index:
                raise ValueError("End index must be 0 (for all) or greater than/equal to start index.")

        except ValueError as e:
            msg_box = QMessageBox()
            msg_box.setStyleSheet("color: #ecf0f1; background-color: #34495e;")
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setText(f"Invalid Start/End Index: {e}")
            msg_box.setWindowTitle("Invalid Index")
            msg_box.exec_()
            return False

        return True # If all validations pass

    def set_processing_state(self, processing):
        self.is_processing = processing
        self.extract_button.setEnabled(not processing)
        self.cancel_button.setEnabled(processing)

        inputs = [self.url_input, self.transcript_file_input,
                self.gemini_file_input, self.api_key_input, self.language_input]
        for input_field in inputs:
            input_field.setReadOnly(processing)

    def select_gemini_model(self):
        msg_box = QMessageBox()
        msg_box.setStyleSheet("color: #ecf0f1; background-color: #34495e;") # Style QMessageBox
        msg_box.setWindowTitle("Select Gemini Model")
        msg_box.setText("Choose a Gemini model for refinement:")

        model_combo = QComboBox()
        model_combo.addItems(self.available_models)
        model_combo.setCurrentText(self.selected_model_name) 

        layout = QVBoxLayout()
        layout.addWidget(model_combo)
        widget = QWidget()
        widget.setLayout(layout)
        msg_box.layout().addWidget(widget, 1, 0, msg_box.layout().rowCount(), 1) 

        ok_button = msg_box.addButton(QMessageBox.Ok)
        cancel_button = msg_box.addButton(QMessageBox.Cancel)

        msg_box.exec_()

        if msg_box.clickedButton() == ok_button:
            return model_combo.currentText()
        else:
            return None


    def start_extraction_and_refinement(self):
        if not self.validate_inputs():
            return

        selected_model = self.select_gemini_model()
        if selected_model:
            self.selected_model_name = selected_model
        else:
            return # User cancelled model selection

        self.set_processing_state(True)
        self.progress_bar.setValue(0)
        self.status_display.clear()

        transcript_output = self.transcript_file_input.text() or \
                          f"transcript_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"

        self.extraction_thread = TranscriptExtractionThread(
            self.url_input.text(),
            transcript_output,
            self.start_index,
            self.end_index
        )

        self.extraction_thread.progress_update.connect(self.progress_bar.setValue)
        self.extraction_thread.status_update.connect(self.update_status)
        self.extraction_thread.extraction_complete.connect(self.start_gemini_processing)
        self.extraction_thread.error_occurred.connect(self.handle_error)

        self.status_display.append("<font color='#3498db'>Starting transcript extraction...</font>")
        self.extraction_thread.start()

    def start_gemini_processing(self, transcript_file):
        self.progress_bar.setValue(0) # Reset progress bar for Gemini processing
        self.status_display.append("<font color='#2ecc71'>Transcript extraction complete! Starting Gemini processing...</font>")

        output_language = self.language_input.text() # Get language from input field
        current_chunk_size = self.chunk_size_slider.value()
        selected_prompt = self.prompts[self.selected_category]
        self.gemini_thread = GeminiProcessingThread(
            transcript_file,
            self.gemini_file_input.text(),
            self.api_key_input.text(),
            self.selected_model_name, # Pass selected model name
            output_language, # Pass output language
            chunk_size=current_chunk_size,
            prompt=selected_prompt
        )

        self.gemini_thread.progress_update.connect(self.update_gemini_progress) # Use separate progress update for Gemini
        self.gemini_thread.status_update.connect(self.update_status)
        self.gemini_thread.processing_complete.connect(self.handle_success)
        self.gemini_thread.error_occurred.connect(self.handle_error)

        self.gemini_thread.start()

    def update_gemini_progress(self, progress_percent):
        # Offset the progress bar to start after extraction (assuming extraction takes up to 50%)
        
        gemini_progress = progress_percent 
        self.progress_bar.setValue(gemini_progress)


    def update_status(self, message):
        color = "#3498db" if "extraction" in message else "#2ecc71"
        self.status_display.append(f"<font color='{color}'>{message}</font>")

    def handle_success(self, output_file):
        self.set_processing_state(False)
        msg_box = QMessageBox()
        msg_box.setStyleSheet("color: #ecf0f1; background-color: #34495e;") # Style QMessageBox
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setText(f"Processing complete!\nOutput saved to: {output_file}")
        msg_box.setWindowTitle("Success")
        msg_box.exec_()
        self.progress_bar.setValue(100)

    def handle_error(self, error):
        self.set_processing_state(False)
        msg_box = QMessageBox()
        msg_box.setStyleSheet("color: #ecf0f1; background-color: #34495e;") # Style QMessageBox
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setText(error)
        msg_box.setWindowTitle("Error")
        msg_box.exec_()
        self.progress_bar.setValue(0)

    def cancel_processing(self):
        if self.extraction_thread and self.extraction_thread.isRunning():
            self.extraction_thread.stop()
            self.extraction_thread.quit()
            self.extraction_thread.wait()

        if self.gemini_thread and self.gemini_thread.isRunning():
            self.gemini_thread.stop()
            self.gemini_thread.quit()
            self.gemini_thread.wait()

        self.set_processing_state(False)
        self.status_display.append("<font color='#e74c3c'>Processing cancelled by user</font>")
        self.progress_bar.setValue(0)

    def select_transcript_output_file(self):
        self.select_output_file("Select Transcript Output File", self.transcript_file_input)

    def select_gemini_output_file(self):
        self.select_output_file("Select Gemini Output File", self.gemini_file_input)

    def select_output_file(self, title, field):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(
            self, title, "", "Text Files (*.txt);;All Files (*)", options=options)
        if file_path:
            if not (file_path.endswith(".txt") ):
                file_path += ".txt"  # Default to .txt if no extension is given
            field.setText(file_path)


class TranscriptExtractionThread(QThread):
    progress_update = pyqtSignal(int)
    status_update = pyqtSignal(str)
    extraction_complete = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, playlist_url, output_file, start_index=1, end_index=0):
        super().__init__()
        self.playlist_url = playlist_url
        self.output_file = output_file
        self.start_index = start_index
        self.end_index = end_index # 0 means process all/to the end
        self._is_running = True

    def run(self):
        try:
            url = self.playlist_url
            playlist_name = "Unknown Playlist/Video" # Default name
            all_video_urls = [] # Renamed to reflect it holds all URLs initially
            original_total_videos = 0

            if "playlist?list=" in url: # Check if it's a playlist URL
                try:
                    playlist = Playlist(url)
                    try:
                        all_video_urls = list(playlist.video_urls) # Get all URLs
                        original_total_videos = len(all_video_urls)
                        playlist_name = playlist.title
                        self.status_update.emit(f"Found playlist: {playlist_name} with {original_total_videos} videos.")
                    except KeyError as ke:
                        error_msg = f"Extraction error (Accessing Playlist Details): {str(ke)}. YouTube structure likely changed. Try updating pytube (`pip install --upgrade pytube`) or check pytube issues."
                        self.error_occurred.emit(error_msg)
                        return # Stop processing if we can't get video details
                    except Exception as access_e: # Catch other potential errors accessing properties
                         error_msg = f"Extraction error (Accessing Playlist Properties): {str(access_e)}. URL: {url}"
                         self.error_occurred.emit(error_msg)
                         return

                except KeyError as ke:
                     error_msg = f"Extraction error (Initializing Playlist): {str(ke)}. YouTube structure likely changed. Try updating pytube (`pip install --upgrade pytube`) or check pytube issues."
                     self.error_occurred.emit(error_msg)
                     return # Stop processing if playlist object fails
                except Exception as init_e: # Catch other potential errors during Playlist initialization
                    error_msg = f"Extraction error (Initializing Playlist Object): {str(init_e)}. URL: {url}"
                    self.error_occurred.emit(error_msg)
                    return

            elif "watch?v=" in url: # Check if it's a single video URL
                all_video_urls = [url]
                original_total_videos = 1
                # Try to get video title for single video case (optional, less likely to fail here)
                try:
                    from pytube import YouTube
                    yt = YouTube(url)
                    playlist_name = yt.title
                    self.status_update.emit(f"Processing single video: {playlist_name}")
                except Exception as single_title_e:
                    self.status_update.emit(f"Processing single video (Could not get title: {str(single_title_e)}). URL: {url}")
                    playlist_name = "Single Video" # Fallback name
            else:
                self.error_occurred.emit(f"Invalid URL format: {url}")
                return

            if not all_video_urls: # If we failed to get video_urls earlier
                self.error_occurred.emit(f"Could not retrieve video URLs for {url}. See previous errors.")
                return

            # --- Slicing Logic (NEW) ---
            # Adjust for 0-based slicing and user's 1-based input
            slice_start = self.start_index - 1
            if slice_start < 0:
                slice_start = 0 # Ensure start is not negative

            if self.end_index == 0: # 0 means process to the end
                slice_end = None # Slicing with None goes to the end
            else:
                slice_end = self.end_index # Already 1-based, slice goes up to but not including end

            # Apply the slice
            video_urls_to_process = all_video_urls[slice_start:slice_end]
            total_videos = len(video_urls_to_process) # This is the number we'll actually process

            if total_videos == 0:
                 self.status_update.emit("No videos found in the specified range.")
                 # Emit completion signal with empty file or handle as needed
                 # For now, just write header and complete
                 with open(self.output_file, 'w', encoding='utf-8') as f:
                     f.write(f"Playlist Name: {playlist_name}\n")
                     f.write(f"(No videos processed for range {self.start_index} to {self.end_index if self.end_index != 0 else 'End'})\n")
                 self.extraction_complete.emit(self.output_file)
                 return


            self.status_update.emit(f"Processing {total_videos} videos (range {self.start_index} to {self.end_index if self.end_index != 0 else 'End'} of {original_total_videos}).")
            # --- End Slicing Logic ---


            with open(self.output_file, 'w', encoding='utf-8') as f:
                f.write(f"Playlist Name: {playlist_name}\n")
                f.write(f"Processing Range: {self.start_index} to {self.end_index if self.end_index != 0 else 'End'}\n\n") # Add range info

                # Iterate over the *sliced* list
                for index, video_url in enumerate(video_urls_to_process, 1):
                    if not self._is_running:
                        return

                    try:
                        video_id = video_url.split("?v=")[1].split("&")[0]
                        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
                        transcript = ' '.join([transcript['text'] for transcript in transcript_list])

                        f.write(f"Video URL: {video_url}\n")
                        f.write(transcript + '\n\n')

                        # Progress is now based on the sliced list size
                        progress_percent = int((index / total_videos) * 100)
                        self.progress_update.emit(progress_percent)
                        # Use the actual video number from the original list for status if desired,
                        # but using 'index' relative to the slice is simpler and clearer for progress.
                        original_index = slice_start + index # Calculate original index if needed for logs/status
                        self.status_update.emit(f"Extracted transcript for video {index}/{total_videos} (Original Playlist Index: {original_index})")
                    except Exception as video_error:
                        original_index = slice_start + index
                        self.status_update.emit(f"Error processing video {index}/{total_videos} (Original Playlist Index: {original_index}, URL: {video_url}): {str(video_error)}")


            self.extraction_complete.emit(self.output_file)
        except Exception as e: # General fallback catch
            # Avoid catching the specific KeyErrors again if they were handled
            if not isinstance(e, KeyError):
                 self.error_occurred.emit(f"General extraction error: {str(e)}")

    def stop(self):
        self._is_running = False


class GeminiProcessingThread(QThread):
    progress_update = pyqtSignal(int)
    status_update = pyqtSignal(str)
    processing_complete = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    # Default chunk size set in MainWindow.__init__ before creating thread instances
    chunk_size = MainWindow.DEFAULT_CHUNK_SIZE # Referencing the constant


    def __init__(self, input_file, output_file, api_key, selected_model_name, output_language, chunk_size,prompt): 
        super().__init__()
        self.input_file = input_file
        self.output_file = output_file
        self.api_key = api_key
        # Use the chunk_size passed from MainWindow, which originates from the slider
        # The initial/default value of the slider is now set by MainWindow.DEFAULT_CHUNK_SIZE
        self.chunk_size = chunk_size
        self.selected_model_name = selected_model_name
        self.output_language = output_language
        self.prompt = prompt
        self._is_running = True
        logging.basicConfig(filename='gemini_processing.log', level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')


    def run(self):
        try:
            genai.configure(api_key=self.api_key)
            video_chunks = self.split_videos(self.input_file) # input_file is transcript file path
            final_output_path = self.output_file
            response_file_path = self.output_file.replace(".txt", "_temp_response.txt")
            total_videos = len(video_chunks) -1 if len(video_chunks) > 1 else 0 # Calculate total videos for progress

            with open(response_file_path, "w", encoding="utf-8") as response_file:
                response_file.write("")

            for video_index, video_chunk in enumerate(video_chunks[1:]): # Start from 1 to skip empty chunk
                if not self._is_running: # Check for stop signal
                    return
                self.status_update.emit(f"\nProcessing Video {video_index + 1}/{total_videos}: Preview: {video_chunk[:50]}...")
                word_count = len(video_chunk.split())
                self.status_update.emit(f"Word Count: {word_count} words")
                self.status_update.emit(f"Chunk Size: {self.chunk_size} words")
                

                video_transcript_chunks = self.split_text_into_chunks(video_chunk, self.chunk_size)
                previous_response = ""
                for chunk_index, chunk in enumerate(video_transcript_chunks):
                    if not self._is_running: # Check for stop signal inside inner loop
                        return
                    if previous_response:
                        context_prompt = (
                            "The following text is a continuation... "
                            f"Previous response:\n{previous_response}\n\nNew text to process(Do Not Repeat the Previous response:):\n"
                        )
                    else:
                        context_prompt = ""

                    # Replace [Language] with user specified language
                    formatted_prompt = self.prompt.replace("[Language]", self.output_language)
                    full_prompt = f"{context_prompt}{formatted_prompt}\n\n{chunk}"

                    model = genai.GenerativeModel(self.selected_model_name) # Use selected model

                    self.status_update.emit(f"Generating Gemini response for Video {video_index + 1}/{total_videos}, Chunk {chunk_index + 1}/{len(video_transcript_chunks)}, please wait...")
                    response = model.generate_content(full_prompt)

                    with open(response_file_path, "a", encoding="utf-8") as response_file:
                        response_file.write(response.text + "\n\n")
                    previous_response = response.text
                    self.status_update.emit(f"Chunk {chunk_index + 1}/{len(video_transcript_chunks)} processed and saved to temp file.")

                self.status_update.emit(f"All Gemini responses for video {video_index + 1} have been saved to temp file.")

                with open(response_file_path, "r", encoding="utf-8") as response_file:
                    video_response_content = response_file.read()

                with open(final_output_path, "a", encoding="utf-8") as final_output_file:
                    final_output_file.write(f"Video URL: {video_chunks[video_index+1].splitlines()[0].replace('Video URL: ', '')}\n") # Add Video URL as heading
                    final_output_file.write(video_response_content + "\n\n")

                with open(response_file_path, "w", encoding="utf-8") as response_file:
                    response_file.write("") # Clear temp file

                progress_percent = int(((video_index + 1) / total_videos) * 100) if total_videos > 0 else 100 # Calculate Gemini progress
                self.progress_update.emit(progress_percent) # Emit Gemini progress
                self.status_update.emit(f"Final Gemini output for video {video_index + 1} appended to {final_output_path}")

            self.status_update.emit(f"All Gemini responses for all videos have been saved to {final_output_path}.")
            self.processing_complete.emit(final_output_path)
            self.progress_update.emit(100) # Ensure progress bar reaches 100% at the end
        except Exception as e:
            error_message = f"Gemini error: {str(e)}"
            self.error_occurred.emit(error_message)
            logging.error(error_message)


    def split_text_into_chunks(self, text, chunk_size, min_chunk_size=500):
        words = text.split()
        chunks = [" ".join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]
        if len(chunks) > 1 and len(chunks[-1].split()) < min_chunk_size:
            chunks[-2] += " " + chunks[-1]
            chunks.pop()
        return chunks

    def split_videos(self, file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
        video_chunks = re.split(r'(?=Video URL:)', content) # Split by Video URL: from transcript file
        video_chunks = [chunk.strip() for chunk in video_chunks if chunk.strip()]
        return video_chunks

    def stop(self):
        self._is_running = False


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec_())