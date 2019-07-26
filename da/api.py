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

import os
import sys
import time
import stat
import pickle
import logging
import collections.abc
import os.path

from sys import stderr
from . import common, sim, endpoint
from .common import api, deprecated, get_runtime_option, ProcessId

DISTPY_SUFFIXES = [".da", ""]
PYTHON_SUFFIX = ".py"
NODECLS = "Node_"
BASE_MODULE_NAME = 'da.lib.base'
DEFAULT_MASTER_PORT = 15000
ASYNC_TIMEOUT = 5
PORT_RANGE = 10

CONSOLE_LOG_FORMAT = \
    '[%(relativeCreated)d] %(name)s%(daPid)s:%(levelname)s: %(message)s'
FILE_LOG_FORMAT = \
    '[%(asctime)s] %(name)s%(daPid)s:%(levelname)s: %(message)s'
HEADER_REGEXP = "# -\\*- generated by ([0-9a-z.-]*) -\\*-"

log = logging.getLogger(__name__)

def find_file_on_paths(filename, paths):
    """Looks for a given 'filename' under a list of directories, in order.

    If found, returns a pair (path, mode), where 'path' is the full path to
    the file, and 'mode' is the result of calling 'os.stat' on the file.
    Otherwise, returns (None, None).

    """
    for path in paths:
        fullpath = os.path.join(path, filename)
        try:
            filemode = os.stat(fullpath)
            return fullpath, filemode
        except OSError:
            pass
    return None, None

def strip_suffix(filename):
    """Returns a filename minus it's extension."""

    dotidx = filename.rfind(".")
    return filename[:dotidx] if dotidx != -1 else filename

@api
def init(**configs):
    """Initializes the DistAlgo runtime.

    """
    common.initialize_runtime_options(configs)

@api
def import_da(name, from_dir=None, compiler_args=[]):
    """Imports DistAlgo module 'module', returns the module object.

    This function mimics the Python builtin __import__() function for DistAlgo
    modules. 'name' is the name of the module to be imported, in
    "dotted module name" format. The module must be implemented in one regular
    DistAlgo source file with a '.da' filename suffix; package modules are not
    supported.

    This function returns the imported module object upon successful import;
    otherwise, 'ImportError' is raised.

    Optional argument 'compiler_args' is a list of command line arguments to
    pass to the compiler, if a compiler invocation is needed. Optional
    argument 'from_dir' should be a valid module search path that overrides
    'sys.path'.

    """
    import re
    import importlib
    import da.compiler as compiler

    force_recompile = get_runtime_option('recompile', default=False)
    paths = sys.path if from_dir is None else [from_dir]
    pathname = name.replace(".", os.sep)
    for suffix in DISTPY_SUFFIXES:
        fullpath, mode = find_file_on_paths(pathname + suffix, paths)
        if fullpath is not None:
            break
    if fullpath is None:
        raise ImportError("Module %s not found." % name)
    pyname = strip_suffix(fullpath) + PYTHON_SUFFIX
    try:
        pymode = os.stat(pyname)
        with open(pyname, "r") as fd:
            header = fd.readline(80)
        res = re.match(HEADER_REGEXP, header)
        if res is None or (res.group(1) != common.__version__):
            force_recompile = True
    except OSError:
        pymode = None

    if (force_recompile or pymode is None or
            pymode[stat.ST_MTIME] < mode[stat.ST_MTIME]):
        oldargv = sys.argv
        try:
            argv = oldargv[0:0] + compiler_args + [fullpath]
            res = compiler.ui.main(argv)
        except Exception as err:
            raise RuntimeError("Compiler failure!", err)
        finally:
            sys.argv = oldargv

        if res != 0:
            raise ImportError("Unable to compile %s, errno: %d" %
                              (fullpath, res))

    moduleobj = importlib.import_module(name)
    common.setup_logging_for_module(name, CONSOLE_LOG_FORMAT, FILE_LOG_FORMAT)
    return moduleobj

def _load_cookie():
    authkey = get_runtime_option('cookie')
    if authkey is None:
        try:
            fname = os.path.expanduser("~/.da.cookie")
            with open(fname, "r") as fd:
                authkey = fd.read(80).encode()
        except OSError:
            pass
    return authkey

def _parse_address(straddr):
    assert isinstance(straddr, str)
    components = straddr.split(':')
    if len(components) > 2:
        raise ValueError("Invalid address: {}".format(straddr))
    elif len(components) == 0:
        return "", None
    elif len(components) == 1:
        return components[0], None
    else:
        try:
            return components[0], int(components[1])
        except ValueError as e:
            raise ValueError("Invalid port number: {}".format(components[1]))

