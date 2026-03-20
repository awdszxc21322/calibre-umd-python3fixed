#!/usr/bin/env python
# -*- coding: utf-8 -*-
#########################################################################
# Author: Xinyu.Xiang, Thihy
# Updated for Python 3 / Calibre 5.0+ in 2026
# Contributor: awdszxc21322 <zsz337845818@gmail.com>
#########################################################################
import os
import datetime
import struct
import io  # Python 3 使用 io 替代 cStringIO
from PIL import Image
import zlib
import traceback
import random

class Chapter(object):
    def _getTitle(self):
        return self.title
    def _setTitle(self, value):
        self.title = value
    Title = property(_getTitle, _setTitle, None, 'title of the chapter')

    def _getContent(self):
        return self.content
    def _setContent(self, value):
        self.content = value
    Content = property(_getContent, _setContent, None, 'content of the chapter')

    def __init__(self, title, content):
        self.title = title
        self.content = content

class UMDFile(object):

    def __init__(self):
        self.additionalCheck = 0
        self.author = ''
        self.chapOff = []
        self.chapters = []
        self.cid = 0
        self.contentLength = 0
        self.cover = None
        self.cover_data = None
        self.day = '1'
        self.encoding = 'utf-16-le'
        self.gender = ''
        self.month = '1'
        self.pgkSeed = 0
        self.publishDate = datetime.datetime.now()
        self.publisher = ''
        self.title = ''
        self.type = None
        self.vendor = ''
        self.year = '2000'
        self.zippedSeg = []
        self.arrJpeg = [] 
        self.metaOnly = False

    def _getTitle(self): return self.title
    def _setTitle(self, v): self.title = v
    Title = property(_getTitle, _setTitle)

    def _getChapters(self): return self.chapters
    def _setChapters(self, v): self.chapters = v
    Chapters = property(_getChapters, _setChapters)

    def _getPublisher(self): return self.publisher
    def _setPublisher(self, v): self.publisher = v
    Publisher = property(_getPublisher, _setPublisher)

    def _getCover(self): return self.cover
    def _setCover(self, v): self.cover = v
    Cover = property(_getCover, _setCover)

    def _getCoverData(self):
        if self.cover_data is not None:
            return self.cover_data
        if self.cover is None:
            return None
        try:
            sio = io.BytesIO()
            self.cover.convert('RGB').save(sio, 'JPEG')
            self.cover_data = sio.getvalue()
            return self.cover_data
        except:
            print("cannot read cover data")
            traceback.print_exc()
            return None
    CoverData = property(_getCoverData)

    def _getAuthor(self): return self.author
    def _setAuthor(self, v): self.author = v
    Author = property(_getAuthor, _setAuthor)

    def read(self, ufile, metaOnly=False):
        self.metaOnly = metaOnly
        self.chapters = []
        self.arrJpeg = []
        
        header = self._readuint32(ufile)
        if header != 0xde9a9b89:
            raise UMDException('wrong header')
        
        ch1 = self._peekchar(ufile)
        while ch1 == b'#':
            ufile.read(1)
            num2 = self._readint16(ufile)
            num3 = self._readbyte(ufile)
            num4 = self._readbyte(ufile) - 5
            self._readSection(num2, num3, num4, ufile)
            ch1 = self._peekchar(ufile)
            if num2 == 0xf1 or num2 == 10:
                num2 = 0x84
            while ch1 == b'$':
                ufile.read(1)
                num5 = self._readuint32(ufile)
                num6 = self._readuint32(ufile) - 9
                self._readadditional(num2, num5, num6, ufile)
                ch1 = self._peekchar(ufile)

        if self.type == '2':
            raise UMDException("Don't support comic umd")
        
        try:
            self.publishDate = datetime.datetime(int(self.year), int(self.month), int(self.day))
        except:
            self.publishDate = datetime.datetime.now()

        if not self.metaOnly:
            extlist = []
            for zitm in self.zippedSeg:
                extlist.append(zlib.decompress(zitm))
            # Python 3 中 join bytes 需要用 b''
            totalcontent = b''.join(extlist)
            for i in range(len(self.chapOff)):
                stt = self.chapOff[i]
                ed = self.chapOff[i+1] if i < len(self.chapOff)-1 else len(totalcontent)
                self.chapters[i].content = totalcontent[stt:ed].decode(self.encoding, 'ignore')
            self.zippedSeg = []

    def _readadditional(self, id, check, length, ufile):
        if not self.metaOnly:
            if id == 0x0e:
                self.arrJpeg.append(self._readimg(ufile, length))
                return
            if id == 0x81:
                ufile.read(length)
                return
            if id == 0x83:
                count = length // 4
                self.chapOff = [0] * count
                for i in range(count):
                    self.chapOff[i] = self._readint32(ufile)
                return
            if id == 0x84:
                if self.additionalCheck != check:
                    self.zippedSeg.append(ufile.read(length))
                    return
                buffer1 = ufile.read(length)
                num2 = 0
                while num2 < len(buffer1):
                    num3 = buffer1[num2]
                    num2 += 1
                    title_bytes = buffer1[num2:num2+num3]
                    self.chapters.append(Chapter(title_bytes.decode(self.encoding, 'ignore'), ""))
                    num2 += num3
                return
        if id == 0x82:
            self.cover = self._readimg(ufile, length)
            return 
        ufile.seek(length, os.SEEK_CUR)

    def _readimg(self, ufile, length):
        try:
            return Image.open(io.BytesIO(ufile.read(length)))
        except:
            print("cannot read image")
            traceback.print_exc()
            return None

    def _readbyte(self, ufile):
        data = ufile.read(1)
        return data[0] if data else 0

    def _peekchar(self, ufile):
        c = ufile.read(1)
        if c: ufile.seek(-1, 1)
        return c

    def _readint32(self, ufile):
        return struct.unpack('<i', ufile.read(4))[0]

    def _readuint32(self, ufile):
        return struct.unpack('<I', ufile.read(4))[0]

    def _readint16(self, ufile):
        return struct.unpack('<h', ufile.read(2))[0]

    def _readstr2uni(self, ufile, length):
        return ufile.read(length).decode(self.encoding, 'ignore')

    def _readSection(self, id, b, length, ufile):
        if id == 1:
            self.type = str(self._readbyte(ufile))
            self.pgkSeed = self._readint16(ufile)
        elif id == 2: self.title = self._readstr2uni(ufile, length)
        elif id == 3: self.author = self._readstr2uni(ufile, length)
        elif id == 4: self.year = self._readstr2uni(ufile, length)
        elif id == 5: self.month = self._readstr2uni(ufile, length)
        elif id == 6: self.day = self._readstr2uni(ufile, length)
        elif id == 8: self.publisher = self._readstr2uni(ufile, length)
        elif id == 9: self.vendor = self._readstr2uni(ufile, length)
        elif id == 10: self.cid = self._readint32(ufile)
        elif id == 11: self.contentLength = self._readint32(ufile)
        elif id in (0x81, 0x83, 0x84, 130):
            if id == 130: ufile.read(1)
            self.additionalCheck = self._readuint32(ufile)
        else:
            ufile.read(length)

class UMDException(Exception):
    pass