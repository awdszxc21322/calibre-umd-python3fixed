#!/usr/bin/env  python
__license__   = 'GPL v3'
__copyright__ = '2011, Thihy <my2003cat@gmail.com>'
# Updated for Python 3 compatibility in 2026
# Contributor: awdszxc21322 <zsz337845818@gmail.com>
__docformat__ = 'restructuredtext en'

import re, time, os, sys

def debug_print(text):
    from calibre.constants import DEBUG
    if DEBUG:
        time_string = time.strftime('%Y/%m/%d %H:%M:%S  ', time.gmtime())
        text = re.sub('<P>|[\n\r]','\n' + time_string , text)
        print time_string + text