def _bootstrap_node(cls, nodename, trman):
    router = None
    is_master = get_runtime_option('master')
    hostname = get_runtime_option('hostname')
    port = get_runtime_option('port')
    if port is None:
        port = get_runtime_option('default_master_port')
        strict = False
        if is_master:
            try:
                trman.initialize(hostname=hostname, port=port, strict=True)
            except endpoint.TransportException as e:
                log.debug("Binding attempt to port %d failed: %r", port, e)
                trman.close()
    else:
        strict = True
    if not trman.initialized:
        trman.initialize(hostname=hostname, port=port,
                         strict=strict, linear=is_master)
    nid = ProcessId._create(pcls=cls,
                            transports=trman.transport_addresses,
                            name=nodename)
    common._set_node(nid)
    if not is_master:
        rhost, rport = _parse_address(get_runtime_option('peer'))
        if len(rhost) == 0:
            rhost = hostname
        if rport is None:
            rport = get_runtime_option('default_master_port')
        trman.start()
        router = sim.Router(trman)
        try:
            router.bootstrap_node(rhost, rport, timeout=ASYNC_TIMEOUT)
        except sim.BootstrapException as e:
            log.info("Bootstrapping attempt failed due to %r, "
                     " continuing as a master node (use '--master' to "
                     "disable bootstrapping at startup).", e)
        router.start()
    return router

def _load_main_module():
    target = get_runtime_option('file')
    compiler_args = get_runtime_option('compiler_flags').split()
    if target is not None:
        source_dir = os.path.dirname(target)
        basename = strip_suffix(os.path.basename(target))
        if not os.access(target, os.R_OK):
            die("Can not access source file %s" % target)
        sys.path.insert(0, source_dir)
        module = import_da(basename,
                           from_dir=source_dir,
                           compiler_args=compiler_args)
        sys.argv = [target] + get_runtime_option('args')
    elif get_runtime_option('module') is not None:
        module_args = get_runtime_option('module')
        module_name = module_args[0]
        module = import_da(module_name, compiler_args=compiler_args)
        sys.argv = ['__main__'] + module_args[1:]
    else:
        module = import_da(BASE_MODULE_NAME)
    return module

def _check_nodename():
    nodename = get_runtime_option('nodename')
    if not common.check_name(nodename):
        die("'--nodename' must not contain any of the characters in {}".
            format(common.ILLEGAL_NAME_CHARS))
    return nodename

