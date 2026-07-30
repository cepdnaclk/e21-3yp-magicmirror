import os
import time
import threading
import tkinter as tk
from PIL import Image, ImageTk
import boto3
from dotenv import load_dotenv

# ================= CONFIGURATION & PATHS =================
# Load AWS S3 configuration from .env file
load_dotenv()
AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
BUCKET_NAME = os.getenv('BUCKET_NAME')
AWS_REGION = os.getenv('AWS_DEFAULT_REGION', 'ap-southeast-1')

# Local directory where downloaded photos are kept
SLIDES_DIR = os.path.expanduser("~/slides")
os.makedirs(SLIDES_DIR, exist_ok=True)

# Slideshow interval in milliseconds (8000ms = 8 seconds)
SLIDESHOW_INTERVAL_MS = 8000

# ================= BACKGROUND S3 SYNC THREAD =================
def run_s3_sync_thread(gui_root):
    """Background worker that continuously syncs photos from S3 and alerts GUI of changes."""
    if not AWS_ACCESS_KEY or not AWS_SECRET_KEY or not BUCKET_NAME:
        print("❌ S3 Sync Error: Missing AWS credentials in your .env file.")
        print("   Make sure AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and BUCKET_NAME are set.")
        return

    print("🔌 S3 Slideshow Sync Service initialized...")
    s3 = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        region_name=AWS_REGION
    )

    while True:
        try:
            # 1. Fetch current slides from S3
            res = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix="public/slideshow/")
            s3_files = []
            has_changes = False

            if 'Contents' in res:
                for item in res['Contents']:
                    key = item['Key']
                    if key.endswith('/'):
                        continue  # Skip directories
                    
                    filename = os.path.basename(key)
                    s3_files.append(filename)
                    local_path = os.path.join(SLIDES_DIR, filename)

                    # Download file if missing locally
                    if not os.path.exists(local_path):
                        print(f"📥 [Sync] Downloading new slide: {filename}")
                        s3.download_file(BUCKET_NAME, key, local_path)
                        has_changes = True

            # 2. Purge local files that were removed from S3
            for local_file in os.listdir(SLIDES_DIR):
                local_file_path = os.path.join(SLIDES_DIR, local_file)
                if os.path.isfile(local_file_path) and local_file not in s3_files:
                    if local_file.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                        print(f"🗑️ [Sync] Deleting removed slide: {local_file}")
                        os.remove(local_file_path)
                        has_changes = True

            # 3. If downloads/deletions occurred, trigger thread-safe GUI reload
            if has_changes:
                print("🔔 [Sync] Changes detected! Signaling slideshow GUI to refresh immediately...")
                gui_root.event_generate("<<S3_Sync_Updated>>", when="tail")

        except Exception as e:
            print(f"⚠️ [Sync] S3 connection error: {e}")
        
        # Check S3 for updates every 20 seconds
        time.sleep(20)

# ================= TKINTER FULLSCREEN PLAYER =================
class SlideshowPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Mirror Slideshow Player")
        
        # Set up a sleek, deep black fullscreen canvas
        self.root.configure(bg="black")
        self.root.attributes("-fullscreen", True)
        self.root.config(cursor="none") # Hide mouse cursor for mirror presentation

        # Key Bindings
        self.root.bind("<Escape>", self.exit_fullscreen) # Press ESC to exit
        
        # Thread-safe event binding for instant S3 update reaction
        self.root.bind("<<S3_Sync_Updated>>", self.on_sync_updated)

        # Label widget to hold active slide - styled edge-to-edge
        self.label = tk.Label(self.root, bg="black", bd=0, highlightthickness=0)
        self.label.pack(expand=True, fill="both")

        # Slideshow state variables
        self.slides = []
        self.current_index = -1
        self.scheduled_id = None # Tracks the self.root.after timer event

        # Kickoff player loop
        self.update_slides_list()
        self.transition_next_slide()

    def on_sync_updated(self, event=None):
        """Triggered immediately when the S3 sync thread detects a change."""
        print("🔔 [Player] Received S3 update signal! Refreshing active slides...")
        # Immediately transition to reflect changes without waiting for the 8s interval
        self.transition_next_slide(force=True)

    def update_slides_list(self):
        """Scans the local slides directory for valid image files."""
        try:
            valid_exts = ('.png', '.jpg', '.jpeg', '.webp')
            files = [
                os.path.join(SLIDES_DIR, f) 
                for f in os.listdir(SLIDES_DIR) 
                if f.lower().endswith(valid_exts)
            ]
            files.sort() # Keep slides consistent chronologically/alphabetically
            self.slides = files
        except Exception as e:
            print(f"Error scanning local files: {e}")
            self.slides = []

    def transition_next_slide(self, force=False):
        """Displays the next image with high-quality adaptive scaling and instant fallbacks."""
        # Cancel previous timer if a forced/instant transition is triggered
        if force and self.scheduled_id is not None:
            self.root.after_cancel(self.scheduled_id)
            self.scheduled_id = None

        # Always update local file index
        self.update_slides_list()

        if not self.slides:
            # Display premium dark typography placeholder if no slides exist yet
            self.label.config(
                image="", 
                text="📷 ReflectOS Mirror Slideshow\n\nUpload photos from your companion app\nto view them here in real-time!",
                font=("Helvetica", 22, "bold"),
                fg="#555555" # Soft dark gray so it stays ambient behind the glass
            )
            self.current_index = -1
        else:
            image_path = ""
            try:
                # Cycle index safely within active slides boundaries
                self.current_index = (self.current_index + 1) % len(self.slides)
                image_path = self.slides[self.current_index]

                # Get screen dimensions dynamically
                screen_w = self.root.winfo_screenwidth()
                screen_h = self.root.winfo_screenheight()

                # Load and adaptively scale image (maintain perfect aspect ratio)
                img = Image.open(image_path)
                img_w, img_h = img.size
                
                scale = min(screen_w / img_w, screen_h / img_h)
                new_w = int(img_w * scale)
                new_h = int(img_h * scale)

                img_scaled = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                self.photo = ImageTk.PhotoImage(img_scaled)

                # Render edge-to-edge
                self.label.config(image=self.photo, text="")
            except Exception as render_err:
                print(f"⚠️ [Player] Render failed for slide {image_path}: {render_err}")
                # SELF-HEALING: If image was deleted mid-loop or corrupted, skip to next index immediately
                if self.slides:
                    self.transition_next_slide(force=True)
                    return

        # Schedule next standard transition and record scheduled ID
        self.scheduled_id = self.root.after(SLIDESHOW_INTERVAL_MS, self.transition_next_slide)

    def exit_fullscreen(self, event=None):
        """Safely closes the standalone window when Escape key is pressed."""
        print("🔌 Exiting slideshow...")
        self.root.destroy()

# ================= ENTRYPOINT =================
if __name__ == "__main__":
    # 1. Start the main Tkinter Window in the main thread (GUI standard)
    root = tk.Tk()
    app = SlideshowPlayer(root)

    # 2. Spin up AWS S3 sync engine on a background thread, passing GUI root reference
    sync_thread = threading.Thread(target=run_s3_sync_thread, args=(root,), daemon=True)
    sync_thread.start()

    # 3. Enter Tkinter event loop
    root.mainloop()
