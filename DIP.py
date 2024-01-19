import os
import cv2
import numpy as np
import imghdr
from PIL import Image, ImageOps, ImageFilter
import io
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QPushButton, QFileDialog, QHBoxLayout, \
    QScrollArea, QFrame, QSplashScreen
from PyQt5.QtGui import QPixmap, QColor, QPalette, QImage, QPainter, QFont, QPen, QIcon, QLinearGradient, QBrush
from PyQt5.QtCore import Qt, QTimer
import io


def compress_image(image_path):
    # Check the format of the image
    img_format = imghdr.what(image_path)
    if img_format not in ['jpeg', 'png', 'webp', 'tiff']:
        raise ValueError("Unsupported image format")

    # Read the image
    image = Image.open(image_path)

    if img_format == 'jpeg':
        # Technique 1: Progressive encoding for JPEG
        compressed_image_1 = io.BytesIO()
        image.save(compressed_image_1, format=img_format, progressive=True, quality=85)

        # Technique 2: Adaptive Huffman Coding (Using OpenCV as a proxy)
        compressed_image_2 = io.BytesIO()
        image.save(compressed_image_2, format=img_format, quality=70, subsampling='4:2:2')

        # Custom Approach: Resolution reduction and different chroma subsampling
        compressed_image_3 = io.BytesIO()
        # Resize image if it's large
        if image.size[0] > 1920 or image.size[1] > 1080:
            image = image.resize((int(image.size[0] / 2), int(image.size[1] / 2)), Image.LANCZOS)
        image.save(compressed_image_3, format=img_format, quality=75, subsampling='4:2:0')

    elif img_format == 'tiff':
        # Technique 1: LZW Compression
        compressed_image_1 = io.BytesIO()
        image.save(compressed_image_1, format='TIFF', compression='tiff_lzw')

        # Technique 2: Bit-depth reduction if possible
        compressed_image_2 = io.BytesIO()
        if image.mode == 'RGBA' or image.mode == 'RGB':
            image.convert('P', palette=Image.ADAPTIVE).save(compressed_image_2, format='TIFF')
        else:
            image.save(compressed_image_2, format='TIFF')

        # Custom Approach: Grayscale conversion
        compressed_image_3 = io.BytesIO()
        gray_image = ImageOps.grayscale(image)
        gray_image.save(compressed_image_3, format='TIFF')


    elif img_format == 'png':

        # Technique 1: More aggressive Color Quantization

        compressed_image_1 = io.BytesIO()

        quantized_image = image.convert('P', palette=Image.WEB, colors=64)  # Reduced colors

        quantized_image.save(compressed_image_1, format='PNG')

        # Technique 2: High compression level with dithering

        compressed_image_2 = io.BytesIO()

        image.save(compressed_image_2, format='PNG', compress_level=9, optimize=True, dither=Image.FLOYDSTEINBERG)

        # Custom Approach: Aggressive color reduction and resizing for large images

        compressed_image_3 = io.BytesIO()

        if image.size[0] * image.size[1] > 1024 * 1024:  # Resize if larger than 1MP

            image = image.resize((int(image.size[0] / 2), int(image.size[1] / 2)), Image.LANCZOS)

        image = image.quantize(colors=32, method=Image.MAXCOVERAGE)

        image.save(compressed_image_3, format='PNG', compress_level=9)


    elif img_format == 'webp':

        # Adjust quality based on original file size

        original_size = os.path.getsize(image_path)

        quality = 50 if original_size > 100 * 1024 else 80  # Lower quality for larger files

        # Technique 1: WebP lossy compression with dynamic quality

        compressed_image_1 = io.BytesIO()

        image.save(compressed_image_1, format='WEBP', quality=quality)

        # Technique 2: WebP lossless compression

        compressed_image_2 = io.BytesIO()
        if original_size < 200 * 1024:  # Threshold for small images, e.g., 200 KB
            # Skip compression for already small/optimized images
            with open(image_path, 'rb') as original_image:
                compressed_image_2.write(original_image.read())
        else:
            # Apply moderate lossy compression for larger images
            moderate_quality = 70
            image.save(compressed_image_2, format='WEBP', quality=moderate_quality)

        # Custom Approach: Adjusting compression based on image size

        compressed_image_3 = io.BytesIO()
        quality = 80 if image.size[0] * image.size[1] > 500 * 500 else 90
        image.save(compressed_image_3, format='WEBP', quality=quality)

    return compressed_image_1, compressed_image_2, compressed_image_3

