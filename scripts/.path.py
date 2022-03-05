import os
import sys
import platform
from pathlib import Path
from subprocess import run, PIPE
    
mark = "#PATH#"
system = platform.system()
extension = ".bat" if system == "Windows" else ".sh"
folder = "win" if system == "Windows" else "posix"
target_file = 'chess'+extension
execution_path = Path(__file__).resolve().parent
shell_fpath = execution_path/folder/target_file
main_path = execution_path.parent

def do(action=None):
    with open(shell_fpath, 'r') as file:
        content = file.read()
    with open(shell_fpath, 'w') as file:
        if action == '--replace':
            file.write(content.replace(mark, str(main_path)))
        elif action == '--reset':
            file.write(content.replace(str(main_path), mark))

if __name__ == "__main__":
    args = sys.argv; args.pop(0)
    if len(args) > 0:
        action = args[0]
        if '--replace' == action:
            do(action=action)
        elif '--reset' == action:
            do(action=action)
            
