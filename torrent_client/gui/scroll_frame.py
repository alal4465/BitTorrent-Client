import tkinter as tk
from tkinter import ttk


class VerticalScrolledFrame(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        """Initialize a scroll bar

        Args:
            parent: the parent window
            *args: variable length argument list
            **kw: arbitrary keyword arguments
        """

        tk.Frame.__init__(self, parent, *args, **kwargs)

        vscrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL)
        vscrollbar.pack(fill=tk.Y, side=tk.RIGHT, expand=tk.FALSE)
        canvas = tk.Canvas(self, bd=0, highlightthickness=0,
                        yscrollcommand=vscrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=tk.TRUE)
        vscrollbar.config(command=canvas.yview)

        canvas.xview_moveto(0)
        canvas.yview_moveto(0)

        self.interior = interior = tk.Frame(canvas)
        interior_id = canvas.create_window(0, 0, window=interior,
                                           anchor=tk.NW)

        label = tk.Label(self.interior, text=" Download Progress ", font=("Helvetica", 16, "underline", "bold"), fg="turquoise4")
        label.pack()

        def _configure_interior(event):
            """Update the scrollbars and canvas to match the size of the inner frame

            Args:
                event: an event object

            Returns:
                None
            """

            size = (interior.winfo_reqwidth(), interior.winfo_reqheight())
            canvas.config(scrollregion="0 0 %s %s" % size)
            if interior.winfo_reqwidth() != canvas.winfo_width():

                canvas.config(width=interior.winfo_reqwidth())
        interior.bind('<Configure>', _configure_interior)

        def _configure_canvas(event):
            """Update the inner frame's width to fill the canvas

            Args:
                event: an event object

            Returns:
                None
            """

            if interior.winfo_reqwidth() != canvas.winfo_width():
                canvas.itemconfigure(interior_id, width=canvas.winfo_width())
        canvas.bind('<Configure>', _configure_canvas)
