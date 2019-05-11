from PyQt5.QtWidgets import QStackedWidget, QLabel, QStackedLayout, QWidget, QGraphicsOpacityEffect
from PyQt5.QtCore import QTimer, Qt, QUrl, QThread, QFileInfo, pyqtSignal, QPropertyAnimation, QSize, QObject
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtGui import QPixmap, QMovie, QFont

from PIL import Image
import os
import utils
try:
    # Python2
    from Queue import PriorityQueue, Empty
except ImportError:
    # Python3
    from queue import PriorityQueue, Empty

try:
    import vlc
    __VLC__ = True
except ImportError:
    __VLC__ = False

class VLCMediaPlayer(QObject):
    mediaStatusChanged = pyqtSignal(bool)
    def __init__(self, parent = None):
        QObject.__init__(self, parent)
        self._instance = vlc.Instance()
        self._player = self._instance.media_player_new()
        self.parent = parent
        self._timer = QTimer(self)
        self._timer.setInterval(200)
        self._is_playing = False
        self._timer.timeout.connect(self.update_mediaStatusChanged)
    def setVideoOutput(self, video_widget):
        self._player.set_nsobject(video_widget.winId().__int__())
    def setMedia(self, media):
        self.media = self._instance.media_new(media.canonicalUrl().toString())
        self._player.set_media(self.media)
        # self._player.play()
        self._player.pause()
    def __getattr__(self, attr):
        if not hasattr(self, attr):
            print (attr)
        return lambda x: None
    def play(self):
        self._player.play()
        self._timer.start()
        self.EndOfMedia = False
        self._is_playing = True
    def setPlaybackRate(self, v):
        self._player.set_rate(v)
    def update_mediaStatusChanged(self):
        is_playing = self._player.is_playing()
        if is_playing != self._is_playing:
            self.mediaStatusChanged.emit(is_playing)
            self._is_playing = is_playing
            if is_playing == False:
                self.EndOfMedia = True
                # self._player.stop()

class StdInfo(QLabel):
    def __init__(self, text_func, align = Qt.AlignRight | Qt.AlignBottom, parent = None, font = None, **kwds):
        QLabel.__init__(self, parent, **kwds)
        if font == None:
            font = QFont()
            font.setPointSize(36)
        self.setStyleSheet("QLabel {color: gray;}")
        self.setFont(font)
        self.text_func = text_func
        self.align = align
        if callable(text_func):
            self.display = self.display_func 
        else:
            self.setText(self.text_func)
            self.display = self.display_str
        effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(effect)
        self.anim = QPropertyAnimation(effect, b"opacity")
        self.anim.setDuration(2000)
        self.anim.setStartValue(1.)
        self.anim.setEndValue(0.)
        # self.anim.setEasingCurve(QEasingCurve.OutQuad)
        self.anim.finished.connect(self.hide)
        self.parent().resized.connect(self.set_position)
    def set_position(self, pos = None):
        if pos == None:
            coords = self.parent().geometry().getCoords()
            if self.align & Qt.AlignLeft:
                x = coords[0]
            else:
                x = coords[2] - self.width()
            if self.align & Qt.AlignTop:
                y = coords[1]
            else:
                y = coords[3] - self.height()
            pos = (x, y)
        self.move(*pos)
    def display_func(self):
        self.setText(self.text_func())
        self.show()
        self.anim.stop()
        self.anim.start()
    def display_str(self):
        self.show()
        # self.anim.updateCurrentValue(1.)
        self.anim.stop()
        self.anim.start()

class ResizeWidget(QWidget):
    resized = pyqtSignal()
    def resizeEvent(self, event):
        self.resized.emit()
        return super(ResizeWidget, self).resizeEvent(event)

