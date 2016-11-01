# Copyright (c) 2010-2016 Bo Lin
# Copyright (c) 2010-2016 Yanhong Annie Liu
# Copyright (c) 2010-2016 Stony Brook University
# Copyright (c) 2010-2016 The Research Foundation of SUNY
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import sys
import logging
import argparse

__version__ = "1.0.0rc1"

from da.common import initialize_runtime_options
from da.api import entrypoint

if hasattr(sys, '_real_argv'):
    sys.argv[0] = sys._real_argv

def parseConfig(item):
    try:
        key, value = item.split('=')
        return key, value
    except ValueError:
        die("Invalid configuration format: %s" % item)

def parseArgs():
    LogLevelNames = [n.lower() for n in logging._nameToLevel]

    parser = argparse.ArgumentParser(fromfile_prefix_chars='@')

    parser.add_argument('--iterations', type=int, default=1,
                        help="number of times to run the program, defaults to 1.")
    parser.add_argument("--no-log",
                        action="store_true", default=False,
                        help="if set, don't customize the root logger. "
                        "Useful if DistAlgo is run as a library .")
    parser.add_argument("-f", "--logfile", action="store_true", default=False,
                        help="creates a log file for this run.")
    parser.add_argument("--logfilename",
                        help="file name of the log file, defaults to appending"
                        "'.log' to the source file name.")
    parser.add_argument("--logdir")
    parser.add_argument("-L", "--logconsolelevel",
                        choices=LogLevelNames, default="info",
                        help="severity level of logging messages to print to "
                        "the console, defaults to 'info'.")
    parser.add_argument("-F", "--logfilelevel",
                        choices=LogLevelNames, default="debug",
                        help="severity level of logging messages to log to "
                        "the log file, defaults to 'debug'.")
    parser.add_argument("--pid-format",
                        choices=['short', 'long', 'full'], default='short',
                        help="sets the format of string representation of "
                        "process ids. 'short' prints the process class name "
                        "followed by the uid truncated to the last 5 hexdigits. "
                        "This is the default. 'long' prints the process class "
                        "name followed by the full 24 hexdigit untruncated uid. "
                        "'full' prints the full string representation of the "
                        "process id object. For named processes, both the "
                        "'short' and 'long' forms print the process name "
                        "in place of the uid.")
    parser.add_argument("-i", "--load-inc-module",
                        action="store_true", default=False,
                        help="if set, try to load the incrementalized "
                        "interface module.")
    parser.add_argument("-C", "--control-module-name", default=None,
                        help="name of the control module. If set, "
                        "results from the inc-module will be compared "
                        "against results from this module. Any mismatch will "
                        "raise IntrumentationError. Defaults to no control "
                        "module.")
    parser.add_argument("-m", "--inc-module-name",
                        help="name of the incrementalized interface module, "
                        "defaults to source module name + '_inc'. ")
    parser.add_argument("-H", "--hostname", default='localhost',
                        help="hostname for binding network sockets, "
                        "defaults to 'localhost'. ")
    parser.add_argument("-N", "--nodename", default="",
                        help="hostname for binding network sockets, "
                        "defaults to 'localhost'. ")
    parser.add_argument("--cookie", default=None,
                        help="a string for authentication of peers. "
                        "All peer processes participating in message passing "
                        "must have matching cookies. "
                        "Defaults to the content of '${HOME}/.da.cookie'. ")
    parser.add_argument('--message-buffer-size', type=int, default=(4 * 1024),
                        help="Size in bytes of send and receive buffers used by "
                        "transports. Default value is 4096.")
    parser.add_argument("-r", "--recompile", dest="recompile",
                        help="force recompile DistAlgo source file. ",
                        action="store_true", default=False)
    parser.add_argument("-c", "--compiler-flags", default="",
                        help="flags to pass to the compiler, if (re)compiling "
                        "is required.")
    parser.add_argument("-o", "--config", default=[], nargs='*',
                        help="sets runtime configuration variables, overrides "
                        "configurations declared in the program source.")
    parser.add_argument("--start-method", default=None, choices=['fork', 'spawn'],
                        help="choose the semantics for creating child process."
                        " 'fork' is the default method on UNIX-like systems,"
                        " 'spawn' is the default method on Windows systems.")
    parser.add_argument("-I", "--default-proc-impl", default='process',
                        choices=['process', 'thread'],
                        help="choose the default implementation for running "
                        " DistAlgo processes."
                        " 'process' uses OS processes,"
                        " 'thread' uses OS threads.")
    parser.add_argument("-v", "--version", action="version", version=__version__)
    parser.add_argument("file",
                        help="DistAlgo source file to run.")
    parser.add_argument("args", nargs=argparse.REMAINDER,
                        help="arguments passed to program in sys.argv[1:].")

    args = parser.parse_args()
    args.config = dict(parseConfig(item) for item in args.config)
    return args

def libmain():
    """Main program entry point.

    Parses command line options, sets up global variables, and calls the 'main'
    function of the DistAlgo program.

    """
    args = parseArgs()
    initialize_runtime_options(args.__dict__)
    entrypoint()

def die(mesg = None):
    if mesg != None:
        sys.stderr.write(mesg + "\n")
    sys.exit(1)

if __name__ == '__main__':
    libmain()
