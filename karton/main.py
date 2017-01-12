#! /usr/bin/env python
#
# Copyright (C) 2016-2017 Marco Barisione
#
# Released under the terms of the GNU LGPL license version 2.1 or later.

import argparse
import collections

import logging

# For practicality.
from logging import die, info, verbose


class ArgumentParser(argparse.ArgumentParser):
    '''
    ArgumentParser for handling special Karton use cases.
    '''

    def error(self, message):
        if message == 'too few arguments':
            # There seems to be no other way, but we need a decent message when
            # the program is invoked without arguments.
            self.print_help()
            raise SystemExit(1)

        super(ArgumentParser, self).error(message)


class SharedArgument(object):
    '''
    Definition of an argparse argument which can be added to multiple subparsers
    (AKA commands).
    '''

    def __init__(self, *args, **kwargs):
        '''
        Initialise a SharedArgument. The arguments are the same you would pass
        to ArgumentParser.add_argument.
        '''
        self.args = args
        self.kwargs = kwargs

    def add_to_parser(self, target_parser):
        '''
        Add the command to target_parser.
        '''
        target_parser.add_argument(*self.args, **self.kwargs)

    @staticmethod
    def add_group_to_parser(target_parser, shared_arguments):
        '''
        Add all the commands in the shared_arguments iterable to target_parser.
        '''
        for arg in shared_arguments:
            arg.add_to_parser(target_parser)


CommandInfo = collections.namedtuple('CommandInfo', ['name', 'subparser', 'callback'])


def do_run(parsed_args):
    pass


def do_shell(parsed_args):
    pass


def do_start(parsed_args):
    pass


def do_stop(parsed_args):
    pass


def do_status(parsed_args):
    pass


def do_build(parsed_args):
    pass


def run_karton():
    '''
    Runs Karton.
    '''

    parser = ArgumentParser(description='Manages semi-persistent Docker containers.')
    subparsers = parser.add_subparsers(dest='command', metavar='COMMAND')

    all_commands = {}

    def add_command(command_name, callback, *args, **kwargs):
        command_subparser = subparsers.add_parser(command_name, *args, **kwargs)
        all_commands[command_name] = CommandInfo(
            name=command_name,
            subparser=command_subparser,
            callback=callback)
        return command_subparser

    def add_to_every_command(*args, **kwargs):
        for command in all_commands.itervalues():
            command.subparser.add_argument(*args, **kwargs)

    # Definition of arguments common to multiple commands.
    cd_args = (
        SharedArgument(
            '--no-cd',
            dest='cd',
            action='store_const',
            const='no',
            help='don\'t change the current directory in the container'),
        SharedArgument(
            '--auto-cd',
            dest='cd',
            action='store_const',
            const='auto',
            help='chanbge the current directory in the container only if the same is available ' \
                'in both container and host'),
        )

    # "run" command.
    run_parser = add_command(
        'run',
        do_run,
        help='run a  program in the container',
        description='Runs a program or command inside the container (starting it if necessary).')

    run_parser.add_argument(
        'remainder',
        metavar='COMMANDS',
        nargs=argparse.REMAINDER,
        help='commands to execute in the container')

    SharedArgument.add_group_to_parser(run_parser, cd_args)

    # "shell" command.
    shell_parser = add_command(
        'shell',
        do_shell,
        help='start a shell in the container',
        description='Starts an interactive shell inside the container (starting it if necessary)')

    SharedArgument.add_group_to_parser(shell_parser, cd_args)

    # "start" command.
    add_command(
        'start',
        do_start,
        help='if not running, start the container',
        description='Starts the container. If already running does nothing. '
        'Usually you should not need to use this command as both "run" and "shell" start '
        'the container automatically.')

    # "stop" command.
    add_command(
        'stop',
        do_stop,
        help='stop the container if running',
        description='Stops the container. If already not running does nothing.')

    # "status" command.
    add_command(
        'status',
        do_status,
        help='query the status of the container',
        description='Prints information about the status of the container and the list of '
        'programs running in it.')

    # "build" command.
    add_command(
        'build',
        do_build,
        help='build the image for the container',
        description='Builds (or rebuilds) the image for the specified container.')

    # "help" command.
    def do_help(help_parsed_args):
        sub_command_name = help_parsed_args.sub_command
        if sub_command_name is None:
            parser.print_help()
            return

        command = all_commands.get(sub_command_name)
        if command is None:
            die('"%s" is not a Karton command. '
                'Try "karton help" to list the available commands.' % sub_command_name)

        command.subparser.print_help()

    help_parser = add_command(
        'help',
        do_help,
        help='show the help message',
        description='Shows the documentation. If used with no argument, then the general '
        'documentation is shown. Otherwise, when a command is specified as argument, '
        'the documentation for that command is shown.')

    help_parser.add_argument(
        'sub_command',
        metavar='COMMAND',
        nargs='?',
        help='command you want to know more about')

    # Arguments common to everything.
    add_to_every_command(
        '-v',
        '--verbose',
        action='store_true',
        help='enable verbose logging')

    # Now actually parse the command line.
    parsed_args = parser.parse_args()

    logging.set_verbose(parsed_args.verbose)

    command = all_commands.get(parsed_args.command)
    if command is None:
        die('Invalid command "%s". This should not happen.' % parsed_args.command)

    # We don't use argparse's ability to call a callback as we need to do stuff before
    # it's called.
    command.callback(parsed_args)


def main():
    '''
    Runs Karton as a command, i.e. taking care or dealing with keyboard interrupts,
    unexpected exceptions, etc.

    If you need to run Karton as part of another program or from unit tests, use
    run_karton instead.
    '''

    try:
        run_karton()
    except KeyboardInterrupt:
        info('\nInterrupted.')
        raise SystemExit(1)
    except Exception as exc: # pylint: disable=broad-except
        # We print the backtrace only if verbose logging is enabled.
        msg = 'Internal error!\nGot exception: "%s".\n' % exc
        if logging.get_verbose():
            verbose(msg)
            raise
        else:
            die(msg)

    raise SystemExit(0)


if __name__ == '__main__':
    main()
