try:
    # Python2
    import Tkinter as tk
    from Queue import PriorityQueue
except ImportError:
    # Python3
    import tkinter as tk
    from queue import PriorityQueue
from PIL import ImageTk
from itertools import cycle, chain
from threading import Thread
from utils import rescaled

class App(tk.Tk):
    '''Tk window/label adjusts to size of image'''
    def __init__(self, image_files, delay):
        # the root will be self
        tk.Tk.__init__(self)
        # set x, y position only
        self.geometry("{}x{}".format(self.winfo_screenwidth(), self.winfo_screenheight()))
        self.state("normal")
        self.status = True
        self.delay = delay
        # allows repeat cycling through the pictures
        # store as (img_object, img_name) tuple

        self.pictures = chain([None], cycle(image_files))
        self._size = [self.winfo_screenwidth(), self.winfo_screenheight()]
        self.maxqsize = 10
        self._result = PriorityQueue(self.maxqsize)
        self._next = 0
        self._queued = 0
        self.threading(self.maxqsize)
        # self.pictures = cycle((tk.PhotoImage(file=image), image)
        #                       for image in image_files)
        self.picture_display = tk.Label(self)
        self.picture_display.pack()
        self.bind("<Control-Return>", self.toggle_fullscreen)
        self.bind("<space>", self.toggle_pause)
        self.bind("<Escape>", self.toggle_quit)
    def threading(self, n = 1):
        for _ in range(n):
            thread = Thread(target = rescaled,
                            args = (next(self.pictures), self._size, self._result, self._queued))
            self._queued += 1
            thread.start()
            # thread.join()
    def show_slides(self):
        self.set_size()
        if not self.status:
            self.after(self.delay, self.show_slides)
            return 
        '''cycle through the images and show them'''
        # next works with Python26 or higher
        i, img_object = self._result.get()
        while i != self._next:
            self._result.put((i, img_object), False)
            i, img_object = self._result.get()
        if img_object != None:
            del self.picture_display.image
            img_object = ImageTk.PhotoImage(image = img_object)
        self.picture_display.configure(image=img_object)
        self.picture_display.image = img_object
        # shows the image filename, but could be expanded
        # to show an associated description of the image
        self._next += 1
        self.threading()
        self.after(self.delay, self.show_slides)
    def set_size(self):
        self._size[:] = self.winfo_width(), self.winfo_height()
    def run(self):
        self.mainloop()

    def toggle_fullscreen(self, event=None):
        self.state = not self.state  # Just toggling the boolean
        self.attributes("-fullscreen", self.state)
        return "break"

    def toggle_pause(self, event=None):
        self.status = not self.status
        return "break"

    def toggle_quit(self, event=None):
        self._result.task_done()
        self.destroy()