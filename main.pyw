import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QProgressBar, QTextEdit, QFileDialog, QMessageBox,
                             QSlider, QGroupBox, QCheckBox)  # CHANGED: Removed QComboBox, added QCheckBox
from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QFont, QColor
from datetime import datetime
from pytubefix import Playlist, YouTube
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai
import re
import logging
import os
from dotenv import load_dotenv
from builtins import KeyError
load_dotenv(".env")


class MainWindow(QMainWindow):
    DEFAULT_CHUNK_SIZE = 70000  # Define default chunk size as a class variable

    def __init__(self):
        super().__init__()
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # --- CHANGED: Moved from category_combo to multiple checkboxes. ---
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
            Format the entire response using Markdown syntax.
            Text:
            """,

            "Summary": """Summarize the following transcript into a concise and informative summary. 
            Identify the core message, main arguments, and key pieces of information presented in the video.
            The summary should capture the essence of the video's content in a clear and easily understandable way.
            Aim for a summary that is shorter than the original transcript but still accurately reflects its key points.  
            Focus on conveying the most important information and conclusions.
            All output must be generated entirely in [Language]. Do not use any other language at any point in the response. Do not include this unorganized text into your response.
            Format the entire response using Markdown syntax.
            Text: """,

            "Educational": """Transform the following transcript into a comprehensive educational text, resembling a textbook chapter. Structure the content with clear headings, subheadings, and bullet points to enhance readability and organization for educational purposes.

            Crucially, identify any technical terms, jargon, or concepts that are mentioned but not explicitly explained within the transcript. For each identified term, provide a concise definition (no more than two sentences) formatted as a blockquote.  Integrate these definitions strategically within the text, ideally near the first mention of the term, to enhance understanding without disrupting the flow.

            Ensure the text is highly informative, accurate, and retains all the original details and nuances of the transcript. The goal is to create a valuable educational resource that is easy to study and understand.

            All output must be generated entirely in [Language]. Do not use any other language at any point in the response. Do not use any other language at any point in the response. Do not include this unorganized text into your response.
            Format the entire response using Markdown syntax, including the blockquotes for definitions.

            Text:""",

            "Narrative Rewriting": """Rewrite the following transcript into an engaging narrative or story format. Transform the factual or conversational content into a more captivating and readable piece, similar to a short story or narrative article.

            While rewriting, maintain a close adherence to the original subjects and information presented in the video. Do not deviate significantly from the core topics or introduce unrelated elements.  The goal is to enhance engagement and readability through storytelling techniques without altering the fundamental content or message of the video.  Use narrative elements like descriptive language, scene-setting (if appropriate), and a compelling flow to make the information more accessible and enjoyable.

            All output must be generated entirely in [Language]. Do not use any other language at any point in the response. Do not include this unorganized text into your response.
            Format the entire response using Markdown syntax for appropriate emphasis or structure (like paragraph breaks).

            Text:""",

            "Q&A Generation": """Generate a set of questions and answers based on the following transcript for self-assessment or review.  For each question, create a corresponding answer.

            Format each question as a level 3 heading using Markdown syntax (### Question Text). Immediately following each question, provide the answer.  This format is designed for foldable sections, allowing users to easily hide and reveal answers for self-testing.

            Ensure the questions are relevant to the key information and concepts in the transcript and that the answers are accurate and comprehensive based on the video content.

            All output must be generated entirely in [Language]. Do not use any other language at any point in the response. Do not include this unorganized text into your response.
            Format the entire response using Markdown syntax as specified.

            Text:"""
        }

        self.extraction_thread = None
        self.gemini_thread = None
        self.is_processing = False

        self.available_models = ["gemini-2.5-flash-preview-04-17", "gemini-2.5-pro-preview-03-25", "gpt-4.1-mini"]
        self.selected_model_name = "gemini-2.5-flash-preview-04-17"

        # Set the class variable default chunk size using the constant
        GeminiProcessingThread.chunk_size = self.DEFAULT_CHUNK_SIZE

        self.initUI()


    def get_combobox_style(self):
        """No longer used for QComboBox, but kept in case you need a similar style for checkboxes or other combos."""
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
            QComboBox:on {
                border-bottom-left-radius: 0px;
                border-bottom-right-radius: 0px;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left-width: 1px;
                border-left-color: darkgray;
                border-left-style: solid;
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
            }
            QComboBox::down-arrow {
                image: url(down_arrow.png);
            }
            QComboBox::down-arrow:on {
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

    @pyqtSlot(int)
    def update_chunk_size_label(self, value):
        self.chunk_size_value_label.setText(str(value))

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

        # Start/End Video Index Input
        index_layout = QHBoxLayout()

        start_index_layout = QVBoxLayout()
        start_label = QLabel("Start Video Index:")
        start_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        start_label.setStyleSheet("color: #ecf0f1;")
        self.start_index_input = QLineEdit()
        self.start_index_input.setPlaceholderText("1")
        self.start_index_input.setText("1")
        self.start_index_input.setFont(QFont("Segoe UI", 9))
        self.start_index_input.setStyleSheet(self.get_input_style())
        self.start_index_input.setFixedWidth(80)
        start_index_layout.addWidget(start_label)
        start_index_layout.addWidget(self.start_index_input)

        end_index_layout = QVBoxLayout()
        end_label = QLabel("End Video Index (0 for all):")
        end_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        end_label.setStyleSheet("color: #ecf0f1;")
        self.end_index_input = QLineEdit()
        self.end_index_input.setPlaceholderText("0")
        self.end_index_input.setText("0")
        self.end_index_input.setFont(QFont("Segoe UI", 9))
        self.end_index_input.setStyleSheet(self.get_input_style())
        self.end_index_input.setFixedWidth(80)
        end_index_layout.addWidget(end_label)
        end_index_layout.addWidget(self.end_index_input)

        index_layout.addLayout(start_index_layout)
        index_layout.addLayout(end_index_layout)
        index_layout.addStretch(1)
        input_layout.addLayout(index_layout)

        # --- CHANGED: Replaced single ComboBox with multiple checkboxes in a QGroupBox ---
        style_groupbox = QGroupBox("Refinement Styles (Select one or more)")
        style_groupbox.setStyleSheet("QGroupBox { color: #ecf0f1; font-weight: bold; }")
        style_layout = QVBoxLayout()

        # Store checkboxes in a dict for easy reference
        self.style_checkboxes = {}
        for style_name in self.prompts.keys():
            cb = QCheckBox(style_name)
            cb.setStyleSheet("color: #ecf0f1; font-size: 10pt;")
            style_layout.addWidget(cb)
            self.style_checkboxes[style_name] = cb

        style_groupbox.setLayout(style_layout)
        input_layout.addWidget(style_groupbox)
        # --- END CHANGED ---

        # Chunk Size Slider Section
        chunk_size_layout = QVBoxLayout()
        chunk_size_layout.setSpacing(2)
        chunk_size_layout.setContentsMargins(5, 5, 5, 5)

        chunk_size_label = QLabel("Chunk Size:")
        chunk_size_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        chunk_size_label.setStyleSheet("color: #ecf0f1; margin-bottom: 4px;")
        chunk_size_layout.addWidget(chunk_size_label)

        self.chunk_size_slider = QSlider(Qt.Horizontal)
        self.chunk_size_slider.setMinimum(5000)
        self.chunk_size_slider.setMaximum(500000)
        self.chunk_size_slider.setValue(self.DEFAULT_CHUNK_SIZE)
        self.chunk_size_slider.valueChanged.connect(self.update_chunk_size_label)
        self.chunk_size_slider.setStyleSheet("""
            QSlider {
                padding: 0px;
            }
            QSlider::groove:horizontal {
                height: 4px;
                margin: 2px 0;
            }
            QSlider::handle:horizontal {
                width: 12px;
                margin: -6px 0px;
            }
        """)
        chunk_size_layout.addWidget(self.chunk_size_slider)

        self.chunk_size_value_label = QLabel(str(self.DEFAULT_CHUNK_SIZE))
        self.chunk_size_value_label.setFont(QFont("Segoe UI", 10))
        self.chunk_size_value_label.setStyleSheet("color: #ecf0f1; margin-top: 4px;")
        chunk_size_layout.addWidget(self.chunk_size_value_label)

        chunk_size_description = QLabel(
            f"(Maximum number of words given to Gemini per API call. Default: {self.DEFAULT_CHUNK_SIZE} words, approx 1/10 of 1M tokens context window)."
            " Adjust based on task and content length. Larger chunks may be faster but risk API limits or losing detail."
        )
        chunk_size_description.setFont(QFont("Segoe UI", 8))
        chunk_size_description.setStyleSheet("color: #bdc3c7; margin-top: 18px; padding: 2px;")
        chunk_size_description.setWordWrap(True)
        chunk_size_layout.addWidget(chunk_size_description)

        input_layout.addLayout(chunk_size_layout)

        # File Inputs
        self.create_file_input(input_layout,
                               "   Transcript Output File (Optional):",
                               "Choose File",
                               "transcript_file_input",
                               self.select_transcript_output_file)

        self.create_directory_input(input_layout,
                                    "   Summary Output Folder:",
                                    "Choose Folder",
                                    "summary_output_dir_input",
                                    self.select_summary_output_directory)

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
        input_field.setPlaceholderText("Optional: Select file or leave blank for default")
        input_field.setStyleSheet(self.get_input_style())

        button = QPushButton(button_text)
        button.setStyleSheet(self.get_button_style("#3498db", "#2980b9"))
        button.clicked.connect(handler)

        layout.addWidget(input_field)
        layout.addWidget(button)

        font = QFont("Segoe UI", 10, QFont.Bold)
        label = QLabel(label_text)
        label.setFont(font)
        label.setStyleSheet("padding: 0px;")

        parent_layout.addWidget(label)
        parent_layout.addLayout(layout)

        setattr(self, field_name, input_field)

    def create_directory_input(self, parent_layout, label_text, button_text, field_name, handler):
        layout = QHBoxLayout()

        input_field = QLineEdit()
        input_field.setObjectName(field_name)
        input_field.setReadOnly(True)
        input_field.setPlaceholderText(f"Select {label_text.split(':')[0].strip()} folder")
        input_field.setStyleSheet(self.get_input_style())

        button = QPushButton(button_text)
        button.setStyleSheet(self.get_button_style("#3498db", "#2980b9"))
        button.clicked.connect(handler)

        layout.addWidget(input_field)
        layout.addWidget(button)

        font = QFont("Segoe UI", 10, QFont.Bold)
        label = QLabel(label_text)
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
            msg_box.setStyleSheet("color: #ecf0f1; background-color: #34495e;")
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setText("Please enter a valid YouTube playlist URL or single video URL.")
            msg_box.setWindowTitle("Invalid URL")
            msg_box.exec_()
            return False

        # Validate Transcript file only if provided
        transcript_file_path = self.transcript_file_input.text().strip()
        if transcript_file_path and not transcript_file_path.endswith(".txt"):
            msg_box = QMessageBox()
            msg_box.setStyleSheet("color: #ecf0f1; background-color: #34495e;")
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setText("If specified, Transcript output file must be a .txt file")
            msg_box.setWindowTitle("Invalid File")
            msg_box.exec_()
            return False

        # Validate Summary output directory
        summary_dir = self.summary_output_dir_input.text().strip()
        if not summary_dir:
            msg_box = QMessageBox()
            msg_box.setStyleSheet("color: #ecf0f1; background-color: #34495e;")
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setText("Please select a Summary Output Folder.")
            msg_box.setWindowTitle("Output Folder Required")
            msg_box.exec_()
            return False
        if not os.path.isdir(summary_dir):
            msg_box = QMessageBox()
            msg_box.setStyleSheet("color: #ecf0f1; background-color: #34495e;")
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setText("The selected Summary Output path is not a valid folder.")
            msg_box.setWindowTitle("Invalid Folder")
            msg_box.exec_()
            return False

        if not self.api_key_input.text().strip():
            msg_box = QMessageBox()
            msg_box.setStyleSheet("color: #ecf0f1; background-color: #34495e;")
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setText("Please enter your Gemini API key")
            msg_box.setWindowTitle("API Key Required")
            msg_box.exec_()
            return False

        if not self.language_input.text().strip():
            msg_box = QMessageBox()
            msg_box.setStyleSheet("color: #ecf0f1; background-color: #34495e;")
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setText("Please specify the output language")
            msg_box.setWindowTitle("Language Required")
            msg_box.exec_()
            return False

        # Validate that at least one style checkbox is checked
        if not any(cb.isChecked() for cb in self.style_checkboxes.values()):
            msg_box = QMessageBox()
            msg_box.setStyleSheet("color: #ecf0f1; background-color: #34495e;")
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setText("Please select at least one Refinement Style.")
            msg_box.setWindowTitle("No Style Selected")
            msg_box.exec_()
            return False

        # Validate Start/End Index
        try:
            start_index_str = self.start_index_input.text().strip()
            self.start_index = int(start_index_str) if start_index_str else 1
            if self.start_index < 1:
                raise ValueError("Start index must be 1 or greater.")

            end_index_str = self.end_index_input.text().strip()
            self.end_index = int(end_index_str) if end_index_str else 0
            if self.end_index != 0 and self.end_index < self.start_index:
                raise ValueError("End index must be 0 (for all) or >= start index.")
        except ValueError as e:
            msg_box = QMessageBox()
            msg_box.setStyleSheet("color: #ecf0f1; background-color: #34495e;")
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setText(f"Invalid Start/End Index: {e}")
            msg_box.setWindowTitle("Invalid Index")
            msg_box.exec_()
            return False

        return True

    def set_processing_state(self, processing):
        self.is_processing = processing
        self.extract_button.setEnabled(not processing)
        self.cancel_button.setEnabled(processing)

        # Disable or enable input fields accordingly
        inputs = [
            self.url_input,
            self.transcript_file_input,
            self.summary_output_dir_input,
            self.api_key_input,
            self.language_input,
            self.start_index_input,
            self.end_index_input,
            self.chunk_size_slider
        ]
        # Also disable checkboxes
        for style_cb in self.style_checkboxes.values():
            style_cb.setEnabled(not processing)

        for input_field in inputs:
            if isinstance(input_field, (QLineEdit, QTextEdit)):
                input_field.setReadOnly(processing)
            else:
                input_field.setEnabled(not processing)

    def select_gemini_model(self):
        """Optional model selector; you can remove or adapt this as needed."""
        msg_box = QMessageBox()
        msg_box.setStyleSheet("color: #ecf0f1; background-color: #34495e;")
        msg_box.setWindowTitle("Select Gemini Model")
        msg_box.setText("Choose a Gemini model for refinement:")

        # Build a minimal model selection UI in a message box
        # If you have a more advanced UI for model selection, skip this
        # or create a new QDialog for better user experience.

        # (Omitting a polished combo in the interest of clarity)
        # Use a textual approach or build a small layout

        # For brevity, we assume you always return the default
        # Or prompt user in a real combo selection. Placeholder:
        return self.selected_model_name

    def get_selected_styles(self):
        """
        Gather all (style_name, prompt_text) for checkboxes that are checked.
        """
        selected = []
        for style_name, cb in self.style_checkboxes.items():
            if cb.isChecked():
                selected.append((style_name, self.prompts[style_name]))
        return selected

    def start_extraction_and_refinement(self):
        if not self.validate_inputs():
            return

        selected_model = self.select_gemini_model()
        if not selected_model:
            return  # If user somehow cancels model selection
        self.selected_model_name = selected_model

        self.set_processing_state(True)
        self.progress_bar.setValue(0)
        self.status_display.clear()

        # Determine transcript output path
        transcript_input_path = self.transcript_file_input.text().strip()
        summary_output_dir = self.summary_output_dir_input.text().strip()

        if transcript_input_path:
            transcript_output = transcript_input_path
        else:
            transcript_output = os.path.join(summary_output_dir, "transcript.txt")
            self.status_display.append(
                f"<font color='#bdc3c7'>Transcript file not specified, using default: {transcript_output}</font>"
            )

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
        self.progress_bar.setValue(0)
        self.status_display.append("<font color='#2ecc71'>Transcript extraction complete! Starting Gemini processing...</font>")

        output_language = self.language_input.text()
        current_chunk_size = self.chunk_size_slider.value()

        # Collect multiple prompts from checkboxes
        selected_prompts = self.get_selected_styles()  # list of (style_name, prompt_text)

        self.gemini_thread = GeminiProcessingThread(
            transcript_file,
            self.summary_output_dir_input.text(),
            self.api_key_input.text(),
            self.selected_model_name,
            output_language,
            chunk_size=current_chunk_size,
            selected_prompts=selected_prompts  # CHANGED
        )

        self.gemini_thread.progress_update.connect(self.update_gemini_progress)
        self.gemini_thread.status_update.connect(self.update_status)
        self.gemini_thread.processing_complete.connect(self.handle_success)
        self.gemini_thread.error_occurred.connect(self.handle_error)

        self.gemini_thread.start()

    def update_gemini_progress(self, progress_percent):
        self.progress_bar.setValue(progress_percent)

    def update_status(self, message):
        if "extraction" in message.lower():
            color = "#3498db"
        elif "processing" in message.lower():
            color = "#2ecc71"
        else:
            color = "#2ecc71"
        self.status_display.append(f"<font color='{color}'>{message}</font>")

    def handle_success(self, output_path):
        self.set_processing_state(False)
        msg_box = QMessageBox()
        msg_box.setStyleSheet("color: #ecf0f1; background-color: #34495e;")
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setText(f"Processing complete!\nOutput files saved in folder:\n{output_path}")
        msg_box.setWindowTitle("Success")
        msg_box.exec_()
        self.progress_bar.setValue(100)

    def handle_error(self, error):
        self.set_processing_state(False)
        msg_box = QMessageBox()
        msg_box.setStyleSheet("color: #ecf0f1; background-color: #34495e;")
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

    def select_summary_output_directory(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ShowDirsOnly
        dir_path = QFileDialog.getExistingDirectory(
            self, "Select Gemini Output Folder", "", options=options)
        if dir_path:
            self.summary_output_dir_input.setText(dir_path)

    def select_output_file(self, title, field):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(
            self, title, "", "Text Files (*.txt);;All Files (*)", options=options)
        if file_path:
            if not file_path.endswith(".txt"):
                file_path += ".txt"
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
        self.end_index = end_index
        self._is_running = True

    def run(self):
        try:
            url = self.playlist_url
            playlist_name = "Unknown Playlist/Video"
            all_video_urls = []
            original_total_videos = 0

            if "playlist?list=" in url:
                try:
                    playlist = Playlist(url)
                    try:
                        all_video_urls = list(playlist.video_urls)
                        original_total_videos = len(all_video_urls)
                        playlist_name = playlist.title
                        self.status_update.emit(f"Found playlist: {playlist_name} with {original_total_videos} videos.")
                    except KeyError as ke:
                        error_msg = (f"Extraction error (Accessing Playlist Details): {str(ke)}. "
                                     "YouTube structure likely changed. Update pytube or check issues.")
                        self.error_occurred.emit(error_msg)
                        return
                    except Exception as access_e:
                        error_msg = f"Extraction error (Accessing Playlist Properties): {str(access_e)}. URL: {url}"
                        self.error_occurred.emit(error_msg)
                        return
                except KeyError as ke:
                    error_msg = (f"Extraction error (Initializing Playlist): {str(ke)}. "
                                 "YouTube structure likely changed. Update pytube or check issues.")
                    self.error_occurred.emit(error_msg)
                    return
                except Exception as init_e:
                    error_msg = f"Extraction error (Initializing Playlist Object): {str(init_e)}. URL: {url}"
                    self.error_occurred.emit(error_msg)
                    return

            elif "watch?v=" in url:
                all_video_urls = [url]
                original_total_videos = 1
                try:
                    yt = YouTube(url)
                    playlist_name = yt.title
                    self.status_update.emit(f"Processing single video: {playlist_name}")
                except Exception as single_title_e:
                    self.status_update.emit(f"Processing single video (Could not get title: {str(single_title_e)}). URL: {url}")
                    playlist_name = "Single Video"
            else:
                self.error_occurred.emit(f"Invalid URL format: {url}")
                return

            if not all_video_urls:
                self.error_occurred.emit(f"Could not retrieve video URLs for {url}.")
                return

            slice_start = self.start_index - 1
            if slice_start < 0:
                slice_start = 0

            if self.end_index == 0:
                slice_end = None
            else:
                slice_end = self.end_index

            video_urls_to_process = all_video_urls[slice_start:slice_end]
            total_videos = len(video_urls_to_process)

            if total_videos == 0:
                self.status_update.emit("No videos found in the specified range.")
                with open(self.output_file, 'w', encoding='utf-8') as f:
                    f.write(f"Playlist Name: {playlist_name}\n")
                    f.write(f"(No videos processed for range {self.start_index} to {self.end_index if self.end_index != 0 else 'End'})\n")
                self.extraction_complete.emit(self.output_file)
                return

            self.status_update.emit(f"Processing {total_videos} videos (range {self.start_index} to {self.end_index if self.end_index != 0 else 'End'} of {original_total_videos}).")

            with open(self.output_file, 'w', encoding='utf-8') as f:
                f.write(f"Playlist Name: {playlist_name}\n")
                f.write(f"Processing Range: {self.start_index} to {self.end_index if self.end_index != 0 else 'End'}\n\n")

                for index, video_url in enumerate(video_urls_to_process, 1):
                    if not self._is_running:
                        return
                    original_index = slice_start + index
                    try:
                        video_title = f"Video_{original_index}"
                        try:
                            yt = YouTube(video_url)
                            video_title = yt.title
                        except Exception as title_e:
                            self.status_update.emit(
                                f"Warning: Could not get title for video {original_index} ({video_url}): {str(title_e)}"
                            )

                        video_id = video_url.split("?v=")[1].split("&")[0]
                        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
                        transcript = ' '.join([t['text'] for t in transcript_list])

                        f.write(f"Video Title: {video_title}\n")
                        f.write(f"Video URL: {video_url}\n")
                        f.write(transcript + '\n\n')

                        progress_percent = int((index / total_videos) * 100)
                        self.progress_update.emit(progress_percent)
                        self.status_update.emit(
                            f"Extracted transcript for video {index}/{total_videos} "
                            f"(Original Index: {original_index}) - Title: {video_title[:30]}..."
                        )
                    except Exception as video_error:
                        self.status_update.emit(
                            f"Error processing video {index}/{total_videos} "
                            f"(Original Index: {original_index}, URL: {video_url}): {str(video_error)}"
                        )

            self.extraction_complete.emit(self.output_file)
        except Exception as e:
            if not isinstance(e, KeyError):
                self.error_occurred.emit(f"General extraction error: {str(e)}")

    def stop(self):
        self._is_running = False


class GeminiProcessingThread(QThread):
    progress_update = pyqtSignal(int)
    status_update = pyqtSignal(str)
    processing_complete = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    chunk_size = MainWindow.DEFAULT_CHUNK_SIZE

    # CHANGED: Accept a list of selected_prompts instead of a single prompt
    def __init__(self, input_file, output_dir, api_key, selected_model_name, output_language, chunk_size, selected_prompts):
        super().__init__()
        self.input_file = input_file
        self.output_dir = output_dir
        self.api_key = api_key
        self.chunk_size = chunk_size
        self.selected_model_name = selected_model_name
        self.output_language = output_language
        self.selected_prompts = selected_prompts  # list of (style_name, prompt_text)
        self._is_running = True
        logging.basicConfig(filename='gemini_processing.log',
                            level=logging.ERROR,
                            format='%(asctime)s - %(levelname)s - %(message)s')

    def run(self):
        try:
            genai.configure(api_key=self.api_key)
            video_data_chunks = self.split_videos_by_title(self.input_file)
            total_videos = len(video_data_chunks)

            if total_videos == 0:
                self.status_update.emit("No video data found in the transcript file to process.")
                self.processing_complete.emit(self.output_dir)
                return

            for video_index, video_data in enumerate(video_data_chunks):
                if not self._is_running:
                    return

                lines = video_data.strip().split('\n', 2)
                video_title = "Unknown Video"
                video_url = "Unknown URL"
                video_transcript = ""

                if len(lines) >= 1 and lines[0].startswith("Video Title:"):
                    video_title = lines[0].replace("Video Title:", "").strip()
                if len(lines) >= 2 and lines[1].startswith("Video URL:"):
                    video_url = lines[1].replace("Video URL:", "").strip()
                if len(lines) >= 3:
                    video_transcript = lines[2].strip()

                if not video_transcript:
                    self.status_update.emit(
                        f"Skipping Video {video_index + 1}/{total_videos} (Title: {video_title[:30]}...) - No transcript found."
                    )
                    continue

                sanitized_title = sanitize_filename(video_title)
                self.status_update.emit(f"\nProcessing Video {video_index + 1}/{total_videos}: {video_title[:50]}...")
                word_count = len(video_transcript.split())
                self.status_update.emit(f"Word Count: {word_count} words")
                self.status_update.emit(f"Chunk Size: {self.chunk_size} words")

                # Split transcript into sub-chunks
                video_transcript_chunks = self.split_text_into_chunks(video_transcript, self.chunk_size)

                # CHANGED: For each style, generate an output file named Title [STYLE].md
                for (style_name, style_prompt) in self.selected_prompts:
                    full_video_response = ""
                    previous_response = ""

                    # Generate response for each chunk
                    for chunk_index, chunk in enumerate(video_transcript_chunks):
                        if not self._is_running:
                            return

                        formatted_prompt = style_prompt.replace("[Language]", self.output_language)
                        context_prompt = ""
                        # If you want chunk-to-chunk continuity, you can incorporate `previous_response` into context_prompt.

                        full_prompt = f"{context_prompt}{formatted_prompt}\n\n{chunk}"

                        model = genai.GenerativeModel(self.selected_model_name)
                        self.status_update.emit(
                            f"Generating style '{style_name}' for Video {video_index + 1}, Chunk {chunk_index + 1}/{len(video_transcript_chunks)}..."
                        )
                        response = model.generate_content(full_prompt)

                        full_video_response += response.text + "\n\n"
                        previous_response = response.text

                        self.status_update.emit(f"Chunk {chunk_index + 1}/{len(video_transcript_chunks)} processed for style '{style_name}'.")

                    # Write out the final file for this style
                    final_output_path = os.path.join(
                        self.output_dir,
                        f"{sanitized_title} [{style_name}].md"  # CHANGED: append style in brackets
                    )
                    try:
                        with open(final_output_path, "w", encoding="utf-8") as final_output_file:
                            # Add Title as H1 and URL at the top
                            final_output_file.write(f"# {video_title}\n\n")
                            final_output_file.write(f"**Original Video URL:** {video_url}\n\n")
                            final_output_file.write(full_video_response.strip())
                        self.status_update.emit(f"Saved '{style_name}' output for video {video_index + 1} to {final_output_path}")
                    except IOError as e:
                        self.status_update.emit(f"Error writing file {final_output_path}: {e}")
                        self.error_occurred.emit(f"Error writing file {final_output_path}: {e}")
                        # Continue to next style, or break, as you see fit
                        continue

                progress_percent = int(((video_index + 1) / total_videos) * 100) if total_videos > 0 else 100
                self.progress_update.emit(progress_percent)

            self.status_update.emit(f"All Gemini responses saved to individual files in {self.output_dir}.")
            self.processing_complete.emit(self.output_dir)
            self.progress_update.emit(100)

        except Exception as e:
            error_message = f"Gemini processing error: {str(e)}"
            self.error_occurred.emit(error_message)
            logging.exception("Gemini processing error")

    def split_text_into_chunks(self, text, chunk_size, min_chunk_size=500):
        words = text.split()
        chunks = [" ".join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]
        if len(chunks) > 1 and len(chunks[-1].split()) < min_chunk_size:
            chunks[-2] += " " + chunks[-1]
            chunks.pop()
        return chunks

    def split_videos_by_title(self, file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()
            video_chunks = re.split(r'(?=Video Title:)', content)
            if video_chunks and video_chunks[0].startswith("Playlist Name"):
                video_chunks = video_chunks[1:]
            video_chunks = [chunk.strip() for chunk in video_chunks if chunk.strip()]
            return video_chunks
        except FileNotFoundError:
            self.error_occurred.emit(f"Transcript file not found: {file_path}")
            return []
        except Exception as e:
            self.error_occurred.emit(f"Error reading or splitting transcript file {file_path}: {e}")
            return []

    def stop(self):
        self._is_running = False


def sanitize_filename(filename):
    """Removes or replaces characters invalid in Windows/Linux/Mac filenames."""
    sanitized = re.sub(r'[<>:"/\\|?*]', '', filename)
    sanitized = sanitized.replace('&', 'and')
    sanitized = sanitized.strip()
    sanitized = re.sub(r'\s+', '_', sanitized)
    max_len = 200
    if len(sanitized) > max_len:
        cut_point = sanitized[:max_len].rfind('_')
        if cut_point != -1:
            sanitized = sanitized[:cut_point]
        else:
            sanitized = sanitized[:max_len]

    if not sanitized:
        return "untitled_video"
    return sanitized


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec_())
