from .download_bar import DownloadProgressBar
from .scroll_frame import VerticalScrolledFrame
import tkinter as tk
from tkinter import filedialog
import os

WIDTH = 700
HEIGHT = 500

TITLE = 'Torrent Client'


class App(tk.Tk):
    def __init__(self, *args, **kwargs):
        """Initialize an App instance

        Args:
            *args: variable length argument list
            **kwargs: arbitrary keyword arguments
        """

        tk.Tk.__init__(self, *args, **kwargs)

        self.title(TITLE)
        self.geometry(f"{WIDTH}x{HEIGHT}")
        self.config(background="pale turquoise")

        self.scroll_frame = VerticalScrolledFrame(self)
        self.scroll_frame.grid(column=1, row=3)

        self.place_widgets()

    def place_widgets(self):
        """Place tkinter widgets

        Returns:
            None
        """

        label_title = tk.Label(self,
                               text="Bittorrent Client",
                               width=40,
                               height=3,
                               fg="turquoise4",
                               background="LightBlue2",
                               font=("Helvetica", 22, "bold", "underline"))

        button_explore = tk.Button(self,
                                   text="Browse Files",
                                   command=self.download_file)

        button_exit = tk.Button(self,
                                text="Exit",
                                command=lambda code=0: os._exit(0))

        label_title.grid(column=1, row=1)
        button_explore.grid(column=1, row=4)
        button_exit.grid(column=1, row=5)

    def download_file(self):
        """Browse for *.torrent files, create gui download bar and start downloading the file

        Returns:
            None
        """
        file_path = filedialog.askopenfilename(initialdir="/",
                                               title="Select a File",
                                               filetypes=(("Torrent files", "*.torrent"), ("all files", "*.*")))

        if file_path:
            download_bar = DownloadProgressBar(self.scroll_frame.interior, file_path)
            download_bar.pack()
            download_bar.start()
