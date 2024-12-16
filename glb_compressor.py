import os
import sys
import threading
import trimesh
import vtk

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QLabel, QFileDialog,
    QWidget, QPushButton, QSlider, QProgressBar, QTextEdit, QMenuBar, QMenu
)
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import Qt
from PIL import Image


def resource_path(relative_path):
    """
    Get the absolute path to a resource, accounting for frozen environments.
    """
    if getattr(sys, 'frozen', False):  # Check if running in a bundle
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class DragAndDropArea(QWidget):
    def __init__(self, callback, parent=None):
        super().__init__(parent)
        self.callback = callback
        self.setAcceptDrops(True)
        self.setStyleSheet("border: 2px dashed #4CAF50; background-color: #e0e0e0;")
        self.label = QLabel("Drag and Drop .glb Files Here", self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("font-size: 18px; font-weight: bold; color: #333;")
        layout = QVBoxLayout(self)
        layout.addWidget(self.label)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if file_path.endswith(".glb"):
                self.callback(file_path)
            else:
                parent = self.parentWidget()
                if parent:
                    parent.set_status_message("Invalid file type. Only .glb files are supported.")


class GLBCompressorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GLB Compressor with Drag-and-Drop")
        self.setMinimumSize(300, 130)
        self.setStyleSheet("background-color: #333333; color: #FFFFFF;")  # Dark theme
        self.setWindowIcon(QIcon(resource_path("bottomlogo.ico")))

        # Menu Bar
        self.menu_bar = QMenuBar(self)
        file_menu = QMenu("File", self)
        open_action = QAction("Open File", self)
        open_action.triggered.connect(self.open_file_dialog)
        file_menu.addAction(open_action)
        file_menu.addAction(QAction("Exit", self, triggered=self.close))
        help_menu = QMenu("Help", self)
        help_menu.addAction(QAction("About", self, triggered=self.show_about_dialog))
        self.menu_bar.addMenu(file_menu)
        self.menu_bar.addMenu(help_menu)
        self.setMenuBar(self.menu_bar)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # Drag-and-Drop Area
        self.drag_drop_area = DragAndDropArea(callback=self.load_glb_file, parent=self)
        layout.addWidget(self.drag_drop_area)

        # File Label
        self.file_label = QLabel("No file loaded.", self)
        layout.addWidget(self.file_label)

        # Log Area
        self.log_area = QTextEdit(self)
        self.log_area.setReadOnly(True)
        self.log_area.setStyleSheet("background-color: #e0e0e0; border: 1px solid #ccc; font-size: 14px; color: #333;")
        self.log_area.setMaximumHeight(80)
        layout.addWidget(self.log_area)

        # Compression Slider
        slider_layout = QHBoxLayout()
        self.slider_label = QLabel("Compression Level: 50%", self)
        slider_layout.addWidget(self.slider_label)

        self.compression_slider = QSlider(Qt.Horizontal, self)
        self.compression_slider.setRange(10, 100)
        self.compression_slider.setValue(50)
        self.compression_slider.valueChanged.connect(self.update_slider_label)
        slider_layout.addWidget(self.compression_slider)
        layout.addLayout(slider_layout)

        # Progress Bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                height: 30px;
                background-color: #444444;
                border: 1px solid #555555;
                border-radius: 5px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                width: 20px;
            }
        """)
        layout.addWidget(self.progress_bar)

        # Compress Button
        self.compress_button = QPushButton("Compress and Save GLB", self)
        self.compress_button.clicked.connect(self.compress_file)
        layout.addWidget(self.compress_button)

    def open_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open GLB File", "", "GLB Files (*.glb)")
        if file_path:
            self.load_glb_file(file_path)

    def load_glb_file(self, filepath):
        self.filepath = filepath
        self.file_label.setText(f"Loaded file: {os.path.basename(filepath)}")
        self.set_status_message(f"Loaded file: {os.path.basename(filepath)}")

    def update_slider_label(self):
        value = self.compression_slider.value()
        self.slider_label.setText(f"Compression Level: {value}%")

    def compress_file(self):
        if not self.filepath:
            self.set_status_message("No GLB file loaded to compress.")
            return

        output_file, _ = QFileDialog.getSaveFileName(self, "Save Compressed GLB File", "", "GLB Files (*.glb)")
        if output_file:
            threading.Thread(target=self.perform_compression, args=(output_file,)).start()

    def perform_compression(self, output_path):
        try:
            self.update_progress(10, "Loading GLB file...")
            scene = trimesh.load(self.filepath, force="scene")
            self.update_progress(90, "Saving compressed file...")
            scene.export(output_path)
            self.update_progress(100, "Compression complete.")
            self.set_status_message(f"Compressed file saved: {output_path}")
        except Exception as e:
            self.set_status_message(f"Compression failed: {e}")
        finally:
            self.compress_button.setEnabled(True)

    def update_progress(self, value, message):
        self.progress_bar.setValue(value)
        self.log_area.append(message)

    def set_status_message(self, message):
        self.log_area.append(message)

    def show_about_dialog(self):
        self.log_area.append(
            "GLB Compressor: Drag and drop GLB files, adjust compression, and save compressed files."
        )


if __name__ == "__main__":
    app = QApplication([])
    window = GLBCompressorApp()
    window.show()
    app.exec()
