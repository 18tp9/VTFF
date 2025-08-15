import numpy as np
import matplotlib.pyplot as pl
from PIL import Image
from scipy.ndimage import median_filter
import os
import tkinter as tk
from tkinter import simpledialog, filedialog, ttk

class BGDialog(simpledialog.Dialog):
    def __init__(self, parent, imgPath, filenames, title=None):
        self.imgPath = imgPath
        self.filenames = filenames
        self.bg = None
        self.mf = None
        super().__init__(parent, title)
        self.result = None

    def body(self, master):
        self.bgPath = tk.Button(master, text="Select Background Image", command=self.select_bg)
        self.MaxFilter = tk.Button(master, text="Use Maximum Filter", command=self.use_max_filter)
        self.bgPath.grid(row=0, column=1)
        self.MaxFilter.grid(row=4, column=1)

    def buttonbox(self):
        pass

    def select_file(self):
        file_path = filedialog.askopenfilename(title="Select Background Image", filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.bmp;*.tiff")])
        return file_path

    def select_bg(self):
        self.bg = self.select_file()
        self.destroy()

    def use_max_filter(self):
        maxVal = np.maximum.reduce([np.asarray(Image.open(os.path.join(self.imgPath, name)).convert('L')) for name in self.filenames])
        self.mf = maxVal
        self.destroy()

class CutoffDialog(simpledialog.Dialog):
    def body(self, master):
        tk.Label(master, text="Lower cutoff value:").grid(row=0)
        tk.Label(master, text="Upper cutoff value:").grid(row=1)
        self.lower_cutoff = tk.Entry(master)
        self.upper_cutoff = tk.Entry(master)
        self.lower_cutoff.grid(row=0, column=1)
        self.upper_cutoff.grid(row=1, column=1)
        return self.lower_cutoff

    def apply(self):
        try:
            self.result = (int(self.lower_cutoff.get()), int(self.upper_cutoff.get()))
        except ValueError:
            tk.messagebox.showerror("Invalid input", "Please enter valid integer values for cutoff.")
            self.result = None

def select_folder():
    folder_path = filedialog.askdirectory(title="Select Image Folder")
    return folder_path

def backgroundSubtract(path, bg):
    im = Image.open(path).convert('L')
    im = np.asarray(im)
    im1 = bg - im
    return im, im1




# --- Intro/Splash Window ---
intro_window = tk.Tk()
intro_window.title("Welcome")
intro_window.geometry("400x250")
intro_window.configure(bg="#3bafe6")

# Title
title_label = tk.Label(intro_window, text="VTFF", font=("Helvetica", 18, "bold"), bg="#9dd1e9")
title_label.pack(pady=20)

# Message
message_label = tk.Label(
    intro_window,
    text="Welcome to the visual tracer filter finder!\nClick 'Start' to continue.",
    font=("Helvetica", 12),
    bg="#e6cda1"
)
message_label.pack(pady=10)

# Start Button
start_button = ttk.Button(intro_window, text="Start", command=intro_window.destroy)
start_button.pack(pady=20)

# Run splash
intro_window.mainloop()


root = tk.Tk()
root.withdraw()

imgPath = select_folder()
filenames = os.listdir(imgPath)

Pdialog = BGDialog(root, imgPath, filenames, "Background Subtraction Options")
backgroundPath = Pdialog.bg

if backgroundPath is None:
    background = Pdialog.mf
else:
    background = Image.open(backgroundPath).convert('L')
    background = np.asarray(background)

pl.ion()
index = 0
im1 = None

def update_image(index, minC=0, maxC=255, window=17, contour=True, median=False, loading=False, cutoff=False):
    global im, im1

    if loading:
        path = os.path.join(imgPath, filenames[index])
        im, im1 = backgroundSubtract(path, background)

    ax.clear()
    ax.imshow((im), interpolation='nearest', alpha=1, cmap='gray')
    ax.set_title(f"Image # {index} Pixel Range: {minC} - {maxC}")

    if median:
        ax.set_title('LOADING MEDIAN FILTER...')
        fig.canvas.flush_events()
        # ax.invert_xaxis()
        ax.set_xticks([])
        ax.set_yticks([])
        pl.pause(0.001)
        # ax.invert_xaxis()
        im1 = median_filter(im1, window)
        ax.set_title(f"Image # {index} Pixel Range: {minC} - {maxC}, Median Filter: n = {window}")

    if cutoff:
        im1 = np.where((im1 > maxC) | (im1 < minC), 0, im1)

    im1Max = np.max(im1)

    if contour:
        ax.contourf(im1 / im1Max, np.linspace(0.01, 1, 10), cmap='Reds', extend='neither')

    # ax.invert_xaxis()
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlabel("Right/Left: Change Photo   C: Change Pixel Thresholds    M: Test Median Filter  Spacebar: Toggle Contours")

    pl.tight_layout()
    fig.canvas.draw_idle()

contour = True
minC = 0
maxC = 255
medianWindow = 17
medBool = False

def cutoff_keys(event):
    global index, contour, maxC, minC, medianWindow, medBool
    update_needed = False

    if event.key == 'left' and index > 0:
        index -= 1
        loading = True
        update_needed = True
    elif event.key == 'right' and index < len(filenames) - 1:
        index += 1
        loading = True
        update_needed = True
    elif event.key == 'c':
        Cdialog = CutoffDialog(root, "Input Cutoff Values")
        minC, maxC = Cdialog.result
        loading = False
        update_needed = True
    elif event.key == 'm':
        medBool = True
        loading = False
        # if medBool:
        medianWindow = simpledialog.askstring("Input", "Enter median window size (pixels):")
        if medianWindow in [str(0),None,''] :
            medBool=False
            loading=True
        else:
            medianWindow = int(medianWindow)
        update_needed = True
    elif event.key == ' ':
        contour = not contour
        medBool = False
        loading = False
        update_needed = True
    if update_needed:
        ax.clear()
        update_image(index, minC, maxC, medianWindow, median=medBool, contour=contour, loading=loading, cutoff=True)

fig, ax = pl.subplots(figsize=([8, 6]))
update_image(index, loading=True)

fig.canvas.mpl_connect('key_press_event', cutoff_keys)

pl.show(block=True)