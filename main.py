import threading
import os
import sys
from PIL import Image
import pystray
from service import YouTubeDiscordRPCService
from constants import CLIENT_ID

def quit_action(icon, item):
    icon.stop()
    os._exit(0)

def run_service():
    service = YouTubeDiscordRPCService(CLIENT_ID, 5432)
    service.run()

def main():
    # Start the service in a background thread
    service_thread = threading.Thread(target=run_service, daemon=True)
    service_thread.start()

    # Determine the icon path
    if getattr(sys, 'frozen', False):
        # If compiled with Nuitka/PyInstaller
        base_path = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    icon_path = os.path.join(base_path, 'tray', 'tray.png')
    
    # Load the icon
    try:
        image = Image.open(icon_path)
    except Exception:
        # Fallback to a blank image if the icon is missing
        image = Image.new('RGB', (64, 64), color=(255, 255, 255))

    # Create the tray icon
    menu = pystray.Menu(
        pystray.MenuItem('Quit', quit_action)
    )
    icon = pystray.Icon("Youtube Music Service", image, "Youtube Music Service", menu)
    
    icon.run()

if __name__ == "__main__":
    main()
