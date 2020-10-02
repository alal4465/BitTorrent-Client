import tkinter as tk
from tkinter import ttk
import threading
import asyncio
from tracker.tracker import Tracker


class DownloadProgressBar:
    def __init__(self, parent, file_path):
        """Initialize a download progress bar

        Args:
            parent: parent widget to place the bar on
            file_path: file path to the *.torrent file to be downloaded
        """

        self._title = tk.Label(parent, text=file_path.split('/')[-1], font=("Verdana", 10), fg="turquoise3")

        self._progress_bar = ttk.Progressbar(parent, orient=tk.HORIZONTAL, mode='determinate')
        self._file_path = file_path
        self._job = threading.Thread(target=self._download_job)
        self._packed = False

    def start(self):
        """Start the download thread

        Returns:
            None
        """

        self._job.start()

    def join(self):
        """Join the download thread

        Returns:
            None
        """

        self._job.join()

    def pack(self, *args, **kwargs):
        """Pack bar to the parent window

        Returns:
            None
        """

        if not self._job.is_alive():
            self._packed = True

            self._title.pack()
            self._progress_bar.pack(*args, **kwargs)

    def _download_job(self):
        """The downloaded job to be run in a separate thread. Runs the download async event loop

        Returns:
            None
        """

        loop = asyncio.new_event_loop()

        loop.run_until_complete(self._async_download())

        loop.close()
        if self._packed:
            self._progress_bar.pack_forget()
            self._title.pack_forget()

    async def _async_download(self):
        """Preform an asynchronous download of the .torrent file

        Returns:
            None
        """

        tracker = Tracker.from_path(self._file_path, self._progress_bar)
        await tracker.download()
        print(f"[+] downloaded {tracker.torrent_name}")
