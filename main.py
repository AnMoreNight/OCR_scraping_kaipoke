"""
Email Listener - Main Application with PyQt6 UI
Simple interface for monitoring emails and processing OCR data to Kaipoke
"""

import sys
import threading
import time
import io
import subprocess
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QPushButton, QTextEdit, QLabel, QStatusBar,
                             QMessageBox, QSplitter)
from PyQt6.QtCore import QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QTextCursor
from email_listener import EmailListener, log_print
import logging

class LogCapture:
    """Capture stdout and send to UI"""
    def __init__(self, log_callback):
        self.log_callback = log_callback
        self.original_stdout = sys.stdout
        
    def write(self, text):
        if text.strip():  # Only send non-empty lines
            self.log_callback(text.strip())
        return len(text)
    
    def flush(self):
        pass

class EmailListenerThread(QThread):
    """Thread for running email listener in background"""
    log_signal = pyqtSignal(str)
    status_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.listener = None
        self.running = False
        self.log_capture = None
        
    def run(self):
        """Run email listener in background thread"""
        try:
            self.status_signal.emit("メールリスナーを初期化中...")
            self.log_signal.emit("🚀 メールリスナーサービスを開始中...")
            
            # Set up log capture to redirect stdout to UI
            self.log_capture = LogCapture(self.log_signal.emit)
            sys.stdout = self.log_capture
            
            # Create email listener
            self.listener = EmailListener()
            
            # Connect to email server
            if not self.listener.connect():
                self.error_signal.emit("❌ メールサーバーへの接続に失敗しました")
                self.status_signal.emit("接続失敗")
                return
            
            self.status_signal.emit("接続完了 - メールを監視中...")
            self.log_signal.emit("📧 メールリスナーが正常に開始されました!")
            
            # Start listening
            self.running = True
            self.listener.listen(check_interval=30)
            
        except Exception as e:
            self.error_signal.emit(f"❌ 致命的エラー: {e}")
            self.status_signal.emit("エラー")
        finally:
            # Restore original stdout
            if self.log_capture:
                sys.stdout = self.log_capture.original_stdout
            self.running = False
            self.status_signal.emit("停止")
    
    def stop(self):
        """Stop the email listener"""
        self.running = False
        if self.listener:
            try:
                self.listener.stop()  # Request stop first
                self.listener.disconnect()
            except:
                pass

