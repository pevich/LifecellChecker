import sys
import time
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit, QLabel, QFileDialog
)
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class LifecellChecker(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lifecell Number Checker")
        self.setGeometry(300, 200, 600, 400)

        layout = QVBoxLayout()

        self.label = QLabel("Виберіть TXT файл з номерами (один номер на рядок):")
        layout.addWidget(self.label)

        self.text_area = QTextEdit()
        layout.addWidget(self.text_area)

        self.load_btn = QPushButton("Завантажити файл")
        self.load_btn.clicked.connect(self.load_file)
        layout.addWidget(self.load_btn)

        self.start_btn = QPushButton("Старт перевірки")
        self.start_btn.clicked.connect(self.start_check)
        layout.addWidget(self.start_btn)

        self.setLayout(layout)

        self.driver = None

    def load_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Відкрити файл", "", "Text Files (*.txt)")
        if file_name:
            with open(file_name, "r", encoding="utf-8") as f:
                numbers = f.read()
            self.text_area.setPlainText(numbers)

    def start_check(self):
        numbers = self.text_area.toPlainText().splitlines()
        if not numbers:
            self.label.setText("Файл порожній!")
            return

        self.label.setText("Відкриваємо браузер... Авторизуйтесь на сайті!")
        self.init_driver()
        self.driver.get("https://my-ambassador.lifecell.ua")

        input("Після авторизації натисніть Enter тут...")

        for number in numbers:
            self.check_number(number.strip())
        
        self.label.setText("Перевірка завершена!")
        self.driver.quit()

    def init_driver(self):
        chrome_path = os.path.join(os.getcwd(), "chrome-win", "chrome.exe")
        chromedriver_path = os.path.join(os.getcwd(), "chromedriver.exe")

        options = Options()
        options.binary_location = chrome_path
        options.add_experimental_option("excludeSwitches", ["enable-logging"])

        service = Service(chromedriver_path)
        self.driver = webdriver.Chrome(service=service, options=options)

    def click_client_button(self):
        try:
            client_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'Клієнт')]"))
            )
            client_btn.click()
        except TimeoutException:
            print("Не вдалося знайти кнопку Клієнт")
            return False
        return True

    def check_number(self, number):
        if not self.click_client_button():
            return

        try:
            input_field = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "msisdn"))
            )
            input_field.click()
            input_field.clear()
            input_field.send_keys(number)

            search_btn = self.driver.find_element(By.XPATH, "//button[.//span[text()='Пошук']]")
            search_btn.click()

            time.sleep(2)

            try:
                unknown = self.driver.find_element(By.XPATH, "//div[contains(@class, 'text') and text()='UNKNOWN']")
                print(f"{number} - UNKNOWN")
                self.back_to_client()
                return
            except NoSuchElementException:
                pass

            try:
                lte_no_support = self.driver.find_element(By.XPATH, "//div[contains(@class, 'device-no-support') and text()='LTE']")
                print(f"{number} - LTE (не підтримується)")
                self.back_to_client()
                return
            except NoSuchElementException:
                pass

            try:
                lte_support = self.driver.find_element(By.XPATH, "//div[contains(@class, 'support') and text()='LTE']")
                print(f"{number} - LTE (підтримується), реєстрація стартового пакету")
                self.register_start_package()
            except NoSuchElementException:
                print(f"{number} - Результат невідомий")
                self.back_to_client()
        except Exception as e:
            print(f"Помилка з номером {number}: {e}")
            self.back_to_client()

    def back_to_client(self):
        try:
            back_btn = self.driver.find_element(By.XPATH, "//mat-icon[text()='arrow_back']")
            back_btn.click()
            time.sleep(1)
        except NoSuchElementException:
            print("Не вдалося натиснути кнопку Назад")

    def register_start_package(self):
        try:
            start_btn = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'Реєстрація стартового пакету')]"))
            )
            start_btn.click()
            time.sleep(1)
            register_btn = self.driver.find_element(By.XPATH, "//button[.//span[text()='Зареєструвати']]")
            register_btn.click()
            time.sleep(1)
        except Exception as e:
            print(f"Помилка реєстрації: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LifecellChecker()
    window.show()
    sys.exit(app.exec_())
