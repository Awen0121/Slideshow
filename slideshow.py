#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK
# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
import os
import argparse
import sys
try:
    from pathlib import Path
except ImportError:
    from pathlib2 import Path
    reload(sys)
    sys.setdefaultencoding('utf-8')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = "Python Slideshow", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-d", "--delay", type = int, default = 1000, help = 'Delay time in milisecond. For example 1000 mean 1 fps')
    parser.add_argument("-r", "--rate", type = float, default = 5., help = 'Playback speed')
    parser.add_argument("-s", "--qsize", type = int, default = 100, help = 'Queue size')
    parser.add_argument("-b", "--backend", choices = ["qt", "tk", "mp4", "qt+vlc", 'template'], default = "qt+vlc", help = 'GUI backend')
    parser.add_argument("-o", "--output", default = None, help = 'Output file name. <BACKEND> will be set to mp4 if not None.')
    parser.add_argument("f", nargs = "+", type = str, help = 'Input file name.')
    parser.add_argument("-a", "--aspect", default = '4X3', help = "Aspect ratio. Only affect when outputing mp4")#, choices = ['16X9', '4X3', '9X16'])
    parser.add_argument('--dpi', type = int, default = 300, help = 'DPI. Only affect when outputing mp4')
    try:
        import argcomplete
        argcomplete.autocomplete(parser)
    except ImportError:
        pass
    try:
        import sys
        from IPython.core.ultratb import AutoFormattedTB
        sys.excepthook = AutoFormattedTB()
    except ImportError:
        print ('IPython is not installed. Colored Traceback will not be populated.')
    args = parser.parse_args()

# upper left corner coordinates of app window
    if args.output is not None:
        args.backend = 'mp4'
    if args.backend in ("qt", "qt+vlc"):
        import GUIPyQt
        GUIPyQt.__VLC__ = 'vlc' in args.backend
        from PyQt5.QtWidgets import QApplication
        a = QApplication([])
        app = GUIPyQt.App(args.f, args.delay, rate = args.rate, qsize = args.qsize)
        app.setGeometry(20, 20, 1024, 768)
        app.show_slides()
        a.exec_()
    elif args.backend == "tk":
        from GUITk import App
        app = App(args.fs, args.delay)
        app.show_slides()
        app.mainloop()
    elif args.backend == 'mp4':
        from Mp4Movie import App
        assert len(args.f) == 1
        output = Path(args.output).resolve()
        if output.is_dir():
            output = output / (output.name + '.mp4')#os.path.join(args.output, os.path.splitext(os.path.basename(args.f[0]))[0]) + '.mp4'
        print (output)
        app = App(args.f, args.delay, rate = args.rate, aspect = args.aspect, dpi = args.dpi)
        app.show_slides(str(output).format(IN = output))
    elif args.backend == 'template':
        from utils import AlbumReader
        assert len(args.f) == 1
        d = args.f[0]
        assert os.path.isdir(d)
        AlbumReader.make_template(d)
