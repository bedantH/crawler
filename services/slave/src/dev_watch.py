import subprocess
import sys
from watchfiles import watch
import os

WATCH_PATH = os.path.dirname(__file__)

def run_target():
    return subprocess.Popen([sys.executable, '-u', '-m', 'slave.main'])

def main():
    proc = run_target()
    try:
        for changes in watch(WATCH_PATH):
            proc.terminate()
            proc.wait()
            proc = run_target()
    except KeyboardInterrupt:
        proc.terminate()

if __name__ == '__main__':
    main()
