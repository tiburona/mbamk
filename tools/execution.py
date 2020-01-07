import shlex
import subprocess
import threading
from colorama import init, Fore

init(autoreset=True)


def execute(cmd, stream_output=False, output_labels=None):
    if stream_output:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
        while True:
            line = proc.stdout.readline().rstrip().decode('utf-8')
            if not line:
                break
            if output_labels:
                label, color = output_labels
                line = getattr(Fore, color) + '{}'.format(label) + Fore.RESET + ' ' + line
    else:
        command = shlex.split(cmd)
        subprocess.run(command, check=True)


def thread(func):
    def wrapper(*args, **kwargs):
        x = threading.Thread(target=func, args=args, kwargs=kwargs)
        x.start()
    return wrapper


def send_process(command, directory, output_labels=None, thread_wrap=False, stream_output=False):
    if directory != '.':
        command = 'cd {}; '.format(directory) + command

    if thread_wrap:

        @thread
        def start_threaded_process():
            execute(command, stream_output=True, output_labels=output_labels)

        start_threaded_process()

    else:
        execute(command, stream_output=stream_output)