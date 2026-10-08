# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller specification file for packaging Flash Automator into a standalone executable."""

import sys
import os

block_cipher = None

# Platform-aware hidden imports
hidden_imports = [
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    'pynput',
    'pynput.keyboard',
    'pynput.mouse',
    'pyautogui',
    'pytweening',
    'pyscreeze',
    'cv2',
    'PIL',
    'PIL.ImageGrab',
    'pytesseract',
    'sqlite3',
]

if sys.platform.startswith('win'):
    hidden_imports.extend(['pynput.keyboard._win32', 'pynput.mouse._win32'])
elif sys.platform.startswith('linux'):
    hidden_imports.extend(['pynput.keyboard._xorg', 'pynput.mouse._xorg', 'pynput.keyboard._uinput', 'pynput.mouse._evdev'])

a = Analysis(
    ['app.py'],
    pathex=['.', '..'],
    binaries=[],
    datas=[],
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'scipy', 'PyQt5', 'PyQt6', 'PySide2'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

# Standalone executable
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='FlashAutomator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
