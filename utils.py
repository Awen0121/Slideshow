from __future__ import division, print_function
import os
from PIL import Image
import codecs
from sys import version_info
from xml.etree import cElementTree as ET
from itertools import cycle, chain


def rescaled(image, size, result, i = 0, fmt = None):
    if not image:
        try:
            result.put((0, None))
        except AssertionError:
            pass
        return
    image_object = Image.open(image)
    width, height = image_object.width, image_object.height
    winfo_width, winfo_height = size
    ratio = min(winfo_width/width, winfo_height/height)
    try:
        image_object = image_object.resize((int(width*ratio), int(height*ratio)), 1)
        if fmt != None:
            image_object = fmt(image_object)
    except ValueError:
        pass
    try:
        result.put((i, image_object))
    except AssertionError:
        pass

def _read_image(*args):
    for arg in args:
        if os.path.splitext(arg)[1] in (".png", ".jpg", ".mp4", ".wmv", ".gif", '.mpg'):
            yield arg
            continue
        elif os.path.splitext(arg)[1] == ".album":
            directory = os.path.dirname(arg)
            if version_info.major < 3:
                directory = directory.decode('utf-8')
            for item in _album_reader_xml(arg, directory):
                yield item
            continue
        elif os.path.isdir(arg):
            for root, subdirs, files in os.walk(arg):
                files.sort()
                subdirs.sort()
                index = os.path.join(root, "pictures.album")
                if os.path.exists(index):
                    for f in _read_image(index):
                        yield f
                    break
                for f in _read_image(*(os.path.join(root, f) for f in files)):
                    yield f

def read_image(*args):
    return cycle(_read_image(*args))

def _album_reader_text(arg, directory):
    with codecs.open(arg, encoding = "utf-8") as index:
        for l in index.readlines():
            l = l.strip()
            if l:
                if not l.startswith('#'):
                    for img in _read_image(os.path.join(directory, l)):
                        yield img

class AlbumReader(object):
    def __init__(self, *iterable, **kwds):
        self._iterator = self._generator(iterable, **kwds)

    @staticmethod
    def _read_image(arg, ret_fname = False):
        if ret_fname:
            return arg
        return ET.Element('item', path = arg)

    @staticmethod
    def _read_dir(arg, skip_albumfile = False, ret_fname = False):
        for root, subdirs, files in os.walk(arg):
            index = os.path.join(root, "pictures.album")
            if os.path.exists(index) and not skip_albumfile:
                for f in AlbumReader._read_xml(index):
                    yield f
                return
            else:
                files.sort()
                subdirs.sort()
                for d in subdirs:
                    for item in AlbumReader._read_dir(d, skip_albumfile = skip_albumfile, ret_fname = ret_fname):
                        yield item
                for f in (os.path.join(root, f) for f in files):
                    if os.path.splitext(f)[1] in (".png", ".jpg", ".mp4", ".wmv", ".gif", '.mpg'):
                        yield AlbumReader._read_image(f, ret_fname = ret_fname)

    @staticmethod
    def _read_xml(arg, repeat = False):
        directory = os.path.dirname(arg)
        if version_info.major < 3:
            directory = directory.decode('utf-8')
        t = ET.parse(arg)
        album = t.getroot()
        head = album.find('head')
        body = album.find('body')
        for part in chain((head,), cycle((body,)) if repeat else (body,)):
            for item in part:
                if item.tag == 'meta':
                    yield item
                elif item.tag == 'chapter':
                    id = item.get('id')
                    chapter = album.find('./chapter[@id="{}"]'.format(id)) if id else item
                    for meta in chapter.iterfind('meta'):
                        yield meta
                    for l in AlbumReader._read_text(chapter.text, directory):
                        yield l

    @staticmethod
    def _read_text(arg, directory):
        for l in arg.splitlines():
            l = l.strip()
            if l:
                if not l.startswith('#'):
                    l = os.path.join(directory, l)
                    if os.path.isdir(l):
                        for f in AlbumReader._read_dir(l):
                            yield f
                    else:
                        yield AlbumReader._read_image(l)
    @staticmethod
    def _generator(iterable, repeat = True):
        for arg in iterable:
            if os.path.splitext(arg)[1] in (".png", ".jpg", ".mp4", ".wmv", ".gif", '.mpg'):
                yield AlbumReader._read_image(arg)
            elif os.path.splitext(arg)[1] == ".album":
                for item in AlbumReader._read_xml(arg, repeat = repeat):
                    # print 'read album:', item
                    yield item
            elif os.path.isdir(arg):
                for item in AlbumReader._read_dir(arg):
                    # print 'read directory:', item.attrib
                    yield item

    def next(self):
        return next(self._iterator)
    def __next__(self):
        return self.next()
    @staticmethod
    def make_template(path):
        t = """<album>
<head>
<meta command="showFullScreen()"/>
<meta command="change_playspeed(5.)"/>
</head>
<body>
<chapter>
{}
</chapter>
</body>
</album>"""
        albumf = os.path.join(path, 'pictures.album')
        if os.path.exists(albumf):
            raise OSError('Album file already exists.')
        with open(albumf, 'w') as f:
            f.write(t.format('\n'.join(os.path.relpath(f) for f in AlbumReader._read_dir(path, True, True))))
