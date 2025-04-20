"""
YouTube Playlist to Formatted Text (WatchYTPL4Me)

This application extracts transcripts from YouTube playlists or individual videos
and processes them using the Google Gemini API to create well-formatted, readable
markdown documents.

Main features:
- Extract transcripts from YouTube playlists or single videos
- Process text with multiple refinement styles (Balanced, Summary, Educational, etc.)
- Configure chunk size for optimal API processing
- Customize output language
- Select specific video ranges from playlists
- Save outputs to customizable locations

The application uses a multi-threaded approach to maintain UI responsiveness:
1. TranscriptExtractionThread: Extracts video transcripts from YouTube
2. GeminiProcessingThread: Processes transcripts with the Gemini API

Requirements:
- PyQt5 for the user interface
- pytubefix for accessing YouTube data
- youtube_transcript_api for extracting transcripts
- google.generativeai for text processing
"""

import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QProgressBar, QTextEdit, QFileDialog, QMessageBox,
                             QSlider, QGroupBox, QCheckBox, QGridLayout) 
from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QFont, QColor
from datetime import datetime
from pytubefix import Playlist, YouTube
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import google.generativeai as genai
import re
import logging
import os
from dotenv import load_dotenv
from builtins import KeyError
from ytvideo2txt import get_transcript_with_ai_stt
from prompts import text_refinement_prompts
load_dotenv(".env")


