import os
import tkinter as tk
from tkinter import ttk, messagebox
import yt_dlp
import threading

# إنشاء مجلدات التحميل
download_folder = "Downloaded"
video_folder = os.path.join(download_folder, "Video")
audio_folder = os.path.join(download_folder, "Audio")
os.makedirs(video_folder, exist_ok=True)
os.makedirs(audio_folder, exist_ok=True)

# تخزين الجودات
video_map = {}
audio_map = {}

def get_formats():
    url = url_entry.get().strip()
    if not url:
        messagebox.showerror("Error", "Please enter a valid YouTube URL.")
        return

    # إعادة ضبط القوائم قبل تحميل الجودات الجديدة
    video_dropdown['values'] = []
    audio_dropdown['values'] = []
    video_dropdown.set("")
    audio_dropdown.set("")

    progress_var.set(10)
    progress_bar.start()

    def fetch_formats():
        global video_map, audio_map
        ydl_opts = {'quiet': True}
        video_map = {}
        audio_map = {}
        video_qualities_dict = {}

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                formats = info.get('formats', [])

                for f in formats:
                    height = f.get('height')
                    ext = f.get('ext')
                    abr = f.get('abr')
                    filesize = f.get('filesize')

                    if height and ext == 'mp4' and height in [144, 240, 360, 480, 720, 1080, 1440, 2160]:
                        size_mb = round(filesize / (1024 * 1024), 2) if filesize else "Unknown"
                        quality_label = f"{height}p ({size_mb}MB)"

                        if height not in video_qualities_dict or (video_qualities_dict[height][1] == "Unknown" and size_mb != "Unknown"):
                            video_qualities_dict[height] = (f['format_id'], size_mb)

                    if abr:
                        audio_map[abr] = f['format_id']

                video_qualities = [f"{q}p ({size}MB)" for q, (fmt_id, size) in sorted(video_qualities_dict.items())]
                video_map = {quality: video_qualities_dict[int(quality.split('p')[0])][0] for quality in video_qualities}

                sorted_audio = sorted(audio_map.keys(), reverse=True)
                audio_labels = ["High", "Medium", "Low"]
                audio_map = {audio_labels[i]: audio_map[sorted_audio[i]] for i in range(min(3, len(sorted_audio)))}

                video_dropdown['values'] = list(video_map.keys())
                audio_dropdown['values'] = list(audio_map.keys())

                update_quality_selection()

                messagebox.showinfo("Success", "Available qualities loaded successfully!")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load qualities:\n{e}")

        progress_bar.stop()
        progress_var.set(100)

    threading.Thread(target=fetch_formats, daemon=True).start()

def paste_link():
    url_entry.config(state="normal")
    url_entry.delete(0, tk.END)
    url_entry.insert(0, root.clipboard_get())
    url_entry.config(state="readonly")

def update_quality_selection():
    if mode_var.get() == "Video":
        video_dropdown.config(state="readonly")
        audio_dropdown.config(state="disabled")
    else:
        video_dropdown.config(state="disabled")
        audio_dropdown.config(state="readonly")

def download():
    url = url_entry.get().strip()
    if not url:
        messagebox.showerror("Error", "Please enter a valid YouTube URL.")
        return

    selected_mode = mode_var.get()
    selected_quality = video_dropdown.get() if selected_mode == "Video" else audio_dropdown.get()

    if not selected_mode or not selected_quality:
        messagebox.showerror("Error", "Please select a mode and quality before downloading.")
        return

    download_folder_path = video_folder if selected_mode == "Video" else audio_folder
    os.makedirs(download_folder_path, exist_ok=True)

    # إعادة ضبط شريط التقدم
    progress_var.set(0)
    progress_text.set("Initializing download...")
    progress_bar.start()

    def start_download():
        try:
            download_opts = {
                'quiet': True,
                'progress_hooks': [progress_hook],
                'outtmpl': os.path.join(download_folder_path, '%(title)s.%(ext)s')
            }

            if selected_mode == "Video":
                download_opts['format'] = f"{video_map[selected_quality]}+bestaudio"
            else:
                download_opts['format'] = audio_map[selected_quality]

            with yt_dlp.YoutubeDL(download_opts) as ydl:
                ydl.download([url])

            messagebox.showinfo("Success", "Download completed!")

        except Exception as e:
            messagebox.showerror("Error", f"Download failed:\n{e}")

        progress_bar.stop()
        progress_var.set(100)

    threading.Thread(target=start_download, daemon=True).start()

def progress_hook(d):
    if d['status'] == 'downloading':
        downloaded = d.get('downloaded_bytes', 0) / (1024 * 1024)
        total = d.get('total_bytes', 1) / (1024 * 1024)
        speed = d.get('speed', 0) / (1024 * 1024)
        eta = d.get('eta', 0)

        progress_text.set(f"Speed: {speed:.2f} MB/s | {downloaded:.2f}MB / {total:.2f}MB | ETA: {eta}s")
        progress_var.set(int((downloaded / total) * 100) if total else 0)

root = tk.Tk()
root.title("YouTube Downloader")
root.geometry("900x600")

main_frame = tk.Frame(root)
main_frame.pack(expand=True)

progress_var = tk.IntVar()

tk.Label(main_frame, text="Enter YouTube URL:", font=("Arial", 14)).pack(pady=5)

paste_frame = tk.Frame(main_frame)
paste_frame.pack(pady=5)

url_entry = tk.Entry(paste_frame, width=50, font=("Arial", 12), state="readonly")
url_entry.pack(side="left", padx=5)

paste_button = tk.Button(paste_frame, text="PASTE", font=("Arial", 10), command=paste_link, bg="red", fg="white")
paste_button.pack(side="left")

tk.Button(main_frame, text="Get Qualities", font=("Arial", 12), command=get_formats, bg="red", fg="white").pack(pady=10)

mode_var = tk.StringVar(value="Video")
mode_frame = tk.Frame(main_frame)
mode_frame.pack(pady=5)

tk.Radiobutton(mode_frame, text="Video", variable=mode_var, value="Video", font=("Arial", 12), command=update_quality_selection).pack(side="left", padx=20)
tk.Radiobutton(mode_frame, text="Audio", variable=mode_var, value="Audio", font=("Arial", 12), command=update_quality_selection).pack(side="left", padx=20)

tk.Label(main_frame, text="Video Qualities", font=("Arial", 12, "bold")).pack(pady=5)
video_dropdown = ttk.Combobox(main_frame, state="disabled", font=("Arial", 12))
video_dropdown.pack(pady=5)

tk.Label(main_frame, text="Audio Qualities", font=("Arial", 12, "bold")).pack(pady=5)
audio_dropdown = ttk.Combobox(main_frame, state="disabled", font=("Arial", 12))
audio_dropdown.pack(pady=5)

progress_bar = ttk.Progressbar(main_frame, length=300, mode="determinate", variable=progress_var)
progress_bar.pack(pady=10)

progress_text = tk.StringVar()
progress_label = tk.Label(main_frame, textvariable=progress_text, font=("Arial", 12))
progress_label.pack(pady=5)

tk.Button(main_frame, text="Download", font=("Arial", 12), command=download, bg="red", fg="white").pack(pady=10)

update_quality_selection()
root.mainloop()
