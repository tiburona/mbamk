import os
import sys
from set_env import set_env_vars
from execution import send_process
from args_and_commands import parse_args, processes, deployments, construct_kwargs

def build_environment(command, args):
    os.environ['MBAM_START_ENTRY'] = os.path.join(os.path.dirname(os.path.abspath( __file__ )), 'entry.py')
    kwargs = construct_kwargs(command, args)
    try:
        os.environ['FLASK_APP']
        if args.reset:
            set_env_vars(**kwargs)

    except KeyError:
        set_env_vars(**kwargs)


def main():
    ns = parse_args()
    command = sys.argv[1]
    build_environment(command, ns)

    if command == 'test':
        send_process(ns.command)

    if command == 'run':
        for process in 'flask', 'redis', 'celery':
            if getattr(ns, process):
                if ns.npm:
                    output_labels = None
                    thread_wrap = False
                else:
                    output_labels = processes[process]['label']
                    thread_wrap = True

                d = getattr(ns, process + '_dir') if hasattr(ns, process + '_dir') else '.'

                if process == 'flask':
                    for cmd in processes['flask']['cmd'][ns.env]:
                        send_process(cmd, d, output_labels, thread_wrap=thread_wrap, stream_output=True)
                else:
                    send_process(processes[process]['cmd'], d, output_labels, thread_wrap=thread_wrap,
                                 stream_output=True)

    if command == 'deploy':
        if ns.env in ['staging']:
            [send_process(process) for process in deployments[ns.env]['deploy']]

if __name__ == '__main__':
    main()


















