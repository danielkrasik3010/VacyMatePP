#!/usr/bin/env python3
"""
Startup script for VacayMate Streamlit UI
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    print("🚀 Starting VacayMate Streamlit UI...")
    print()
    print("The app will open in your default browser at http://localhost:8501")
    print()
    print("To stop the app, press Ctrl+C in the terminal.")
    print()
    
    # Change to UI directory
    ui_dir = Path(__file__).parent / "UI"
    os.chdir(ui_dir)
    
    try:
        # Run streamlit
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"], check=True)
    except KeyboardInterrupt:
        print("\n👋 VacayMate UI stopped. Thanks for using VacayMate!")
    except FileNotFoundError:
        print("❌ Streamlit not found. Please install it with: pip install streamlit")
        return 1
    except Exception as e:
        print(f"❌ Error starting Streamlit: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
