import os
import time
import requests
import threading
import logging
import mmap
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# ================================
# CONFIGURATION
# ================================
BOT_TOKEN = ""  # Replace with correct bot token
CHAT_ID = ""  # Replace with correct chat ID

# Telegram API URLs
SEND_MESSAGE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
SEND_FILE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
GET_UPDATES_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"

# Files to watch
FILES_TO_WATCH = [
        "/data/data/com.termux/files/home/keyhunt/KEYFOUNDKEYFOUND.txt",
        "/data/data/com.termux/files/home/balance.txt",
        "/data/data/com.termux/files/home/eth/ETHEREUMFOUND.txt",
        "/data/data/com.termux/files/home/FOUNDCASA.txt",
        "mnt/g/heart/prog/roto/found.txt",
        "mnt/g/heart/prog/kang/shubkang.txt",
        "mnt/g/heart/prog/shathecure/FOUND.txt",
        "mnt/g/heart/prog/rsz/FOUND.txt",
        "mnt/g/heart/prog/match/match.txt",
        "G:/heart/bitcoin/rsz/found.txt",
        "G:/heart/solana/match/match.txt",
        "G:/heart/eth/kang/KANGETH.txt",
        "KEYFOUNDKEYFOUND.txt",
        "path/to/your/file.txt"
]

FILES_TO_WATCH = [os.path.abspath(f) for f in FILES_TO_WATCH]

# Ensure directories exist
for file in FILES_TO_WATCH:
    os.makedirs(os.path.dirname(file), exist_ok=True)

# Persistent tracking of file states
file_data = {
    file: {
        "size": os.path.getsize(file) if os.path.exists(file) else 0,
        "created": time.ctime(os.path.getctime(file)) if os.path.exists(file) else "Not Found"
    } for file in FILES_TO_WATCH
}

# Setup Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

# ================================
# TELEGRAM MESSAGE FUNCTIONS
# ================================
def send_message(text):
    """Send a text message to Telegram."""
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try:
        response = requests.post(SEND_MESSAGE_URL, data=payload)
        response.raise_for_status()
        logging.info(f"Message sent: {text}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending message: {e}")

def send_file(file_path):
    """Send a file to Telegram, or fallback to sending its content."""
    try:
        with open(file_path, "rb") as file:
            response = requests.post(
                SEND_FILE_URL, data={"chat_id": CHAT_ID}, files={"document": file}
            )
            response.raise_for_status()
            logging.info(f"File '{file_path}' sent successfully!")
    except Exception as e:
        logging.error(f"Error sending file '{file_path}': {e}")
        send_file_content(file_path)

def send_file_content(file_path):
    """Send file content as a message if sending the file fails."""
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            with mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ) as mmapped_file:
                content = mmapped_file.read(4000).decode('utf-8', errors='ignore')
                send_message(f"📄 *{os.path.basename(file_path)} Content:*\n```\n{content}\n```")
    except Exception as e:
        send_message(f"Error reading file '{file_path}': {e}")

# ================================
# FILE MONITORING CLASS
# ================================
class FileEventHandler(FileSystemEventHandler):
    def on_created(self, event):
        """Triggered when a file is created."""
        if not event.is_directory:
            self.process(event.src_path, created=True)

    def on_modified(self, event):
        """Triggered when a file is modified."""
        if not event.is_directory:
            self.process(event.src_path, created=False)

    def process(self, file_path, created=False):
        """Handles new or modified files."""
        abs_path = os.path.abspath(file_path)

        if abs_path in FILES_TO_WATCH:
            new_size = os.path.getsize(abs_path)
            if created or new_size > file_data[abs_path]["size"]:
                file_data[abs_path]["size"] = new_size
                file_data[abs_path]["created"] = time.ctime(os.path.getctime(abs_path))
                
                send_message(f"✅ STATUS: FOUND : {os.path.basename(abs_path)} || {new_size} bytes")
                time.sleep(1)
                send_file(abs_path)

# ================================
# COMMAND HANDLER FUNCTION
# ================================
def handle_commands():
    """Continuously checks for Telegram bot commands."""
    last_update_id = None
    while True:
        try:
            response = requests.get(GET_UPDATES_URL, params={"offset": last_update_id})
            response.raise_for_status()
            data = response.json()

            if "result" in data:
                for update in data["result"]:
                    last_update_id = update["update_id"] + 1
                    if "message" in update:
                        text = update["message"].get("text", "").strip().lower()
                        if text == "/start":
                            send_message("👋 HELLO MASTER, HOW YOU’RE???\n🚀🔥 LET'S FIND THE SHIT OUT OF THE WORLD! I LNOW YOU CAN COOK THE WHOLE WORLD")
                        elif text == "/update":
                            send_message("🔄 Checking for file updates...")
                            check_files()
                        elif text == "/size":
                            send_sizes()
                        elif text == "/filz":
                            send_created_files()
                        elif text == "/cat":
                            send_all_file_contents()
        except Exception as e:
            logging.error(f"Error in command handler: {e}")
        time.sleep(5)

# ================================
# MANUAL FILE CHECK FUNCTIONS
# ================================
def check_files():
    """Manually check files for creation or size increase."""
    for file_path in FILES_TO_WATCH:
        if os.path.exists(file_path):
            new_size = os.path.getsize(file_path)
            if new_size > file_data[file_path]["size"]:
                file_data[file_path]["size"] = new_size
                send_message(f"✅ STATUS : FOUND : {os.path.basename(file_path)} || {new_size} bytes")
                send_file(file_path)

def send_sizes():
    """Send file sizes of watched files."""
    sizes = [f"{os.path.basename(f)} || {file_data[f]['size']} bytes" for f in FILES_TO_WATCH if os.path.exists(f)]
    send_message("📂 File Sizes:\n" + "\n".join(sizes) if sizes else "⚠ No tracked files found.")

def send_created_files():
    """Send a list of created files along with timestamps."""
    created_files = [f"{os.path.basename(f)} || {file_data[f]['created']}" for f in FILES_TO_WATCH if os.path.exists(f)]
    send_message("📁 Tracked Files Created:\n" + "\n".join(created_files) if created_files else "⚠ No files created yet.")

def send_all_file_contents():
    """Send the content of all existing files."""
    for file_path in FILES_TO_WATCH:
        if os.path.exists(file_path):
            send_file_content(file_path)

# ================================
# MAIN FUNCTION TO START MONITORING
# ================================
if __name__ == "__main__":
    send_message("👋 HELLO MASTER, HOW YOU’RE???\n🚀🔥 THE SERVER IS RUNNING WELL")
    event_handler = FileEventHandler()
    observer = Observer()

    monitored_dirs = {os.path.dirname(f) for f in FILES_TO_WATCH}
    for directory in monitored_dirs:
        observer.schedule(event_handler, directory, recursive=False)

    observer.start()
    threading.Thread(target=handle_commands, daemon=True).start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()

                