class MainWindow(QMainWindow):
    """
    Main application window for the YouTube Playlist to Text converter.
    
    This class provides the user interface for the application, allowing users to:
    - Input a YouTube playlist or video URL
    - Specify language and processing preferences
    - Select refinement styles for text processing 
    - Configure output settings
    - View progress and status updates during processing
    
    The application extracts video transcripts from YouTube and processes them
    using the Gemini API to create formatted and refined output documents.
    """
    
    DEFAULT_CHUNK_SIZE = 70000  # Define default chunk size as a class variable

    def __init__(self):
        super().__init__()
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.prompts = text_refinement_prompts
        self.extraction_thread = None
        self.gemini_thread = None
        self.is_processing = False

        self.available_models = ["gemini-2.5-flash-preview-04-17", "gemini-2.5-pro-preview-03-25"]
        self.selected_model_name = "gemini-2.5-flash-preview-04-17"

        # Set the class variable default chunk size using the constant
        GeminiProcessingThread.chunk_size = self.DEFAULT_CHUNK_SIZE

        self.initUI()

    @pyqtSlot(int)
    def update_chunk_size_label(self, value):
        """
        Updates the displayed chunk size value when the slider is moved.
        
        Args:
            value (int): The new chunk size value from the slider
        """
        self.chunk_size_value_label.setText(str(value))

    def initUI(self):
        """
        Initializes the user interface of the application.
        
        Creates and configures all UI components including:
        - Input fields for URL, language, and API settings
        - Refinement style selection checkboxes
        - Chunk size slider for controlling text processing
        - File input/output selection fields
        - Progress display and status windows
        - Control buttons for starting/canceling operations
        
        Also applies style settings and layouts to create a modern UI appearance.
        """
        self.setWindowTitle("WatchYTPL4Me: Transform YouTube Playlist into Professional-Quality Documents")
        self.setMinimumSize(900, 850)
        self.apply_modern_style()
        self.showFullScreen()

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Title Section
        title_label = QLabel("WatchYTPL4Me: From YouTube Playlist to Formatted Docs")
        title_label.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            color: white;
            padding: 10px;
            border-radius: 8px;
            background: #e74c3c;
        """)
        main_layout.addWidget(title_label)

        # Input Container
        input_container = QWidget()
        input_container.setStyleSheet("background-color: #f5f5f5; border-radius: 10px; padding: 15px;")
        input_layout = QVBoxLayout(input_container)
        input_layout.setSpacing(8)

        # Playlist URL Input
        url_layout = QVBoxLayout()
        url_layout.setContentsMargins(0, 0, 0, 0)
        url_layout.setSpacing(0)
        url_label = QLabel("YouTube URL (Playlist or Video):")
        url_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        url_label.setStyleSheet("color: #333333;")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter YouTube playlist or video URL (e.g., https://www.youtube.com/playlist?list=... or https://www.youtube.com/watch?v=...)")
        self.url_input.setFont(QFont("Segoe UI", 9))
        self.url_input.setStyleSheet(self.get_input_style())
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        input_layout.addLayout(url_layout)

        # Language and Index Inputs in one row
        lang_and_index_layout = QHBoxLayout()
        lang_and_index_layout.setSpacing(0)

        # Language Input (left side)
        language_layout = QVBoxLayout()
        language_layout.setContentsMargins(0, 0, 0, 0)
        language_layout.setSpacing(0)
        language_label = QLabel("Output Language:")
        language_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        language_label.setStyleSheet("color: #333333;")
        self.language_input = QLineEdit()
        self.language_input.setPlaceholderText("e.g., English, Spanish, French")
        self.language_input.setFont(QFont("Segoe UI", 9))
        self.language_input.setStyleSheet(self.get_input_style())
        self.language_input.setText(os.environ.get("LANGUAGE", "English"))
        language_layout.addWidget(language_label)
        language_layout.addWidget(self.language_input)
        lang_and_index_layout.addLayout(language_layout)

        # Start/End Video Index Input (right side)
        index_container = QVBoxLayout()
        index_container.setSpacing(0)
        
        # Index Label
        index_label = QLabel("Video Range:")
        index_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        index_label.setStyleSheet("color: #333333; margin-bottom: -5px; padding: 0px;")
        index_container.addWidget(index_label)
        
        # Index inputs in one row
        index_layout = QHBoxLayout()
        index_layout.setSpacing(0)

        # Start Index
        start_layout = QHBoxLayout()
        start_layout.setSpacing(0)
        start_label = QLabel("Start:")
        start_label.setStyleSheet("color: #333333;")
        self.start_index_input = QLineEdit()
        self.start_index_input.setPlaceholderText("1")
        self.start_index_input.setText("1")
        self.start_index_input.setFont(QFont("Segoe UI", 9))
        self.start_index_input.setStyleSheet(self.get_input_style())
        self.start_index_input.setFixedWidth(60)
        start_layout.addWidget(start_label)
        start_layout.addWidget(self.start_index_input)
        
        # End Index
        end_layout = QHBoxLayout()
        end_layout.setSpacing(0)
        end_label = QLabel("End (0 for all):")
        end_label.setStyleSheet("color: #333333;")
        self.end_index_input = QLineEdit()
        self.end_index_input.setPlaceholderText("0")
        self.end_index_input.setText("0")
        self.end_index_input.setFont(QFont("Segoe UI", 9))
        self.end_index_input.setStyleSheet(self.get_input_style())
        self.end_index_input.setFixedWidth(60)
        end_layout.addWidget(end_label)
        end_layout.addWidget(self.end_index_input)
        
        index_layout.addLayout(start_layout)
        index_layout.addLayout(end_layout)
        index_layout.addStretch(1)
        
        index_container.addLayout(index_layout)
        lang_and_index_layout.addLayout(index_container)
        input_layout.addLayout(lang_and_index_layout)

        # --- Refinement Styles in horizontal layout ---
        style_groupbox = QGroupBox("Refinement Styles (Select one or more)")
        style_groupbox.setStyleSheet("QGroupBox { color: #333333; font-weight: bold; margin-top: 7px; }")
        style_layout = QGridLayout()
        style_layout.setSpacing(0)

        # Store checkboxes in a dict for easy reference
        self.style_checkboxes = {}
        style_keys = list(self.prompts.keys())
        
        # Arrange checkboxes in a grid layout - 3 columns
        row, col = 0, 0
        columns = 3
        for style_name in style_keys:
            cb = QCheckBox(style_name)
            cb.setStyleSheet("color: #333333; font-size: 10pt;")
            style_layout.addWidget(cb, row, col)
            self.style_checkboxes[style_name] = cb
            col += 1
            if col >= columns:
                col = 0
                row += 1

        style_groupbox.setLayout(style_layout)
        input_layout.addWidget(style_groupbox)

        # Chunk Size with label on the same line as slider
        chunk_size_container = QWidget()
        chunk_size_container.setStyleSheet("background-color: #eaeaea; border-radius: 5px; padding: 8px;")
        chunk_size_layout = QVBoxLayout(chunk_size_container)
        chunk_size_layout.setContentsMargins(5, 5, 5, 5)
        chunk_size_layout.setSpacing(0)

        # Header with value
        chunk_header_layout = QHBoxLayout()
        chunk_size_label = QLabel("Chunk Size:")
        chunk_size_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        chunk_size_label.setStyleSheet("color: #333333;")
        
        self.chunk_size_value_label = QLabel(str(self.DEFAULT_CHUNK_SIZE))
        self.chunk_size_value_label.setFont(QFont("Segoe UI", 10))
        self.chunk_size_value_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
        
        chunk_header_layout.addWidget(chunk_size_label)
        chunk_header_layout.addWidget(self.chunk_size_value_label)
        chunk_header_layout.addStretch(1)
        chunk_size_layout.addLayout(chunk_header_layout)

        # Slider
        self.chunk_size_slider = QSlider(Qt.Horizontal)
        self.chunk_size_slider.setMinimum(5000)
        self.chunk_size_slider.setMaximum(500000)
        self.chunk_size_slider.setValue(self.DEFAULT_CHUNK_SIZE)
        self.chunk_size_slider.valueChanged.connect(self.update_chunk_size_label)
        self.chunk_size_slider.setStyleSheet("""
            QSlider {
                padding: 2px 0;
            }
            QSlider::groove:horizontal {
                border: 1px solid #999999;
                height: 8px;
                background: #cccccc;
                margin: 20px 0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #e74c3c;
                border: 1px solid #5c5c5c;
                width: 18px;
                height: 18px;
                margin: -6px 0;
                border-radius: 9px;
            }
            QSlider::handle:horizontal:hover {
                background: #c0392b;
            }
        """)
        chunk_size_layout.addWidget(self.chunk_size_slider)

        # Description
        chunk_size_description = QLabel(
            f"(Maximum words per Gemini API call. Default: {self.DEFAULT_CHUNK_SIZE}, approx. 1/10 of 1M tokens context window)"
        )
        chunk_size_description.setFont(QFont("Segoe UI", 8))
        chunk_size_description.setStyleSheet("color: #666666;")
        chunk_size_description.setWordWrap(True)
        chunk_size_layout.addWidget(chunk_size_description)

        input_layout.addWidget(chunk_size_container)

        # File Inputs
        self.create_file_input(input_layout,
                               "Transcript Output File (Optional):",
                               "Choose File",
                               "transcript_file_input",
                               self.select_transcript_output_file)

        self.create_directory_input(input_layout,
                                    "Summary Output Folder:",
                                    "Choose Folder",
                                    "summary_output_dir_input",
                                    self.select_summary_output_directory)

        # API Key Input
        api_key_layout = QVBoxLayout()
        api_key_layout.setContentsMargins(0, 0, 0, 0)
        api_key_layout.setSpacing(0)
        api_key_label = QLabel("Gemini API Key:")
        api_key_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        api_key_label.setStyleSheet("color: #333333;")
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Enter your Gemini API key")
        self.api_key_input.setFont(QFont("Segoe UI", 9))
        self.api_key_input.setStyleSheet(self.get_input_style())
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setText(os.environ.get("GEMINI_API_KEY", ""))
        api_key_layout.addWidget(api_key_label)
        api_key_layout.addWidget(self.api_key_input)
        input_layout.addLayout(api_key_layout)

        main_layout.addWidget(input_container)

        # Progress Section
        progress_container = QWidget()
        progress_container.setStyleSheet("background-color: #f5f5f5; border-radius: 10px; padding: 10px;")
        progress_layout = QVBoxLayout(progress_container)
        progress_layout.setSpacing(10)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background: #eeeeee;
                border: 1px solid #cccccc;
                border-radius: 5px;
                text-align: center;
                color: #333333;
                font-size: 12px;
                height: 24px;
            }
            QProgressBar::chunk {
                background: #27ae60;
                border-radius: 5px;
            }
        """)
        progress_layout.addWidget(self.progress_bar)

        # Status Display
        self.status_display = QTextEdit()
        self.status_display.setReadOnly(True)
        self.status_display.setStyleSheet("""
            background-color: white;
            border: 1px solid #cccccc;
            border-radius: 5px;
            color: #333333;
            font-size: 12px;
            padding: 8px;
        """)
        progress_layout.addWidget(self.status_display)
        main_layout.addWidget(progress_container)

        # Control Buttons
        control_layout = QHBoxLayout()
        control_layout.setSpacing(20)

        self.extract_button = QPushButton("Start Processing")
        self.extract_button.setStyleSheet(self.get_button_style("#e74c3c", "#c0392b"))
        self.extract_button.clicked.connect(self.start_extraction_and_refinement)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setStyleSheet(self.get_button_style("#7f8c8d", "#34495e"))
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
        """
        Creates a file input component with label, text field, and button.
        
        Args:
            parent_layout: The layout to add this component to
            label_text (str): The label text to display above the input field
            button_text (str): The text to display on the select button
            field_name (str): The object name for the input field (for referencing later)
            handler: The function to call when the select button is clicked
            
        This creates a standardized file input UI component consisting of a label,
        a read-only text field to show the selected file path, and a button to open
        a file selection dialog.
        """
        layout = QVBoxLayout()
        layout.setSpacing(0)
        
        font = QFont("Segoe UI", 10, QFont.Bold)
        label = QLabel(label_text)
        label.setFont(font)
        label.setStyleSheet("color: #333333;")
        layout.addWidget(label)
        
        input_row = QHBoxLayout()
        input_row.setSpacing(10)
        
        input_field = QLineEdit()
        input_field.setObjectName(field_name)
        input_field.setReadOnly(True)
        input_field.setPlaceholderText("Optional: Select file or leave blank for default")
        input_field.setStyleSheet(self.get_input_style())

        button = QPushButton(button_text)
        button.setStyleSheet(self.get_button_style("#3498db", "#2980b9"))
        button.clicked.connect(handler)
        button.setFixedWidth(120)

        input_row.addWidget(input_field)
        input_row.addWidget(button)
        layout.addLayout(input_row)

        parent_layout.addLayout(layout)
        setattr(self, field_name, input_field)

    def create_directory_input(self, parent_layout, label_text, button_text, field_name, handler):
        """
        Creates a directory input component with label, text field, and button.
        
        Args:
            parent_layout: The layout to add this component to
            label_text (str): The label text to display above the input field
            button_text (str): The text to display on the select button
            field_name (str): The object name for the input field (for referencing later)
            handler: The function to call when the select button is clicked
            
        Similar to create_file_input, but specifically for selecting directories
        rather than files.
        """
        layout = QVBoxLayout()
        layout.setSpacing(0)
        
        font = QFont("Segoe UI", 10, QFont.Bold)
        label = QLabel(label_text)
        label.setFont(font)
        label.setStyleSheet("color: #333333;")
        layout.addWidget(label)
        
        input_row = QHBoxLayout()
        input_row.setSpacing(10)

        input_field = QLineEdit()
        input_field.setObjectName(field_name)
        input_field.setReadOnly(True)
        input_field.setPlaceholderText(f"Select {label_text.split(':')[0].strip()} folder")
        input_field.setStyleSheet(self.get_input_style())

        button = QPushButton(button_text)
        button.setStyleSheet(self.get_button_style("#3498db", "#2980b9"))
        button.clicked.connect(handler)
        button.setFixedWidth(140)

        input_row.addWidget(input_field)
        input_row.addWidget(button)
        layout.addLayout(input_row)

        parent_layout.addLayout(layout)
        setattr(self, field_name, input_field)

    def get_input_style(self):
        """
        Returns the CSS styling for input fields.
        
        Returns:
            str: CSS stylesheet string for styling input elements uniformly
            
        This provides consistent styling for all input fields across the application,
        including focus and disabled states.
        """
        return """
            QLineEdit {
                background: white;
                margin-left: 20px;
                border: 1px solid #cccccc;
                border-radius: 4px;
                color: #333333;
                padding: 6px;
            }
            QLineEdit:focus {
                border: 1px solid #e74c3c;
            }
            QLineEdit:disabled {
                background: #eeeeee;
                border-color: #cccccc;
                color: #777777;
            }
        """

    def get_button_style(self, color1, color2):
        """
        Returns the CSS styling for buttons with the specified colors.
        
        Args:
            color1 (str): The base button color (hex code)
            color2 (str): The hover/pressed button color (hex code)
            
        Returns:
            str: CSS stylesheet string for styling buttons
            
        This allows for consistent button styling while letting different 
        buttons have different color schemes.
        """
        return f"""
            QPushButton {{
                background: {color1};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {color2};
            }}
            QPushButton:pressed {{
                background: {color2};
                padding-top: 11px;
                padding-bottom: 9px;
            }}
            QPushButton:disabled {{
                background: #cccccc;
                color: #888888;
            }}
        """

    def apply_modern_style(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #e6e6e6;
            }
            QLabel {
                color: #333333;
            }
            QGroupBox {
                border: 1px solid #cccccc;
                border-radius: 5px;
                margin-top: 12px;
                padding: 10px;
                background: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                background: white;
            }
            QMessageBox {
                background-color: white;
                color: #333333;
            }
        """)

    def center(self):
        frame = self.frameGeometry()
        center_point = QApplication.primaryScreen().availableGeometry().center()
        frame.moveCenter(center_point)
        self.move(frame.topLeft())

    def validate_inputs(self):
        """
        Validates all user inputs before starting the processing.
        
        Returns:
            bool: True if all inputs are valid, False otherwise
            
        Performs validation checks on:
        - URL format (must be a valid YouTube playlist or video URL)
        - Selected refinement styles (at least one must be selected)
        - Output directory (must be a valid directory)
        - API key (must be provided)
        - Language (must be specified)
        - Start/end indices (must be valid numbers with start <= end)
        
        Shows appropriate error messages to the user when validation fails.
        """
        url_text = self.url_input.text()

        if not (url_text.startswith("https://www.youtube.com/playlist") or
                url_text.startswith("https://www.youtube.com/watch?v=")):
            msg_box = QMessageBox()
            msg_box.setStyleSheet("color: #333333; background-color: white;")
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setText("Please enter a valid YouTube playlist URL or single video URL.")
            msg_box.setWindowTitle("Invalid URL")
            msg_box.exec_()
            return False

        # Validate Transcript file only if provided
        transcript_file_path = self.transcript_file_input.text().strip()
        if transcript_file_path and not transcript_file_path.endswith(".txt"):
            msg_box = QMessageBox()
            msg_box.setStyleSheet("color: #333333; background-color: white;")
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setText("If specified, Transcript output file must be a .txt file")
            msg_box.setWindowTitle("Invalid File")
            msg_box.exec_()
            return False

        # Validate Summary output directory
        summary_dir = self.summary_output_dir_input.text().strip()
        if not summary_dir:
            msg_box = QMessageBox()
            msg_box.setStyleSheet("color: #333333; background-color: white;")
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setText("Please select a Summary Output Folder.")
            msg_box.setWindowTitle("Output Folder Required")
            msg_box.exec_()
            return False
        if not os.path.isdir(summary_dir):
            msg_box = QMessageBox()
            msg_box.setStyleSheet("color: #333333; background-color: white;")
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setText("The selected Summary Output path is not a valid folder.")
            msg_box.setWindowTitle("Invalid Folder")
            msg_box.exec_()
            return False

        if not self.api_key_input.text().strip():
            msg_box = QMessageBox()
            msg_box.setStyleSheet("color: #333333; background-color: white;")
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setText("Please enter your Gemini API key")
            msg_box.setWindowTitle("API Key Required")
            msg_box.exec_()
            return False

        if not self.language_input.text().strip():
            msg_box = QMessageBox()
            msg_box.setStyleSheet("color: #333333; background-color: white;")
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setText("Please specify the output language")
            msg_box.setWindowTitle("Language Required")
            msg_box.exec_()
            return False

        # Validate that at least one style checkbox is checked
        if not any(cb.isChecked() for cb in self.style_checkboxes.values()):
            msg_box = QMessageBox()
            msg_box.setStyleSheet("color: #333333; background-color: white;")
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
            msg_box.setStyleSheet("color: #333333; background-color: white;")
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setText(f"Invalid Start/End Index: {e}")
            msg_box.setWindowTitle("Invalid Index")
            msg_box.exec_()
            return False

        return True

    def set_processing_state(self, processing):
        """
        Updates the UI state based on whether processing is active.
        
        Args:
            processing (bool): True if processing is active, False otherwise
            
        When processing is active:
        - Input fields and controls are disabled
        - Cancel button is enabled
        - Extract button is disabled
        
        When processing is inactive:
        - Input fields and controls are enabled
        - Cancel button is disabled
        - Extract button is enabled
        
        This ensures the user cannot modify inputs during processing.
        """
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
        msg_box.setStyleSheet("color: #333333; background-color: white;")
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
        Retrieves all selected refinement styles and their prompt templates.
        
        Returns:
            list: A list of tuples (style_name, prompt_text) for each selected style
            
        This method collects all style checkboxes that the user has checked and
        returns their names and associated prompt templates for use in text processing.
        """
        selected = []
        for style_name, cb in self.style_checkboxes.items():
            if cb.isChecked():
                selected.append((style_name, self.prompts[style_name]))
        return selected

    def start_extraction_and_refinement(self):
        """
        Starts the main processing workflow for transcript extraction and refinement.
        
        This method:
        1. Validates all user inputs
        2. Sets up the processing environment
        3. Creates output directories/files if needed
        4. Starts the transcript extraction thread
        5. Updates the UI to reflect processing state
        
        The processing is done in separate threads to keep the UI responsive.
        First, transcripts are extracted from YouTube, then the Gemini API is used
        to process and refine the text according to the selected styles.
        """
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
        """
        Starts the Gemini API processing thread after transcript extraction.
        
        Args:
            transcript_file (str): Path to the extracted transcript file
            
        This method:
        1. Resets the progress indicator
        2. Gets the selected language and chunk size settings
        3. Collects all selected refinement style prompts
        4. Creates and starts the GeminiProcessingThread
        
        This is typically called automatically when transcript extraction completes.
        """
        self.progress_bar.setValue(0)
        self.status_display.append("<font color='#27ae60'>Transcript extraction complete! Starting Gemini processing...</font>")

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
        if "extracted transcript" in message.lower() or r"Saved '" in message.lower():
            color = "#27ae60"  # Green
        elif "error processing" in message.lower():
            color = "#e74c3c"  # Red
        elif "processing video" in message.lower():
            color = "#2980b9"  # Blue
        else:
            color = "#333333"  # Dark gray
        self.status_display.append(f"<font color='{color}'>{message}</font>")

    def handle_success(self, output_path):
        self.set_processing_state(False)
        msg_box = QMessageBox()
        msg_box.setStyleSheet("color: #333333; background-color: white;")
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setText(f"Processing complete!\nOutput files saved in folder:\n{output_path}")
        msg_box.setWindowTitle("Success")
        msg_box.exec_()
        self.progress_bar.setValue(100)

    def handle_error(self, error):
        self.set_processing_state(False)
        msg_box = QMessageBox()
        msg_box.setStyleSheet("color: #333333; background-color: white;")
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
    """
    Thread for extracting transcripts from YouTube videos or playlists.
    
    This class handles the extraction of transcript data from YouTube in a 
    separate thread to maintain UI responsiveness. It connects to YouTube using
    pytubefix and the YouTube Transcript API to download video transcripts.
    
    The thread signals progress updates and status messages back to the main UI
    and handles error conditions appropriately.
    
    Signals:
        progress_update: Emits the percentage of completion (0-100)
        status_update: Emits status messages as string
        extraction_complete: Emits the path to the saved transcript file when done
        error_occurred: Emits error messages as string
    """
    progress_update = pyqtSignal(int)
    status_update = pyqtSignal(str)
    extraction_complete = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, playlist_url, output_file, start_index=1, end_index=0):
        """
        Initializes the transcript extraction thread.
        
        Args:
            playlist_url (str): URL of the YouTube playlist or single video
            output_file (str): Path where transcript will be saved
            start_index (int): Starting video index (1-based) to process
            end_index (int): Ending video index to process (0 means process all)
        """
        super().__init__()
        self.playlist_url = playlist_url
        self.output_file = output_file
        self.start_index = start_index
        self.end_index = end_index
        self._is_running = True

    def run(self):
        """
        Main execution method for the thread.
        
        This method:
        1. Parses the input URL to determine if it's a playlist or single video
        2. Retrieves video information and transcripts
        3. Processes each video in the specified range
        4. Saves the combined transcripts to the output file
        5. Emits signals for progress updates and completion
        
        Handles various error conditions and edge cases that can occur with 
        YouTube API access. If extraction fails, uses AI STT fallback.
        """
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
                        return # Exit if cancelled

                    original_index = slice_start + index
                    video_title = f"Video_{original_index}"
                    transcript = None # Initialize transcript as None
                    transcript_source = "Unknown" # To track where the transcript came from

                    try:
                        # --- Get Video Title ---
                        try:
                            yt = YouTube(video_url)
                            video_title = yt.title
                        except Exception as title_e:
                            self.status_update.emit(
                                f"Warning: Could not get title for video {original_index} ({video_url}): {str(title_e)}"
                            )

                        # --- Attempt to Get Transcript via Standard API ---
                        video_id = video_url.split("?v=")[1].split("&")[0]
                        try:
                            self.status_update.emit(
                                f"Attempting standard transcript extraction for video {index}/{total_videos} "
                                f"(Original Index: {original_index}) - Title: {video_title[:50]}..."
                            )
                            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
                            transcript = ' '.join([t['text'] for t in transcript_list])
                            transcript_source = "Standard API"
                            self.status_update.emit(
                                f"Successfully extracted transcript via Standard API for video {index}/{total_videos}."
                            )

                        # --- Fallback to AI STT if Standard API Fails ---
                        except (TranscriptsDisabled, NoTranscriptFound) as e:
                            self.status_update.emit(
                                f"Standard transcript unavailable for video {index}/{total_videos} ({type(e).__name__}). "
                                f"Attempting AI STT fallback..."
                            )
                            try:
                                transcript = get_transcript_with_ai_stt(video_url, video_title, self.output_file)
                                if transcript:
                                    transcript_source = "AI STT Fallback"
                                    self.status_update.emit(
                                        f"Successfully obtained transcript via AI STT for video {index}/{total_videos}."
                                    )
                                else:
                                    self.status_update.emit(
                                        f"AI STT fallback failed or returned no transcript for video {index}/{total_videos}."
                                    )
                            except Exception as ai_e:
                                self.status_update.emit(
                                    f"Error during AI STT fallback for video {index}/{total_videos}: {str(ai_e)}"
                                )
                                transcript = None # Ensure transcript is None if AI fails

                        except Exception as api_general_error:
                             # Handle other youtube_transcript_api errors if needed, or re-raise
                             self.status_update.emit(
                                 f"Error getting transcript via Standard API for video {index}/{total_videos}: {str(api_general_error)}"
                             )
                             # Optionally, you could still try AI STT here, or just log and skip
                             transcript = None


                        # --- Write Transcript if Obtained ---
                        if transcript:
                            f.write(f"Video Title: {video_title}\n")
                            f.write(f"Video URL: {video_url}\n")
                            f.write(f"Transcript Source: {transcript_source}\n") # Indicate source
                            f.write(transcript + '\n\n')
                            self.status_update.emit(
                                f"Processed video {index}/{total_videos} "
                                f"(Original Index: {original_index}) - Source: {transcript_source}"
                            )
                        else:
                             self.status_update.emit(
                                f"Skipping video {index}/{total_videos} "
                                f"(Original Index: {original_index}) - Could not obtain transcript from any source."
                            )

                        progress_percent = int((index / total_videos) * 100)
                        self.progress_update.emit(progress_percent)
                        self.status_update.emit(
                            f"Extracted transcript for video {index}/{total_videos} "
                            f"(Original Index: {original_index}) - Title: {video_title[:100]}..."
                        )
                    except Exception as video_loop_error:
                        # Catch errors specific to processing a single video within the loop
                        self.status_update.emit(
                            f"Error processing video {index}/{total_videos} "
                            f"(Original Index: {original_index}, URL: {video_url}): {str(video_loop_error)}"
                        )
                        # Continue to the next video

            self.extraction_complete.emit(self.output_file)

        except Exception as general_error:
            # Catch errors occurring outside the video loop (e.g., playlist access)
            # Exclude KeyError if already handled, or refine based on specific expected errors
            if not isinstance(general_error, KeyError): # Avoid duplicate reporting if KeyError was handled earlier
                self.error_occurred.emit(f"General extraction error: {str(general_error)}")

    def stop(self):
        """
        Stops the thread execution cleanly.
        
        Sets the internal running flag to False, which causes the run method
        to exit gracefully at the next appropriate opportunity.
        """
        self._is_running = False


