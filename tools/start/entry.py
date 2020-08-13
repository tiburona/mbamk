import os
import sys
from set_env import set_env_vars
from execution import send_process
from args_and_commands import parse_args, processes, deployments, construct_kwargs


def build_environment(command, args):
    """Set necessary environment variables and arguments that will be passed to downstream functions"""
    os.environ['MBAM_START_ENTRY'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'entry.py')
    kwargs = construct_kwargs(command, args)
    if args.reset or 'FLASK_APP' not in os.environ:
        set_env_vars(**kwargs)


def main():
    ns = parse_args()
    command = sys.argv[1]
    build_environment(command, ns)

    # send_process is the function that will allow a command to be executed.  In the case of the 'test' command, we need
    # the return code so that our test suite can report an error.
    if command == 'test':
        rc = send_process(ns.command)
        if rc:
            raise ValueError("Received non-zero exit code {}".format(rc))
        return rc

    if command == 'run':
        for process in 'flask', 'redis', 'celery':
            if getattr(ns, process):
                # Right now printing to standard out while using Python threads isn't working properly.  So the job of
                # labeling and printing in color is outsourced to NPM, which knows how to do it.
                if ns.npm:
                    output_labels = None
                    thread_wrap = False
                else:
                    output_labels = processes[process]['label']
                    thread_wrap = True

                # This determines whether it will be necessary to change directories to run the process
                d = getattr(ns, process + '_dir') if hasattr(ns, process + '_dir') else '.'

                # The processes dictionary contains the commands that will be run and the label and color to use when
                # printing to standard out
                if process == 'flask':
                    for cmd in processes['flask']['cmd'][ns.env]:
                        send_process(cmd, d, output_labels, thread_wrap=thread_wrap, stream_output=True)
                else:
                    send_process(processes[process]['cmd'], d, output_labels, thread_wrap=thread_wrap,
                                 stream_output=True)

    # Unused right now.  It's the beginning of thinking about how to use this infrastructure for deployment.
    if command == 'deploy':
        if ns.env in ['staging']:
            [send_process(process) for process in deployments[ns.env]['deploy']]


if __name__ == '__main__':
    main()