class EmailListenerUI(QMainWindow):
    """Main UI Window for Email Listener"""
    
    def __init__(self):
        super().__init__()
        self.listener_thread = None
        self.init_ui()
        
    def init_ui(self):
        """Initialize the UI components"""
        self.setWindowTitle("メールリスナー - OCRからKaipokeへ")
        self.setGeometry(100, 100, 900, 700)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Create title
        title_label = QLabel("📧 メールリスナーサービス")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #2c3e50; margin: 15px; text-align: center;")
        main_layout.addWidget(title_label)
        
        # Create subtitle
        subtitle_label = QLabel("メール監視 → OCRデータ抽出 → Kaipokeアップロード")
        subtitle_font = QFont()
        subtitle_font.setPointSize(12)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setStyleSheet("color: #7f8c8d; margin: 5px; text-align: center;")
        main_layout.addWidget(subtitle_label)
        
        # Create control buttons layout
        control_layout = QHBoxLayout()
        
        # Start button
        self.start_button = QPushButton("▶️ サービス開始")
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 15px 30px;
                font-size: 16px;
                font-weight: bold;
                border-radius: 8px;
                min-width: 150px;
            }
            QPushButton:hover {
                background-color: #229954;
                transform: scale(1.05);
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.start_button.clicked.connect(self.start_service)
        control_layout.addWidget(self.start_button)
        
        # Stop button
        self.stop_button = QPushButton("⏹️ サービス停止")
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 15px 30px;
                font-size: 16px;
                font-weight: bold;
                border-radius: 8px;
                min-width: 150px;
            }
            QPushButton:hover {
                background-color: #c0392b;
                transform: scale(1.05);
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.stop_button.clicked.connect(self.stop_service)
        self.stop_button.setEnabled(False)
        control_layout.addWidget(self.stop_button)
        
        # Clear logs button
        self.clear_button = QPushButton("🗑️ ログクリア")
        self.clear_button.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                border: none;
                padding: 15px 30px;
                font-size: 16px;
                font-weight: bold;
                border-radius: 8px;
                min-width: 150px;
            }
            QPushButton:hover {
                background-color: #e67e22;
                transform: scale(1.05);
            }
        """)
        self.clear_button.clicked.connect(self.clear_logs)
        control_layout.addWidget(self.clear_button)
        
        # Add stretch to push buttons to the left
        control_layout.addStretch()
        main_layout.addLayout(control_layout)
        
        # Logs panel
        logs_label = QLabel("📋 サービスログ")
        logs_label.setStyleSheet("font-weight: bold; color: #34495e; margin: 10px 5px; font-size: 14px;")
        main_layout.addWidget(logs_label)
        
        self.logs_text = QTextEdit()
        self.logs_text.setStyleSheet("""
            QTextEdit {
                background-color: #2c3e50;
                color: #ecf0f1;
                border: 2px solid #34495e;
                border-radius: 8px;
                padding: 15px;
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 13px;
                line-height: 1.4;
            }
        """)
        self.logs_text.setReadOnly(True)
        main_layout.addWidget(self.logs_text)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #34495e;
                color: #ecf0f1;
                border-top: 2px solid #2c3e50;
                padding: 8px;
                font-size: 12px;
                font-weight: bold;
            }
        """)
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("準備完了 - 'サービス開始'をクリックしてメール監視を開始してください")
        
        # Add initial log messages
        self.add_log("📱 メールリスナーUIが開始されました")
        self.add_log("💡 'サービス開始'をクリックしてメール監視を開始してください")
        self.add_log("📧 サービスは画像添付ファイル付きのメールを処理します")
        self.add_log("🔄 OCRが構造化データを抽出し、Kaipokeにアップロードします")
        self.add_log("⚙️ .envファイルに必要な認証情報が設定されていることを確認してください")
        
    def add_log(self, message):
        """Add a log message to the logs panel"""
        timestamp = time.strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        
        self.logs_text.append(formatted_message)
        
        # Auto-scroll to bottom
        cursor = self.logs_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.logs_text.setTextCursor(cursor)
        
    def start_service(self):
        """Start the email listener service"""
        try:
            self.add_log("🚀 メールリスナーサービスを開始中...")
            
            # Create and start listener thread
            self.listener_thread = EmailListenerThread()
            self.listener_thread.log_signal.connect(self.add_log)
            self.listener_thread.status_signal.connect(self.update_status)
            self.listener_thread.error_signal.connect(self.show_error)
            self.listener_thread.start()
            
            # Update UI
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.status_bar.showMessage("サービス開始中...")
            
        except Exception as e:
            self.add_log(f"❌ サービス開始エラー: {e}")
            self.show_error(f"サービス開始に失敗しました: {e}")
    
    def stop_service(self):
        """Stop the email listener service"""
        try:
            self.add_log("⏹️ メールリスナーサービスを停止中...")
            
            if self.listener_thread and self.listener_thread.isRunning():
                self.listener_thread.stop()
                self.listener_thread.wait(5000)  # Wait up to 5 seconds
                
            # Update UI
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.status_bar.showMessage("サービス停止")
            self.add_log("✅ サービスが正常に停止しました")
                    
        except Exception as e:
            self.add_log(f"❌ サービス停止エラー: {e}")
    
    def update_status(self, status):
        """Update status bar message"""
        self.status_bar.showMessage(status)
        self.add_log(f"📊 ステータス: {status}")
    
    def show_error(self, error_message):
        """Show error message in dialog and logs"""
        self.add_log(error_message)
        QMessageBox.critical(self, "エラー", error_message)
        
        # Reset UI state
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.status_bar.showMessage("エラーが発生しました")
    
    def clear_logs(self):
        """Clear the logs panel"""
        self.logs_text.clear()
        self.add_log("🗑️ ログをクリアしました")
    
    def closeEvent(self, event):
        """Handle application close event"""
        if self.listener_thread and self.listener_thread.isRunning():
            reply = QMessageBox.question(self, '終了', 
                                       'サービスが実行中です。停止して終了しますか？',
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            
            if reply == QMessageBox.StandardButton.Yes:
                self.stop_service()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

def main():
    """Main function to run the UI application"""
    try:
        # Create QApplication
        app = QApplication(sys.argv)
        
        # Set application properties
        app.setApplicationName("メールリスナー")
        app.setApplicationVersion("1.0")
        
        # Set application style
        app.setStyleSheet("""
            QMainWindow {
                background-color: #ecf0f1;
            }
            QWidget {
                background-color: #ecf0f1;
            }
        """)
        
        # Create and show main window
        window = EmailListenerUI()
        window.show()
        
        # Run application
        sys.exit(app.exec())
        
    except ImportError as e:
        print(f"❌ インポートエラー: {e}")
        print("💡 PyQt6をインストールしてください:")
        print("   pip install PyQt6")
        sys.exit(1)
    except Exception as e:
        print(f"❌ UI開始エラー: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()