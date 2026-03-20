#!/usr/bin/env python
#!/usr/bin/env python
__license__   = 'GPL v3'
__copyright__ = '2011, Thihy <my2003cat@gmail.com>'
# Updated for Python 3 / Calibre 5.0+ in 2026
# Contributor: awdszxc21322 <zsz337845818@gmail.com>
__docformat__ = 'restructuredtext en'

'''
Used for UMD input
Updated for Python 3 / Calibre 5.0+
'''

import os, uuid, re

from calibre.customize.conversion import InputFormatPlugin
from calibre_plugins.umd_input.umdfile import UMDFile
from calibre_plugins.umd_input.plugininfo import PLUGIN_VERSION
from calibre.ptempfile import TemporaryDirectory
from calibre.utils.filenames import ascii_filename

# 模板字符串保持 Unicode
HTML_TEMPLATE = '<html><head><meta http-equiv="Content-Type" content="text/html; charset=utf-8"/><title>%s</title></head><body>\n%s\n</body></html>'

def html_encode(s):
    # Python 3 中字符串默认为 unicode，不再需要 u'' 前缀
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&apos;').replace('\n', '<br/>').replace(' ', '&nbsp;')

class UMDInput(InputFormatPlugin):

    name        = 'UMD Input'
    author      = 'Thihy'
    description = 'Convert UMD files to OEB'
    file_types  = set(['umd'])
    version     = PLUGIN_VERSION
    
    options = set([])
    
    def initialize(self):
        from calibre.ebooks import BOOK_EXTENSIONS
        if 'umd' not in BOOK_EXTENSIONS:
            BOOK_EXTENSIONS.append('umd')

    def convert(self, stream, options, file_ext, log, accelerators):
        from calibre.ebooks.oeb.base import DirContainer
        log.debug("Parsing UMD file...")
        umdFile = UMDFile()
        umdFile.read(stream) 
        
        log.debug("Handle meta data ...")
        from calibre.ebooks.conversion.plumber import create_oebbook
        oeb = create_oebbook(log, None, options,
                encoding=options.input_encoding, populate=False)
        
        if umdFile.Title:
            oeb.metadata.add('title', umdFile.Title)
        if umdFile.Author:
            oeb.metadata.add('creator', umdFile.Author, attrib={'role':'aut'})
        if umdFile.Publisher:
            oeb.metadata.add('publisher', umdFile.Publisher)

        bookid = str(uuid.uuid4())
        oeb.metadata.add('identifier', bookid, id='uuid_id', scheme='uuid')
        
        # 修正 Python 3 迭代器逻辑
        for ident in oeb.metadata.identifier:
            if 'id' in ident.attrib:
                oeb.uid = ident # 直接赋值元素
                break

        with TemporaryDirectory('_umd2oeb', keep=True) as tdir:
            log.debug('Process TOC ...')
            chapters = umdFile.Chapters
            oeb.container = DirContainer(tdir, log)
            
            cover = umdFile.Cover
            if cover:
                # 兼容旧插件中 cover 对象的 format 属性
                img_format = getattr(cover, 'format', 'jpg')
                fname = 'cover.' + img_format
                outputFile = os.path.join(tdir, fname)
                cover.save(outputFile)
                id_img, href_img = oeb.manifest.generate(id='image', href=ascii_filename(fname))
                oeb.guide.add('cover', 'Cover', href_img)
            
            if chapters is not None:
                i = 1
                for ch in chapters:
                    chapterTitle = ch.Title
                    chapterContent = ch.Content
                    if chapterTitle is None or chapterContent is None:
                        continue
                    
                    fname = 'ch_%d.htm' % i
                    # 使用 utf-8 编码写入文件
                    with open(os.path.join(tdir, fname), 'w', encoding='utf-8') as outputFile:
                        lines = []
                        titleWithoutWhiteSpaces = re.sub(r'\s', '', chapterTitle)
                        print(f"TITLE: {chapterTitle} => {titleWithoutWhiteSpaces}")
                        
                        # 处理特殊换行符
                        chapterContent = chapterContent.replace('\u2029', '\n')
                        
                        for line in chapterContent.split('\n'):
                            line = line.rstrip()
                            # 调试输出
                            print(f"ADD {line}")
                            lines.append('<p>%s</p>' % html_encode(line))
                        
                        # 写入格式化后的 HTML
                        outputFile.write(HTML_TEMPLATE % (chapterTitle, '\n'.join(lines)))
                    
                    oeb.toc.add(chapterTitle, fname)
                    id_ch, href_ch = oeb.manifest.generate(id='html', href=ascii_filename(fname))
                    item = oeb.manifest.add(id_ch, href_ch, 'text/html')
                    item.html_input_href = fname
                    oeb.spine.add(item, True)
                    i += 1
        return oeb