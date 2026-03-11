import sys
import serial
import numpy as np
import re
from PyQt5 import QtWidgets, QtCore, QtGui
import pyqtgraph as pg

# --- CONFIGURATION ---
# TARGET_PORT = "/dev/cu.usbmodem14101"  # Change to "COM6" for Windows
TARGET_PORT = "COM6"  # Default for Windows users
DEFAULT_BAUD = 115200
WINDOW_SIZE = 500  

class ADCOscilloscope(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        # --- Core Variables ---
        self.ser = None
        self.data_buffer = np.zeros(WINDOW_SIZE)
        
        # --- Trigger State Machine ---
        self.is_triggered = False
        self.trigger_stopped = False
        self.post_trigger_count = 0
        self.current_peak = 0
        
        # --- UI Setup ---
        self.setWindowTitle("Inductive ADC Helper - Pro Visualizer")
        self.resize(1050, 650)
        self.setCentralWidget(QtWidgets.QWidget())
        self.layout = QtWidgets.QVBoxLayout(self.centralWidget())
        self.setStyleSheet("QMainWindow { background-color: #121212; } QLabel { color: white; }")

        # --- Toolbar 1: Connection ---
        self.top_layout = QtWidgets.QHBoxLayout()
        self.port_label = QtWidgets.QLabel(f"Target Port: {TARGET_PORT}")
        self.port_label.setStyleSheet("font-size: 14px; font-weight: bold; color: gray;")
        
        self.btn_connect = QtWidgets.QPushButton("Connect")
        self.btn_connect.setFixedWidth(100)
        self.btn_connect.clicked.connect(self.toggle_connection)
        
        self.value_label = QtWidgets.QLabel("Live: ----")
        self.value_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #00f0ff; margin-left: 20px;")
        
        self.top_layout.addWidget(self.port_label)
        self.top_layout.addWidget(self.btn_connect)
        self.top_layout.addWidget(self.value_label)
        self.top_layout.addStretch() 
        self.layout.addLayout(self.top_layout)

        # --- Toolbar 2: Trigger & Cursor Controls ---
        self.trigger_layout = QtWidgets.QHBoxLayout()
        
        self.chk_trigger = QtWidgets.QCheckBox("Enable Trigger Mode")
        self.chk_trigger.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffcc00;")
        
        self.trigger_layout.addWidget(QtWidgets.QLabel("Threshold:"))
        self.thresh_input = QtWidgets.QSpinBox()
        self.thresh_input.setRange(0, 4096)
        self.thresh_input.setValue(4090) 
        self.trigger_layout.addWidget(self.thresh_input)
        
        self.trigger_layout.addWidget(QtWidgets.QLabel("Post-Samples:"))
        self.samples_input = QtWidgets.QSpinBox()
        self.samples_input.setRange(1, 1000)
        self.samples_input.setValue(100) 
        self.trigger_layout.addWidget(self.samples_input)
        
        self.btn_arm = QtWidgets.QPushButton("Arm / Reset Trigger")
        self.btn_arm.setStyleSheet("background-color: #333333; color: white;")
        self.btn_arm.clicked.connect(self.arm_trigger)
        self.trigger_layout.addWidget(self.btn_arm)
        
        self.peak_label = QtWidgets.QLabel("Peak: ----")
        self.peak_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #ff00ff; margin-left: 15px;")
        
        # --- NEW: Cursor Readout Label ---
        self.cursor_label = QtWidgets.QLabel("Cursor: Hover over graph")
        self.cursor_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #aaff00; margin-left: 15px;")
        
        self.trigger_layout.addWidget(self.chk_trigger)
        self.trigger_layout.addWidget(self.peak_label)
        self.trigger_layout.addWidget(self.cursor_label)
        self.trigger_layout.addStretch()
        self.layout.addLayout(self.trigger_layout)

        # --- Plot Area ---
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('#121212')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.curve = self.plot_widget.plot(self.data_buffer, pen=pg.mkPen(color='#00f0ff', width=2))
        
        self.plot_widget.setLabel('left', 'Amplitude', units='Raw')
        self.plot_widget.setLabel('bottom', 'Sample History')
        self.plot_widget.getAxis('left').enableAutoSIPrefix(False)
        self.layout.addWidget(self.plot_widget)

        # --- NEW: Crosshair Setup ---
        self.vLine = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen(color='#aaff00', style=QtCore.Qt.DashLine))
        self.hLine = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen(color='#aaff00', style=QtCore.Qt.DashLine))
        self.plot_widget.addItem(self.vLine, ignoreBounds=True)
        self.plot_widget.addItem(self.hLine, ignoreBounds=True)
        
        # Connect mouse movement to our custom function
        self.plot_widget.scene().sigMouseMoved.connect(self.mouse_moved)

        # --- Timer ---
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(10)

    def mouse_moved(self, pos):
        """Updates the crosshair and cursor label when the mouse hovers over the plot."""
        if self.plot_widget.sceneBoundingRect().contains(pos):
            # Convert screen coordinates to plot coordinates
            mousePoint = self.plot_widget.plotItem.vb.mapSceneToView(pos)
            index = int(mousePoint.x())
            
            # Make sure we are within the bounds of the array
            if 0 <= index < len(self.data_buffer):
                # Get the actual Y value from our data buffer!
                y_val = self.data_buffer[index]
                
                # Snap lines to the data point
                self.vLine.setPos(mousePoint.x())
                self.hLine.setPos(y_val)
                
                # Update label text
                self.cursor_label.setText(f"Cursor: X={index}, Y={int(y_val)}")

    def arm_trigger(self):
        """Resets the state machine so it can look for a new peak."""
        self.is_triggered = False
        self.trigger_stopped = False
        self.post_trigger_count = 0
        self.current_peak = 0
        self.peak_label.setText("Peak: Waiting...")
        self.peak_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #ffcc00; margin-left: 15px;")
        
        if self.ser and self.ser.is_open:
            self.ser.reset_input_buffer()

    def toggle_connection(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
            self.btn_connect.setText("Connect")
            self.btn_connect.setStyleSheet("")
            self.value_label.setText("Live: ----")
        else:
            try:
                self.ser = serial.Serial(TARGET_PORT, DEFAULT_BAUD, timeout=0.01)
                self.btn_connect.setText("Disconnect")
                self.btn_connect.setStyleSheet("background-color: #aa0000; color: white;")
                self.arm_trigger()
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Connection Error", f"Could not open {TARGET_PORT}\n{e}")

    def update_plot(self):
        if not self.ser or not self.ser.is_open:
            return
            
        try:
            while self.ser.in_waiting > 0:
                raw_line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                
                match = re.search(r"Raw:\s*(\d+)", raw_line)
                if match:
                    val = float(match.group(1))
                    
                    if self.chk_trigger.isChecked() and self.trigger_stopped:
                        continue 
                    
                    self.data_buffer[:-1] = self.data_buffer[1:]
                    self.data_buffer[-1] = val
                    self.value_label.setText(f"Live: {int(val)}")
                    
                    if self.chk_trigger.isChecked():
                        if not self.is_triggered and val >= self.thresh_input.value():
                            self.is_triggered = True
                            self.post_trigger_count = self.samples_input.value()
                            self.current_peak = val
                            
                        elif self.is_triggered:
                            self.current_peak = max(self.current_peak, val)
                            self.post_trigger_count -= 1
                            
                            if self.post_trigger_count <= 0:
                                self.trigger_stopped = True
                                self.peak_label.setText(f"Peak: {int(self.current_peak)}")
                                self.peak_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #00ff00; margin-left: 15px;")
            
            if not (self.chk_trigger.isChecked() and self.trigger_stopped):
                self.curve.setData(self.data_buffer)
                
                valid_data = self.data_buffer[self.data_buffer > 0]
                if len(valid_data) > 0:
                    smooth_center = np.mean(valid_data[-50:])
                    self.plot_widget.setYRange(smooth_center - 50, smooth_center + 50)
                    
        except Exception:
            pass 

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion") 
    window = ADCOscilloscope()
    window.show()
    sys.exit(app.exec())