class GeminiProcessingThread(QThread):
    """
    Thread for processing transcripts with the Gemini API.
    
    This class handles the refinement and formatting of transcripts using
    Google's Gemini API. It processes transcript text in chunks to handle
    large transcripts efficiently and applies multiple refinement styles
    based on user selection.
    
    The thread signals progress updates and status messages back to the main UI
    and handles error conditions that may occur during API interaction.
    
    Signals:
        progress_update: Emits the percentage of completion (0-100)
        status_update: Emits status messages as string
        processing_complete: Emits the path to the output directory when done
        error_occurred: Emits error messages as string
    """
    progress_update = pyqtSignal(int)
    status_update = pyqtSignal(str)
    processing_complete = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    chunk_size = MainWindow.DEFAULT_CHUNK_SIZE

    def __init__(self, input_file, output_dir, api_key, selected_model_name, output_language, chunk_size, selected_prompts):
        """
        Initializes the Gemini processing thread.
        
        Args:
            input_file (str): Path to the transcript file to process
            output_dir (str): Directory where processed files will be saved
            api_key (str): Google Gemini API key
            selected_model_name (str): Name of the Gemini model to use
            output_language (str): Target language for the output
            chunk_size (int): Maximum words per API call
            selected_prompts (list): List of tuples (style_name, prompt_text) for processing
            
        The thread initializes with these parameters and sets up logging to track
        any errors that might occur during processing.
        """
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
        """
        Main execution method for the Gemini processing thread.
        
        This method:
        1. Configures the Gemini API with the provided key
        2. Splits the transcript file into individual video sections
        3. For each video:
           - Extracts the title, URL, and transcript text
           - For each selected refinement style:
              - Splits the transcript into manageable chunks
              - Processes each chunk with the Gemini API
              - Combines the responses
              - Saves the result to a markdown file
        4. Emits progress and completion signals
        
        Error handling includes logging exceptions and emitting error signals.
        """
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

                sanitized_title = self._sanitize_filename(video_title)
                self.status_update.emit(f"\nProcessing Video {video_index + 1}/{total_videos}: {video_title[:50]}...")
                word_count = len(video_transcript.split())
                self.status_update.emit(f"Word Count: {word_count} words")
                self.status_update.emit(f"Chunk Size: {self.chunk_size} words")

                # Split transcript into sub-chunks
                video_transcript_chunks = self.split_text_into_chunks(video_transcript, self.chunk_size)

                # For each style, generate an output file named Title [STYLE].md
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
                        f"{sanitized_title} [{style_name}].md"  # Append style in brackets
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
        """
        Splits a long text into smaller chunks for API processing.
        
        Args:
            text (str): The full text to split
            chunk_size (int): Maximum words per chunk
            min_chunk_size (int): Minimum words for the last chunk
            
        Returns:
            list: List of text chunks
            
        If the last chunk is smaller than min_chunk_size, it will be combined with
        the previous chunk to avoid processing very small text segments.
        """
        words = text.split()
        chunks = [" ".join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]
        if len(chunks) > 1 and len(chunks[-1].split()) < min_chunk_size:
            chunks[-2] += " " + chunks[-1]
            chunks.pop()
        return chunks

    def split_videos_by_title(self, file_path):
        """
        Parses the transcript file to extract individual video data.
        
        Args:
            file_path (str): Path to the transcript file
            
        Returns:
            list: List of text blocks, each containing data for a single video
            
        Each video block includes the video title, URL, and transcript text.
        The function handles the specific format created by the transcript extraction
        process and splits the file at each "Video Title:" marker.
        """
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
        """
        Stops the thread execution cleanly.
        
        Sets the internal running flag to False, which causes the run method
        to exit gracefully at the next appropriate opportunity.
        """
        self._is_running = False


    def _sanitize_filename(filename):
        """
        Removes or replaces characters invalid in Windows/Linux/Mac filenames.
        
        Args:
            filename (str): The original filename that may contain invalid characters
            
        Returns:
            str: A sanitized filename that is safe to use on all major operating systems
            
        This function:
        1. Removes invalid characters (<>:"/\|?*)
        2. Replaces ampersands with 'and'
        3. Replaces spaces with underscores
        4. Truncates to a reasonable maximum length (200 chars)
        5. Returns 'untitled_video' if the result is empty
        """
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
    """
    Main entry point for the application.
    
    Creates the main application instance, displays the window,
    and starts the event loop to handle user interactions.
    """
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec_())