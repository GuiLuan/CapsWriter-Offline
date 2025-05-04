from multiprocessing import freeze_support
import src.main as core_server

if __name__ == "__main__":
    freeze_support()
    core_server.init()
