try:
    from tkinter import Label, Entry, Button, Tk, LEFT, RIGHT, INSERT, X, Y, BOTH
except ImportError:
    from Tkinter import Label, Entry, Button, Tk, LEFT, RIGHT, INSERT, X, Y, BOTH
root = Tk()
from PIL import Image
# import matplotlib
# matplotlib.use('TkAgg')
import matplotlib.animation as manimation
import matplotlib.pyplot as plt
import os
from fractions import gcd
import utils

FFMpegWriter = manimation.writers['ffmpeg']

class App(object):
    def __init__(self, image_files, delay, rate = 1., dpi = 300, width = None, height = None, aspect = '4X3'):#width = 1920, height = 1080):
        self.writer = FFMpegWriter(fps = 1000. / delay * rate, metadata = {})
        self.dpi = dpi
        if width == height == None:
            if aspect == '4X3':
                width, height = 800, 600
            elif aspect == '16X9':
                width, height = 2560, 1440
            elif aspect == '9X16':
                width, height = 1440, 2560 
            else:
                width, height = (int(l) for l in aspect.split('X', 1))
        _gcd = gcd(width, height)
        self.fig = plt.figure(figsize = (width/_gcd, height/_gcd), frameon = False, dpi = self.dpi)
        self.ax = self.fig.add_axes([0, 0, 1, 1])
        self.ax.set_axis_off()
        self.image_files = image_files
        self.pictures = utils.AlbumReader(*image_files, repeat = False)
        self.size = (width, height)
    def show_slides(self, output_file):
        if output_file is None:
            self.inputbox()
            output_file = self._output_file
        output_file = os.path.expanduser(output_file)
        print 'Output: {}'.format(output_file)
        with self.writer.saving(self.fig, output_file, None):
            for im in self.pictures._iterator:
                if im.tag == 'meta':
                    continue
                print im.get('path')
                im = Image.open(im.get('path'))
                im.thumbnail(self.size)
                im = self.ax.imshow(im)
                self.writer.grab_frame()
                im.remove()
    def inputbox(self):
        text = Label(root)
        text['text'] = 'Output:'
        text.pack(side=LEFT)
        field = Entry(root)
        field.pack(side=LEFT, fill = X, expand = 1)
        execute = Button(root)
        execute['text'] = 'Execute'
        execute.pack(side=RIGHT)
        field.insert(INSERT, os.getcwd()+os.sep)
        def command():
            self._output_file = field.get()
            root.destroy()
        execute['command'] = command
        root.mainloop()
