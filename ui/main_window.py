import sys
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QPixmap, QPainter, QPen, QGuiApplication
from PIL import ImageGrab
from PyQt5.QtWidgets import QDialog  # 导入 QDialog
from PyQt5.QtCore import QRect  # 添加这行导入
import pytesseract


from skimage.metrics import structural_similarity as ssim
import numpy as np
from ocr.ocr_extractor import extract_text
import config

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Screenshot Translator")
        self.setGeometry(100, 100, 800, 600)

        # UI 元素
        self.label = QLabel("请选择一个区域进行截屏", self)
        self.label.setAlignment(Qt.AlignCenter)
        self.setCentralWidget(self.label)

        # 截屏按钮（仅第一次使用）
        self.screenshot_button = QPushButton("选区截屏", self)
        self.screenshot_button.clicked.connect(self.select_screen_area)
        self.screenshot_button.setGeometry(10, 10, 100, 30)

        # 定时器：每 1 秒检测内容变化
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_for_updates)

        # 状态变量
        self.previous_screenshot = None
        self.selected_rect = None  # 保存选区坐标
        self.region_selected = False  # 标志变量，确保选区只选一次

    def select_screen_area(self):
        if not self.region_selected:
            # 执行框选操作
            self.selected_rect = self.capture_selected_area()
            self.previous_screenshot = ImageGrab.grab(bbox=self.selected_rect)
            self.region_selected = True
            self.screenshot_button.setDisabled(True)  # 禁用按钮，防止重复选区
            self.timer.start(1000)  # 开始检测内容变化
            print(f"选区坐标: {self.selected_rect}")
        else:
            print("选区已完成，不能重复选取！")

    def capture_selected_area(self):
        """ 选区截图功能 """
        screen = QGuiApplication.primaryScreen().grabWindow(0)
        selector = RegionSelector(screen)
        if selector.exec():
            x, y, width, height = selector.selected_rect.getRect()
            # 标准化坐标，确保 left < right, top < bottom
            left = min(x, x + width)
            top = min(y, y + height)
            right = max(x, x + width)
            bottom = max(y, y + height)
            return (left, top, right, bottom)  # 返回修正后的坐标
        else:
            return None

    def check_for_updates(self):
        """ 检测选区内容变化 """
        if self.selected_rect is None:
            return

        current_screenshot = ImageGrab.grab(bbox=self.selected_rect)
        curr_array = np.array(current_screenshot)

        # 确保截图尺寸和格式一致
        prev_array = np.array(self.previous_screenshot.resize(current_screenshot.size))
        if prev_array.ndim == 3:
            prev_array = np.mean(prev_array, axis=2).astype(np.uint8)
        if curr_array.ndim == 3:
            curr_array = np.mean(curr_array, axis=2).astype(np.uint8)

        similarity = ssim(prev_array, curr_array)
        print(f"相似度: {similarity}")

        if similarity < 0.9:  # 相似度低于 90% 时触发 OCR
            print("检测到内容变化，重新进行 OCR...")
            self.previous_screenshot = current_screenshot
            text = self.perform_ocr(current_screenshot)
            self.display_result(text)


    def perform_ocr(self, image):
        """ OCR 提取文本 - 使用 Tesseract OCR """
        text = pytesseract.image_to_string(image, lang='jpn')  # 指定日语语言包
        print("OCR 结果:", text)
        return text

    def display_result(self, text):
        """ 显示 OCR 提取的结果 """
        self.label.setText(f"提取的文本: {text}")


class RegionSelector(QDialog):
    """ 区域选择器（支持鼠标框选） """
    def __init__(self, pixmap):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setCursor(Qt.CrossCursor)
        self.setWindowOpacity(0.7)
        self.selected_rect = None
        self.pixmap = pixmap
        self.start_pos = None
        self.end_pos = None
        self.showFullScreen()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.pixmap)
        if self.start_pos and self.end_pos:
            painter.setPen(QPen(Qt.red, 2, Qt.SolidLine))
            rect = self.rect_from_points(self.start_pos, self.end_pos)
            painter.drawRect(rect)

    def mousePressEvent(self, event):
        self.start_pos = event.pos()
        self.end_pos = None
        self.update()

    def mouseMoveEvent(self, event):
        self.end_pos = event.pos()
        self.update()

    def mouseReleaseEvent(self, event):
        self.end_pos = event.pos()
        self.selected_rect = self.rect_from_points(self.start_pos, self.end_pos)
        self.accept()

    def rect_from_points(self, p1, p2):
        """ 根据起始和结束点返回 QRect """
        from PyQt5.QtCore import QRect
        return QRect(min(p1.x(), p2.x()), min(p1.y(), p2.y()),
                     abs(p1.x() - p2.x()), abs(p1.y() - p2.y()))