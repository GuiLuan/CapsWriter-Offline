import sys
from multiprocessing import freeze_support

from src.main import start

if __name__ == "__main__":
    if sys.platform == "win32":
        freeze_support()
    start()
