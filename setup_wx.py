import sys

from cx_Freeze import setup, Executable

from csviewer_wx import AppConfig


base = None
if sys.platform == 'win32':
    base = 'Win32GUI'

# includes = ['json']


# 'unicodedata', 'linecache', 'contextlib', 'tokenize', 'datetime'

# Нужно!
# 'abc', 'codecs', 'functools', 'enum', 're', 'heapq', 'stat', 'reprlib, 'locale', 'base64'
excludes = ['tkinter', 'logging', 'unittest', 'email', 'html', 'http', 'urllib',
            'xml', 'pydoc', 'doctest', 'argparse', 'zipfile',
            'subprocess', 'pickle', 'threading', 'calendar',
            'gettext', 'bz2', 'fnmatch', 'getopt', 'string',
            'stringprep', 'quopri', 'copy', 'imp',
            'configparser', 'weakref', 'typing', ]

zip_include_packages = ['collections', 'encodings', 'importlib', 'wx']

options = {
    'build_exe': {
        'include_msvcr': True,
        'excludes': excludes,
        # 'includes': includes,
        'zip_exclude_packages': [],
        # 'zip_include_packages': ["*"],
        'zip_include_packages': zip_include_packages,
        'build_exe': 'build_csviewer_win_x64',
    }
}

executables = [
    Executable(
        'main.py',
        targetName='CSViewer.exe',
        base=base,
        icon=r'data/images/app/csviewer_ico.ico',
        copyright='Matvienko Alexey (ma1ex) Copyright © 2020',
        trademarks='MARKiS ™',
    )
]

setup(name='CSViewer',
      version=AppConfig.APP_VERSION,
      description=AppConfig.APP_DESCRIPTION,
      options=options,
      executables=executables,
      )
