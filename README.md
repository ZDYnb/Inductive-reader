# Inductive-reader

Double-click the `setup_and_run.bat` file to run if you are using windows computer

## Mac setup
## Quick Start (Mac / Linux)

### Prerequisites
This tool requires **Python 3**. If you do not have it installed, the setup script will alert you. You can install it using one of these two methods:
* **Option 1 (Easiest):** Download and run the official macOS installer from [python.org](https://www.python.org/downloads/macos/).
* **Option 2 (Homebrew):** If you use Homebrew, simply open your terminal and run `brew install python`.

### Installation & Launch
To run the automated setup script on a Mac, you need to grant it execution permissions the very first time you download the repository.

1. Open your **Terminal** and navigate to the downloaded repository folder.
2. Run this command to make the script executable (you only do this once):
   ```bash
   chmod +x setup_and_run.sh

### How to Find Your Port

Before running the visualizer, you need to tell the code where to look for the sensor data. Open `src/main.py` and update the `TARGET_PORT` variable at the top of the file.

**For Windows Users:**
1. Open **Device Manager**.
2. Expand the **Ports (COM & LPT)** section.
3. Look for your connected USB device (e.g., `COM6`).
4. Update the code: `TARGET_PORT = "COM6"`

**For Mac Users:**
1. Plug in your development board via USB.
2. Open your **Terminal**.
3. Type the following command and press Enter:
   ```bash
   ls /dev/cu.*