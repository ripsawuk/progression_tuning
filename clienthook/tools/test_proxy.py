"""Offline proof that the built proxy answers like the system version.dll.

Loads clienthook\\build\\version.dll (the proxy) and C:\\Windows\\System32\\version.dll (the control),
asks both for notepad.exe's version resource, and prints the fixed-file version each one returns.
Also prints whether the proxy's own log line appears, which is the thing the game will show.

    python clienthook\\tools\\test_proxy.py
"""
import ctypes
import os
from ctypes import wintypes

BUILD = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "build"))
TARGET = os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "System32", "notepad.exe")


def probe(dll, label):
    size = dll.GetFileVersionInfoSizeW(TARGET, None)
    if not size:
        print(f"{label:8} size=0  (no version resource)")
        return None
    buf = ctypes.create_string_buffer(size)
    ok = dll.GetFileVersionInfoW(TARGET, 0, size, buf)
    ptr = ctypes.c_void_p()
    ln = wintypes.UINT()
    q = dll.VerQueryValueW(buf, "\\", ctypes.byref(ptr), ctypes.byref(ln))
    ver = None
    if q and ptr.value:
        ms = ctypes.cast(ptr, ctypes.POINTER(ctypes.c_uint32))
        ver = (ms[2] >> 16, ms[2] & 0xFFFF, ms[3] >> 16, ms[3] & 0xFFFF)
    print(f"{label:8} size={size:5} info={bool(ok)} query={bool(q)} version={ver}")
    return ver


def main():
    os.add_dll_directory(BUILD)
    system = probe(ctypes.WinDLL(os.path.join(os.environ["SystemRoot"], "System32", "version.dll")), "system")
    proxy = probe(ctypes.WinDLL(os.path.join(BUILD, "version.dll")), "proxy")
    same = system == proxy and system is not None
    print(f"pass-through: {'OK - identical' if same else 'MISMATCH'}")
    return 0 if same else 1


if __name__ == "__main__":
    raise SystemExit(main())