class ReadMediaThread(QThread):
    def __init__(self, fname, queue, priority, size = QSize(800, 600), parent = None):
        QThread.__init__(self, parent = parent)
        self.fname = fname
        self.queue = queue
        self.priority = priority
        self.size = size
        # self.parent = parent
    def __del__(self):
        self.wait()
    def run(self):
        ext = os.path.splitext(self.fname)[1]
        if ext in (".mp4", ".wmv", '.mpg'):
            media = QMediaContent(QUrl.fromLocalFile(QFileInfo(self.fname).absoluteFilePath()))
        elif ext in ('.jpg', '.png'):
            media = QPixmap(self.fname).scaled(self.size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        elif ext in ('.gif', ):
            _media = Image.open(self.fname)
            media = QMovie(self.fname)#, parent = self.parent())
            media.setScaledSize(QSize(*_media.size))
            media.setCacheMode(QMovie.CacheAll)
            # media.setSpeed(100)
        # QCoreApplication.processEvents()
        self.queue.put((self.priority, media))        

class App(ResizeWidget):
    _changed_playseed = pyqtSignal()
    def __init__(self, image_files, delay, rate = 1.0, qsize = 100, parent = None):
        QStackedWidget.__init__(self, parent)
        self.status = True
        self.delay = delay
        self.rate = rate
        self.image_files = image_files
        self.pictures = utils.AlbumReader(*image_files)
        self.maxqsize = qsize
        self.timer = QTimer(self)
        self.timer.setInterval(self.delay)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.show_slides)
        self._timeout = self.delay / 10
        self._result = PriorityQueue(self.maxqsize)
        self._next = 0
        self._queued = 0
        self._gif_replay_times = [0, 3]
        self.layout = QStackedLayout(self)
        # slideshow
        self.SlideShowWidget = QLabel(self)
        self.SlideShowWidget.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.info_fps = StdInfo(lambda: "fps: {:.1f}".format(1000. / self.delay * self.rate),
                                align = Qt.AlignRight | Qt.AlignBottom,
                                parent = self)
        self._changed_playseed.connect(self.info_fps.display)
        self.info_playspeed = StdInfo(lambda: "x {:.0%}".format(self.rate),
                                align = Qt.AlignRight | Qt.AlignTop,
                                parent = self)
        self._changed_playseed.connect(self.info_playspeed.display)
        self._changed_playseed.emit()
        # video
        self.MediaPlayer = VLCMediaPlayer(self) if __VLC__ else QMediaPlayer(self)
        self.VideoWidget = QVideoWidget(self)
        self.MediaPlayer.setVideoOutput(self.VideoWidget)
        self.MediaPlayer.setPlaybackRate(self.rate)
        self.MediaPlayer.mediaStatusChanged.connect(self.end_of_media)
        self.layout.addWidget(self.SlideShowWidget)
        self.layout.addWidget(self.VideoWidget)
        self.threading(int(self.maxqsize/10))

        self.show()

    def threading(self, n = 1):
        i = 0
        while i < n:
            try:
                media = next(self.pictures)
            except StopIteration:
                self._queued = -1
                return 1
            if media.tag == 'meta':
                exec('self.' + media.get('command'))
                continue

            thread = ReadMediaThread(media.get('path'), self._result, self._queued, self.size(), parent = self)
            self._queued += 1
            thread.start()
            i += 1

    def show_slides(self):
        try:
            i, img_object = self._result.get(True, 5)
            if isinstance(img_object, QMediaContent):
                self.MediaPlayer.setMedia(img_object)
        except Empty:
            self.timer.stop()
            return
        while i != self._next:
            self._result.put((i, img_object), False)
            i, img_object = self._result.get()
            if isinstance(img_object, QMediaContent):
                self.MediaPlayer.setMedia(img_object)
        if isinstance(img_object, QMediaContent):
            # If a movie
            # self.MediaPlayer.setMedia(img_object)
            self.layout.setCurrentWidget(self.VideoWidget)
            self.MediaPlayer.play()
        elif isinstance(img_object, QMovie):
            # If a gif
            size = img_object.scaledSize()
            img_object = QMovie(img_object.fileName())
            img_object.setCacheMode(QMovie.CacheAll)
            self._gif = img_object
            img_object.frameChanged.connect(self.gif_frame_changed)
            self.SlideShowWidget.setMovie(img_object)
            size.scale(self.SlideShowWidget.size(), Qt.KeepAspectRatio)
            img_object.setScaledSize(size)
            img_object.setSpeed(int(self.rate*100))
            self.layout.setCurrentWidget(self.SlideShowWidget)
            # self.change_playspeed(self.rate)
            img_object.start()
        else:
            # If a picture
            # print(img_object.size())
            self.SlideShowWidget.setPixmap(img_object.scaled(self.SlideShowWidget.size(), Qt.KeepAspectRatio))
            self.timer.start(self.delay / self.rate)
            self.layout.setCurrentWidget(self.SlideShowWidget)
        self._next += 1
        self.threading(self.maxqsize - self._result.qsize())

    def keyPressEvent(self, e):
        key = e.key()
        if key == Qt.Key_Escape: # Esc: Exit
            self.close()
            return
        if key == Qt.Key_Space: # Space: stop/start
            self.status = not self.status
            if self.status:
                if self.rate > 0:
                    self.timer.start()
            else:
                self.timer.stop()
            return
        if key == Qt.Key_S:
            import Mp4Movie
            app = Mp4Movie.App(self.image_files, self.delay, rate = self.rate, aspect = '4X3')
            app.show_slides(None)
            # self.close()
            return
        if key == 93: # ]: -10%
            self.change_playspeed(self.rate + 0.1)
            return
        if key == 91: # [: +10%
            self.change_playspeed(self.rate - 0.1)
            return
        if e.modifiers() == Qt.ControlModifier: # Ctrl + Enter: Toggle Full Screen
            if key == Qt.Key_Return:
                self.toggle()

    def toggle(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def end_of_media(self, status):
        if status == self.MediaPlayer.EndOfMedia:
            self.timer.start(0)

    def change_playspeed(self, speed):
        if speed < 0:
            speed = 0
        self.rate = speed
        if self.rate == 0:
            self.timer.stop()
        elif self.status and not self.timer.isActive() and not hasattr(self, '_gif'):
            self.timer.start()
        if hasattr(self, '_gif'):
            self._gif.setSpeed(int(speed*100))
        self.MediaPlayer.setPlaybackRate(self.rate)
        self._changed_playseed.emit()

    def gif_frame_changed(self, frame):
        if (frame + 1) == self._gif.frameCount():
            self._gif_replay_times[0] += 1
            if self._gif_replay_times[0] == self._gif_replay_times[1]:
                self._gif.stop()
                self.timer.start(0)
                self._gif_replay_times[0] = 0
                del self._gif