def entrypoint():
    """Entry point for running DistAlgo as the main module.

    """
    import socket
    import multiprocessing

    startmeth = get_runtime_option('start_method')
    if startmeth != multiprocessing.get_start_method(allow_none=True):
        multiprocessing.set_start_method(startmeth)
    try:
        module = _load_main_module()
    except ImportError as e:
        die("ImportError: " + str(e))
    if not hasattr(module, 'Node_'):
        if get_runtime_option('idle'):
            # Just use the generic node:
            module.Node_ = sim.NodeProcess
        else:
            die("Main process not defined!")
    elif not (type(module.Node_) is type and
              issubclass(module.Node_, sim.DistProcess)):
        die("Main process is not a DistProcess: {}".format(module.Node_))

    common.set_runtime_option('this_module_name', module.__name__)
    common.set_runtime_option('main_module_name', module.__name__)
    if get_runtime_option('inc_module_name') is None:
        common.set_runtime_option('inc_module_name', module.__name__ + "_inc")
    hostname = socket.gethostbyname(common.get_runtime_option('hostname'))
    common.set_runtime_option('hostname', hostname)
    common.sysinit()
    common.setup_logging_for_module("da")

    # Start main program
    nodename = _check_nodename()
    niters = get_runtime_option('iterations')
    traces = get_runtime_option('replay_traces')
    router = None
    trman = None
    if len(nodename) == 0:
        # Safety precaution: disallow distributed messaging when no node name
        # specified (i.e. run an isolated node), by setting the cookie to a
        # random value:
        cookie = multiprocessing.current_process().authkey
    else:
        cookie = _load_cookie()
    try:
        trman = endpoint.TransportManager(cookie)
        if len(nodename) > 0 and not traces:
            router = _bootstrap_node(module.Node_, nodename, trman)
            nid = common.pid_of_node()
        else:
            trman.initialize()
            nid = ProcessId._create(pcls=module.Node_,
                                    transports=trman.transport_addresses,
                                    name=nodename)
            common._set_node(nid)
    except (endpoint.TransportException, sim.RoutingException) as e:
        log.error("Transport initialization failed due to: %r", e)
        stderr.write("System failed to start. \n")
        return 5

    log.info("%s initialized at %s:(%s).", nid,
             get_runtime_option('hostname'), trman.transport_addresses_str)

    if not traces:
        nodeimpl = None
        try:
            log.info("Starting program %s...", module)
            for i in range(niters):
                log.info("Running iteration %d ...", (i+1))

                nodeimpl = sim.OSThreadContainer(process_class=module.Node_,
                                                 transport_manager=trman,
                                                 process_id=nid,
                                                 parent_id=nid,
                                                 process_name=nodename,
                                                 router=router)
                nodeimpl.start()
                log.info("Waiting for remaining child processes to terminate..."
                         "(Press \"Ctrl-C\" to force kill)")
                nodeimpl.join()
                nodeimpl = None
                log.info("Main process terminated.")

        except KeyboardInterrupt as e:
            log.warning("Received keyboard interrupt. ")
            if nodeimpl is not None:
                stderr.write("Terminating node...")
                nodeimpl.end()
                t = 0
                while nodeimpl.is_alive() and t < ASYNC_TIMEOUT:
                    stderr.write(".")
                    t += 1
                    nodeimpl.join(timeout=1)
            if nodeimpl is not None and nodeimpl.is_alive():
                stderr.write("\nNode did not terminate gracefully, "
                             "some zombie child processes may be present.\n")
                return 2
            else:
                stderr.write("\nNode terminated. Goodbye!\n")
                return 1
        except Exception as e:
            log.error("Caught unexpected global exception: %r", e, exc_info=1)
            return 4

    else:
        try:
            pobjs = []
            proctype = get_runtime_option('default_proc_impl')
            if proctype == 'thread':
                router = sim.Router(trman)
                router.start()
            log.info(
                "Replaying trace file(s) on program %s using %r containers...",
                module, proctype)
            implcls = getattr(sim, 'OS{}Container'.format(proctype.capitalize()))
            common.set_global_config(module.Node_._config_object)
            for i in range(niters):
                log.info("Running iteration %d...", (i+1))
                pobjs = [implcls(process_class=sim.DistProcess,
                                 transport_manager=trman,
                                 router=router,
                                 replay_file=tf)
                         for tf in traces]
                for p in pobjs:
                    p.start()
                log.info("Waiting for replay processes to terminate..."
                         "(Press \"Ctrl-C\" to force kill)")
                while pobjs:
                    p = pobjs[-1]
                    p.join()
                    pobjs.pop()
                log.info("All replay completed.")

        except KeyboardInterrupt as e:
            stderr.write("\nReceived keyboard interrupt. ")
            stderr.write("\nTerminating processes...")
            for p in pobjs:
                p.end()
            t = 0
            for p in pobjs:
                while p.is_alive() and t < ASYNC_TIMEOUT:
                    stderr.write(".")
                    t += 1
                    p.join(timeout=1)
            if any(p.is_alive() for p in pobjs):
                stderr.write("\nSome child processes may have been zombied.\n")
                return 2
            else:
                stderr.write("\nAll child processes terminated. Goodbye!\n")
                return 1
        except sim.TraceException as e:
            log.error("Could not replay trace due to: %r", e)
            return 9
        except Exception as e:
            log.error("Caught unexpected global exception: %r", e, exc_info=1)
            return 4

    return 0

def dump_trace(filename):
    with open(filename, 'rb') as stream:
        print('Dumping {}:'.format(filename))
        header = stream.read(4)
        if header != sim.TRACE_HEADER:
            die('{} is not a DistAlgo trace file!')
        version = stream.read(4)
        print("\n  Generated by DistAlgo version ", end='')
        if version[-1] == 0:
            print("{}.{}.{}".format(*version[:-1]))
        else:
            print("{}.{}.{}-{}".format(*version))
        tracetyp = stream.read(1)[0]
        if tracetyp == sim.TRACE_TYPE_RECV:
            print("  Receive trace ")
            dump_item = dump_recv_item
        elif tracetyp == sim.TRACE_TYPE_SEND:
            print("  Send trace ")
            dump_item = dump_send_item
        else:
            stderr.write("Error: unknown trace type {}\n".format(tracetyp))
            return
        pid = pickle.load(stream)
        parent = pickle.load(stream)
        print("  Running process: {}\tParent process: {}\n".format(pid, parent))
        while True:
            try:
                dump_item(stream)
            except EOFError:
                break
            except Exception as e:
                stderr.write("Error: trace file corrupted: {}\n".format(e))
                return
        print("END OF TRACE")

def dump_recv_item(stream):
    delay, item = pickle.load(stream)
    if isinstance(item, common.QueueEmpty):
        print("-- {!r} ".format(item), end='')
    else:
        print(" {1} <= {0} ".format(*item), end='')
    if delay:
        print("@+{:.3f}s".format(delay))
    else:
        print('')

RESULT_STR = { True:'Succeeded', False:'Failed'}
def dump_send_item(stream):
    event, value = pickle.load(stream)
    if event == sim.Command.Message:
        print(" ({}) => ".format(RESULT_STR[value]))
    elif event == sim.Command.New:
        print(" +> {} ".format(value))
    else:
        print(" ({}) <? Unknown event type {}".format(value, event))

def die(mesg = None):
    if mesg != None:
        stderr.write(mesg + "\n")
    sys.exit(1)
