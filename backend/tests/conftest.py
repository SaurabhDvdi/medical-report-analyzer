import sys
import os

# Ensure Windows DLL search path includes directories containing msvcp140.dll
if sys.platform == "win32" and hasattr(os, "add_dll_directory"):
    for p in sys.path:
        for candidate in ["sklearn/.libs", "numpy.libs", "pandas.libs"]:
            target = os.path.join(p, *candidate.split("/"))
            if os.path.isdir(target):
                try:
                    os.add_dll_directory(target)
                except Exception:
                    pass
