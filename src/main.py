import sys
import serial
import numpy as np
import re
from PyQt5 import QtWidgets, QtCore, QtGui
import pyqtgraph as pg

# --- CONFIGURATION ---
TARGET_PORT = "COM6"  
DEFAULT_BAUD = 115200
WINDOW_SIZE = 500  

class ADCOscilloscope(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        # --- Initialize Variables ---
        self.ser = None
        self.data_buffer = np.zeros(WINDOW_SIZE)
        
        # --- UI Setup ---
        self.setWindowTitle("Inductive ADC Helper - Pro Visualizer")
        self.resize(1000, 600)
        self.setCentralWidget(QtWidgets.QWidget())
        self.layout = QtWidgets.QVBoxLayout(self.centralWidget())
        
        # Dark Mode Styling
        self.setStyleSheet("QMainWindow { background-color: #121212; } QLabel { color: white; }")

        # --- Top Toolbar ---
        self.top_layout = QtWidgets.QHBoxLayout()
        
        self.port_label = QtWidgets.QLabel(f"Target Port: {TARGET_PORT}")
        self.port_label.setStyleSheet("font-size: 14px; font-weight: bold; color: gray;")
        
        self.btn_connect = QtWidgets.QPushButton("Connect")
        self.btn_connect.setFixedWidth(100)
        self.btn_connect.clicked.connect(self.toggle_connection)
        
        # --- NEW: Digital Readout Label ---
        self.value_label = QtWidgets.QLabel("Value: ----")
        self.value_label.setStyleSheet("font-size: 28px; font-weight: bold; color: #00f0ff; margin-left: 20px;")
        
        self.top_layout.addWidget(self.port_label)
        self.top_layout.addWidget(self.btn_connect)
        self.top_layout.addWidget(self.value_label) # Add readout to the top bar
        self.top_layout.addStretch() 
        
        self.layout.addLayout(self.top_layout)

        # --- Plot Area ---
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('#121212')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        
        # Line style: Neon Cyan
        self.curve = self.plot_widget.plot(
            self.data_buffer, 
            pen=pg.mkPen(color='#00f0ff', width=2)
        )
        
        # Set Labels
        self.plot_widget.setLabel('left', 'Amplitude', units='Raw')
        self.plot_widget.setLabel('bottom', 'Sample History')
        
        # Disable the "k" (kilo) prefix
        self.plot_widget.getAxis('left').enableAutoSIPrefix(False)
        
        self.layout.addWidget(self.plot_widget)

        # --- Timer for Live Updates ---
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(10)

    def toggle_connection(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
            self.btn_connect.setText("Connect")
            self.btn_connect.setStyleSheet("")
            self.value_label.setText("Value: ----")
            print("Disconnected.")
        else:
            try:
                self.ser = serial.Serial(TARGET_PORT, DEFAULT_BAUD, timeout=0.01)
                self.btn_connect.setText("Disconnect")
                self.btn_connect.setStyleSheet("background-color: #aa0000; color: white;")
                print(f"Connected to {TARGET_PORT}")
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Connection Error", f"Could not open {TARGET_PORT}\n{e}")

    def update_plot(self):
        if self.ser and self.ser.is_open:
            try:
                latest_value = None
                while self.ser.in_waiting > 0:
                    raw_line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    
                    match = re.search(r"Raw:\s*(\d+)", raw_line)
                    if match:
                        latest_value = float(match.group(1))
                        
                        self.data_buffer[:-1] = self.data_buffer[1:]
                        self.data_buffer[-1] = latest_value
                
                self.curve.setData(self.data_buffer)
                
                # --- Update the Digital Readout ---
                if latest_value is not None:
                    self.value_label.setText(f"Value: {int(latest_value)}")
                
                # --- Dynamic Y-Axis Zoom ---
                valid_data = self.data_buffer[self.data_buffer > 0]
                if len(valid_data) > 0:
                    smooth_center = np.mean(valid_data[-50:])
                    self.plot_widget.setYRange(smooth_center - 50, smooth_center + 50)
                
            except Exception as e:
                pass 

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion") 
    
    window = ADCOscilloscope()
    window.show()
    sys.exit(app.exec())