# Example usage
# compressed_images = compress_image(r'.\imgcode\road.jpg')
# img_format = imghdr.what(r'.\imgcode\road.jpg')
# for i, img in enumerate(compressed_images):
#     with open(f'compressed_image_{i}.{img_format}', 'wb') as f:
#         f.write(img.getbuffer())


class ImageCompressionApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setDarkTheme()
        self.setWindowTitle('Image Compression Viewer')
        # add logo
        self.setWindowIcon(QIcon('./imgcode/logo.svg'))
        self.resize(1700, 500)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.loadButton = QPushButton('Load Image')
        self.loadButton.setStyleSheet(
            "QPushButton { background-color: #0077b6; color: white; border-radius: 10px; height: 25px; padding: 10px; font-size: 18px; margin-top: 5px; margin-bottom: 5px; }"
            f"QPushButton:hover {{ background-color: {self.lighten_color('#0077b6')}; cursor: pointer; }}"
        )
        self.loadButton.clicked.connect(self.openImage)
        self.layout.addWidget(self.loadButton)


        self.scrollArea = QScrollArea()
        # self.scrollArea.setStyleSheet("QScrollArea { border-radius: 20px; border: 1px solid black; background-color: black; }")
        self.scrollArea.setStyleSheet(
            "QScrollArea { background-color: #464545; border-radius: 10px; }"
        )
        self.scrollAreaWidgetContents = QWidget()
        # add style to the label
        self.scrollAreaWidgetContents.setStyleSheet('''
                        QWidget { 
                        background: rgba(255, 255, 255, 0.34);
                        border-radius: 16px;
                        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
                        backdrop-filter: blur(7.7px);
                        -webkit-backdrop-filter: blur(7.7px);
                        border: 1px solid rgba(255, 255, 255, 0.3); 
                        content: "Please upload image";
                        }
                        '''
        )
        self.label = QLabel(self.scrollArea)
        self.label.setText("Please upload image")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet('''
            QLabel {
                font-size: 20px;
                color: white;
                text-shadow: 0 0 10px white;
            }
        ''')

        # Adjust the geometry of the label to be at the center of the window
        self.label.setGeometry(0, 300, self.width(), 40)
        # add a text label in the center of the scroll area


        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.scrollArea.setWidgetResizable(True)
        self.layout.addWidget(self.scrollArea)

        self.imageLayout = QHBoxLayout(self.scrollAreaWidgetContents)
        self.imageLabels = []

        # Initial placeholder image

    def resizeEvent(self, event):
        # Override the resize event to adjust the label's position when the window is resized
        self.label.setGeometry(0, self.height() / 3, self.width(), 40)

    @staticmethod
    def lighten_color(color, amount=120):
        return QColor(color).lighter(amount).name()

    def setDarkTheme(self):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ToolTipBase, Qt.red)
        palette.setColor(QPalette.ToolTipText, Qt.blue)
        palette.setColor(QPalette.Text, Qt.white)
        palette.setColor(QPalette.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.HighlightedText, Qt.black)
        self.setPalette(palette)

    def openImage(self):
        imagePath, _ = QFileDialog.getOpenFileName()
        if imagePath:
            self.scrollAreaWidgetContents.setStyleSheet(
                "QWidget { background-color: #464545; border-radius: 10px; color: white; }")
            # remove the label
            self.label.deleteLater()

            compressed_images = compress_image(imagePath)
            img_format = imghdr.what(imagePath)

            for label in self.imageLabels:
                self.imageLayout.removeWidget(label)
                label.deleteLater()
            self.imageLabels.clear()

            self.addImage(imagePath, "Original Image", img_format)

            technique_names = ["Progressive Encoding", "Adaptive Huffman Coding", "Custom Compression"]
            for i, img_bytes in enumerate(compressed_images):
                self.addImage(img_bytes, f"{technique_names[i]}", img_format)
        else:
            self.scrollAreaWidgetContents.setStyleSheet('''
                QWidget { 
                background: rgba(255, 255, 255, 0.34);
                border-radius: 16px;
                box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
                backdrop-filter: blur(7.7px);
                -webkit-backdrop-filter: blur(7.7px);
                border: 1px solid rgba(255, 255, 255, 0.3); 
                }
                '''
            )

    def addImage(self, image_source, title, img_format):
        frame = QFrame()
        layout = QVBoxLayout()
        frame.setLayout(layout)

        label = QLabel(title)
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)

        pixmap_label = QLabel()
        pixmap = QPixmap()
        if isinstance(image_source, str):
            pixmap.load(image_source)
        else:
            pixmap.loadFromData(image_source.getvalue(), img_format.upper())
        pixmap_label.setPixmap(pixmap.scaled(350, 350, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        layout.addWidget(pixmap_label)

        self.imageLayout.addWidget(frame)
        self.imageLabels.append(frame)

class SplashScreen(QSplashScreen):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Set dark background color
        self.setAutoFillBackground(True)
        palette = self.palette()

        # Assuming the size of the splash screen is known for gradient calculation
        gradient = QLinearGradient(0, 0, 0, 400)
        gradient.setColorAt(0.0, QColor('#D8B5FF'))  # Dark grey at the top
        gradient.setColorAt(1.0, QColor('#1EAE98'))  # Less dark grey at the bottom

        palette.setBrush(QPalette.Window, QBrush(gradient))
        self.setPalette(palette)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignCenter)

        # Icon layout
        icon_layout = QHBoxLayout()
        icon_layout.setAlignment(Qt.AlignCenter)

        # Icon Label
        icon_label = QLabel()
        icon_pixmap = QPixmap('imgcode/logo.svg')  # Replace with the path to your icon
        # add desgin to the icon
        icon_label.setStyleSheet(
            "QLabel { margin-top: -40px; margin-bottom: 10px; }"
        )
        icon_label.setPixmap(icon_pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        icon_layout.addWidget(icon_label)

        # Title label
        title_label = QLabel("Image Compression")
        title_label.setStyleSheet('''
                    QLabel {
                        margn-top: -10px;
                        font-size: 24px;
                        color: white;
                        font-weight: bold;
                    }
                ''')

        # Text label
        text_label = QLabel("Umar Javed")
        text_label.setStyleSheet('''
                    QLabel {
                        margin-left: 65%;
                        margin-top: 20px;
                        font-size: 16px;
                        color: white;
                    }
                ''')
        text_label.setWordWrap(True)
        text_label2 = QLabel("Waleed Khalid")
        text_label2.setStyleSheet('''
                    QLabel {
                        margin-left: 65%;

                        font-size: 16px;
                        color: white;
                    }
                ''')
        text_label2.setWordWrap(True)
        text_label3 = QLabel("Ali Haider")
        text_label3.setStyleSheet('''
                    QLabel {
                                            margin-left: 65%;

                        font-size: 16px;
                        color: white;
                    }
                ''')
        text_label3.setWordWrap(True)
        text_label4 = QLabel("Aliza Khokhar")
        text_label4.setStyleSheet('''
                            QLabel {
                                                    margin-left: 65%;

                                font-size: 16px;
                                color: white;
                            }
                        ''')
        text_label4.setWordWrap(True)

        # Add widgets to main layout
        main_layout.addLayout(icon_layout)
        main_layout.addWidget(title_label)
        main_layout.addWidget(text_label)
        main_layout.addWidget(text_label2)
        main_layout.addWidget(text_label3)
        main_layout.addWidget(text_label4)

        # Set layout and window properties
        wrapper_widget = QWidget()
        wrapper_widget.setLayout(main_layout)
        self.setCentralWidget(wrapper_widget)
        self.resize(386, 412)
        self.setStyleSheet("QWidget { border-radius: 20px; }")

    def center(self):
        # Center the splash screen on the screen
        screen = QApplication.primaryScreen()
        size = screen.size()
        self.move((size.width() - self.width()) / 2, (size.height() - self.height()) / 2)

    def setCentralWidget(self, widget):
        # Custom method to set the central widget with margins
        layout = QVBoxLayout(self)
        layout.addWidget(widget)
        layout.setContentsMargins(10, 10, 10, 10)  # Adjust margins as necessary
        self.setLayout(layout)



if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Create and show the main application window
    ex = ImageCompressionApp()

    # Create the splash screen
    splash = SplashScreen()
    splash.show()
    splash.center()

    # Close the splash screen after 2 seconds and show the main window
    QTimer.singleShot(3000, splash.close)
    QTimer.singleShot(3000, ex.show)

    sys.exit(app.exec_())
