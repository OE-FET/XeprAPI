# uncompyle6 version 3.4.1
# Python bytecode 2.7 (62211)
# Decompiled from: Python 3.7.4 (default, Sep  7 2019, 18:27:02)
# [Clang 10.0.1 (clang-1001.0.46.4)]
# Embedded file name: /home/thob/Develop/xeprdev/xeprgit/linux/../StdEnvironment/sharedProDeL/Standard/XeprAPI.py
# Compiled at: 2014-10-08 15:31:14
"""
*Xepr API* module for Python, providing access to **Xepr** via *libxeprapi.so*
"""
_msgprefix = 'Xepr API: '

import types, sys
assert not sys.version_info[0] != 2 or not sys.version_info[1] in [5, 6, 7], '%sNeed Python V2.5.x, V2.6.x or V2.7.x to use XeprAPI' % _msgprefix
import os, tempfile, re, ctypes
from ctypes import byref
from sys import stderr
from pipes import quote
from exceptions import Exception
try:
    import numpy as NP
    _tmp = [ int(x) for x in NP.__version__.strip().split('.') ]
    assert not _tmp[0] < 1 or (_tmp[0] == 1 and _tmp[1] < 2)
    assert not _tmp[0] == 1 and (_tmp[1] == 2 and len(_tmp) == 3 and _tmp[2] < 1)
except:
    raise ImportError('%sNeed recent (>= V1.2.1) Numpy package for Python' % _msgprefix)

try:
    import multiprocessing as MP
except:
    import Queue

try:
    import Tkinter as tk
except:
    pass

try:
    ctypes.c_bool
except:
    ctypes.c_bool = ctypes.c_byte


PRODELDOCSUBDIR = 'Examples'
SUCCESS = 0


class pointer(ctypes.c_int32):

    def __init__(self, val=None):
        if val == None:
            ctypes.c_int32.__init__(self)
        elif type(val) == pointer:
            val = val.value
        else:
            ctypes.c_int32.__init__(self, val)

        return


class char(ctypes.c_char):

    def __init__(self, val=None):
        if val == None:
            ctypes.c_char.__init__(self)
        elif type(val) == char:
            val = val.value
        else:
            ctypes.c_char.__init__(self, val)

        return


def _loadapilib(libxeprapi=None):
    libname = 'libxeprapi_32.so' if ctypes.sizeof(ctypes.c_void_p) * 8 == 32 else 'libxeprapi.so'
    if not libxeprapi:
        try:
            libxeprapi = os.path.dirname(os.path.realpath(__file__))
        except:
            libxeprapi = '.'

    libxeprapi += libname if libxeprapi.endswith('/') else '/' + libname
    newlibname = tempfile.mkstemp(suffix='.so', prefix='lib')
    os.write(newlibname[0], open(libxeprapi).read())
    os.close(newlibname[0])
    libAPI = ctypes.cdll.LoadLibrary(newlibname[1])
    os.unlink(newlibname[1])
    return libAPI


def _findInst(apilib):
    buf = ctypes.create_string_buffer(255)
    apilib.XeprGetSockDir(buf)
    topdir = buf.value
    dgramfile = map(str.split, open('/proc/net/unix').read().splitlines())
    suffserv = ctypes.string_at(apilib.suffserv)
    suffclient = ctypes.string_at(apilib.suffclient)
    sufftitle = ctypes.string_at(apilib.sufftitle)
    xeprsocks = [ f[(-1)] for f in dgramfile if f[(-1)].startswith(topdir) ]
    activedirs = [ os.path.dirname(f) for f in xeprsocks if f.endswith(suffserv) ]
    unconnected = [ f for f in activedirs if '%s/%s' % (f, suffclient) not in xeprsocks ]
    return [ (int(os.path.basename(f)), open(os.path.join(f, sufftitle)).read()) for f in unconnected ]


class _InstSelect():

    def __init__(self, items):
        self.items = items
        self.result = None
        master = self.master = tk.Tk()
        master.resizable(width=0, height=0)
        master.title('XeprAPI: Select Instance')
        labelfont = ('sans', 10)
        self.label = tk.Label(master, text='Select Xepr instance to connect to:', font=labelfont, padx=32, pady=32)
        self.lframe = tk.Frame(relief=tk.SUNKEN)
        self.spacer1 = tk.Frame()
        self.spacer2 = tk.Frame()
        self.listbox = tk.Listbox(self.lframe, font=labelfont, width=40)
        for item in items:
            self.listbox.insert(tk.END, item)

        self.scrollbar = tk.Scrollbar(self.lframe)
        self.scrollbar.config(command=self.listbox.yview)
        self.listbox.config(yscrollcommand=self.scrollbar.set)
        self.listbox.bind('<Double-Button-1>', self.selectcmd)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.pack(fill=tk.Y, expand=1)
        self.selectit = tk.Button(master, text='Select', font=labelfont, command=self.selectcmd)
        self.cancel = tk.Button(master, text='Cancel', font=labelfont, command=self.master.quit)
        self.label.pack()
        self.lframe.pack(fill=tk.BOTH, expand=1)
        self.spacer2.pack(fill=tk.X, pady=16)
        self.selectit.pack(side=tk.LEFT)
        self.cancel.pack(side=tk.RIGHT)
        master.mainloop()
        return

    def selectcmd(self, *l):
        try:
            self.result = int(self.listbox.curselection()[0])
        except:
            self.result = None

        self.master.quit()
        return


def _runInstSelect(thelist, thequeue):
    selector = _InstSelect(thelist)
    thequeue.put(selector.result)


def getXeprInstances():
    """
    Detects **Xepr** instances which are waiting for connections from XeprAPI clients. For this to work, the API has to be
    enabled in **Xepr** (menu "*Processing*"  ->  sub-menu "*XeprAPI*"  ->  menu item "*Enable Xepr API*"). Xepr instances which
    already are connected to an XeprAPI client are not listed.

    :return:        Dictionary of Xepr process ID numbers as its keys and the visible window title of the
                    Xepr instance as the corresponding values. The process ID (PID) keys can be used to connect to a specific
                    **Xepr** instance by specifying the PID when creating an object of :class:`~Xepr`.
"""
    apilib = _loadapilib()
    instances = _findInst(apilib)
    return dict([ (p, t) for p, t in instances ])


class Xepr(object):
    """
    Initializes the Xepr object and establishes a connection to the Xepr software. For this to work, the API has to be enabled in
    **Xepr** (menu "*Processing*"  ->  sub-menu "*XeprAPI*"  ->  menu item "*Enable Xepr API*").

    :param constantconstants: If *True*, ProDeL constants are only requested once upon API initialization; if *False*, the
            constants are requested from **Xepr** each time they are used in XeprAPI classes or in the Python script
            instantiating the class object. Typically, there is no reason to change the default behavior.
    :type constantconstants:    True or False; default = True

    :param libxeprapi: Specify path to the helper library *libxeprapi.so*. If no path is given, XeprAPI looks for the library in the directory
                       where the XeprAPI Python module is located as well as in the current directory.
    :type libxeprapi:  string or None; default = None

    :param verbose:    If *True*, enables a few messages in the XeprAPI module.
    :type verbose:     True or False; default = False

    :param pid:    Connect to a specific **Xepr** instance (corresponding to this process ID). If no *pid* value is specified an
                   **Xepr** instance will be sought out upon construction.
    :type pid:     integer value or *None*

    :return:           Instance of :class:`~Xepr`

    Example::

        >>> import XeprAPI

        >>> Xepr=XeprAPI.Xepr()

"""

    def __init__(self, constantconstants=True, libxeprapi=None, verbose=False, pid=None):
        self._APIopen = False
        self._API = _loadapilib(libxeprapi)
        self._constantconstants = constantconstants
        self.verbose = verbose
        self._dynamicmethods = []
        if 'XEPR_PID' not in os.environ:
            self._setDestPID(pid)
        else:
            self._setDestPID(int(os.environ['XEPR_PID']))
        self.XeprOpen()

    def __del__(self):
        self._API.XeprDisableAPI(0)

    def _findInstances(self):
        return _findInst(self._API)

    def _setDestPID(self, pid=None):
        available = self._findInstances()
        if available:
            if pid != None:
                if pid not in [ x[0] for x in available ]:
                    raise ValueError('No such Xepr instance waiting for connections.')
            elif len(available) == 1:
                pid = available[0][0]
            else:
                try:
                    theList = [ '%s (PID %u)' % (x[1], x[0]) for x in available ]
                    if 'MP' in globals():
                        theQueue = MP.Queue()
                        theProcess = MP.Process(target=_runInstSelect, args=(
                         theList, theQueue))
                        theProcess.start()
                    else:
                        theQueue = Queue.Queue()
                        _runInstSelect(theList, theQueue)
                    res = theQueue.get()
                except:
                    res = 0

                if res != None:
                    pid = available[res][0]
        if not pid:
            raise IOError('%sCould not connect to any Xepr instance.' % _msgprefix)
        else:
            self._API.XeprSetInstPID(pid)
        return

    def _printmsg(self, msg, newline=True, prefix=_msgprefix):
        if self.verbose:
            if prefix:
                print >> stderr, '%s%s%s' % (prefix, msg, '\n' if newline else ''),
            else:
                print >> stderr, '%s%s' % (msg, '\n' if newline else ''),

    def XeprActive(self):
        """
    :returns: *True* if the *Xepr API* is active.
"""
        return self._API.XeprAPIactive() >= SUCCESS

    def XeprOpen(self):
        """
    Opens the Xepr API for Python. Can be used to re-open the API after having closed it using :meth:`XeprClose`. Usually, you
    will not need to open the API manually, since it will be opened automatically upon instantiation of the :class:`~Xepr` class, i.e.
    by creating an instance of :class:`XeprAPI.Xepr()`.

    :raises: IOError exception in case opening the *Xepr API* did not succeed.
"""
        self._printmsg('Opening Xepr API...', newline=False)
        if self._API.XeprAPIactive() < SUCCESS:
            self._printmsg('failed.', prefix=None)
            raise IOError('%sCould not open API' % _msgprefix)
        namesP = ctypes.c_char_p()
        argsP = ctypes.c_char_p()
        retsP = ctypes.c_char_p()
        numoffunctions = self._API.XeprGetFunctions(byref(namesP), byref(argsP), byref(retsP))
        assert not numoffunctions < SUCCESS, '%sUnable to retrieve API function list' % _msgprefix
        listoffunctions = ctypes.string_at(namesP).splitlines()
        listofargs = NP.fromstring(ctypes.string_at(argsP, numoffunctions), NP.int8)
        listofrets = NP.fromstring(ctypes.string_at(retsP, numoffunctions), NP.bool)
        prodeldirP = ctypes.c_char_p()
        self._API.XeprGetProDeLDir(byref(prodeldirP))
        prodeldoc = self._getprodelprototypes(ctypes.string_at(prodeldirP), PRODELDOCSUBDIR)
        self._prodeldoc = prodeldoc
        for idx, func, args, rets in zip(range(len(listoffunctions)), listoffunctions, listofargs, listofrets):
            if hasattr(self, func):
                func = '_%s_' % func
            self._dynamicmethods.append(func)
            returnavalue = 'True' if rets else 'False'
            if args >= 0:
                if self._constantconstants and args == 0 and func.isupper() and rets:
                    setattr(self, func, self._callXeprfunc(idx, True))
                else:
                    params = (', ').join([ 'p%u' % i for i in range(args) ])
                    setattr(self, func, types.MethodType(eval('lambda self,%s: self._callXeprfunc(%u, %s, %s)' % (
                     params, idx, returnavalue, params)), self, self.__class__))
            else:
                setattr(self, func, types.MethodType(eval('lambda self, *p: self._callXeprfunc(%u, %s, *(p+(len(p),)))' % (
                 idx, returnavalue)), self, self.__class__))
            if hasattr(getattr(self, func), '__func__'):
                if func in prodeldoc:
                    setattr(getattr(self, func).__func__, '__doc__', prodeldoc[func] + '\n\nSee ProDeL documentation in Xepr for more information.')
                else:
                    setattr(getattr(self, func).__func__, '__doc__', 'See ProDeL documentation in Xepr for information.')

        self._printmsg('done.', prefix=None)
        commandsP, argdescsP = ctypes.c_char_p(), ctypes.c_char_p()
        numofcommands = self._API.XeprGetXeprCommands(byref(commandsP), byref(argdescsP))
        assert not numofcommands < SUCCESS, '%sUnable to retrieve Xepr function list' % _msgprefix
        listofcommands = ctypes.string_at(commandsP).splitlines()
        listofcommandargs = ctypes.string_at(argdescsP).splitlines()
        self.XeprCmds = self._cmds()
        self.XeprCmds._execCmd = self.execCmd
        for cmdname, arg in zip(listofcommands, listofcommandargs):
            if cmdname[0].isalpha():
                setattr(self.XeprCmds, cmdname, types.MethodType(eval("lambda self, *p: self._execCmd('%s', *p)" % cmdname), self.XeprCmds, self._cmds))

        return

    def getTitle(self, dset):
        buf = self.Xeprbuf(1024)
        self._getTitle_(dset, buf)
        return buf.getstr()

    def aqGetStrParValue(self, *p):
        buf = self.Xeprbuf(1024)
        self._aqGetStrParValue_(*(p + (buf, len(buf))))
        return buf.getstr()

    def aqGetSplFormula(self, *p):
        buf = self.Xeprbuf(1024)
        self._aqGetSplFormula_(*(p + (buf, len(buf))))
        return buf.getstr()

    def aqGetParUnits(self, *p):
        buf = self.Xeprbuf(1024)
        self._aqGetParUnits_(*(p + (buf, len(buf))))
        return buf.getstr()

    def aqGetParLabel(self, *p):
        buf = self.Xeprbuf(1024)
        self._aqGetParLabel_(*(p + (buf, len(buf))))
        return buf.getstr()

    def aqGetSplName(self, *p):
        buf = self.Xeprbuf(1024)
        self._aqGetSplName_(*(p + (buf, len(buf))))
        return buf.getstr()

    def aqGetComment(self, *p):
        buf = self.Xeprbuf(1024)
        self._aqGetComment_(*(p + (buf, len(buf))))
        return buf.getstr()

    def XeprDataset(self, *p, **k):
        """
    Create a :class:`~Dataset` object for accessing Xepr's datasets or creating new datasets (both 1D and 2D).

    :param size: Size of dataset to be created. If *size* = *None*, no dataset is created, but it will be retrieved from the **Xepr** dataset
                 specified by *xeprset* upon access to one of the attributes of the dataset object. If *size* is an integer number,
                 a 1D dataset will be created, with *size* being the number of values on the abscissa. If *size* is a tuple of two integer
                 numbers, i.e. (X,Y), a 2D dataset will be created, with X being the number of values on the first abscissa and Y
                 the number of values on the second abscissa.
    :type size:  integer value or tuple of integer values or None; default = None
    :param shape: similar to *size* argument, but in reversed order for 2D datasets, where *shape* = (Y,X) will create a dataset with
                  X being the number of values on the first abscissa and Y the number of values on the second abscissa. For 1D
                  datasets, *size* and *shape* have the same meaning.
    :type shape:  integer value or tuple of integer values or None; default = None

    :param autorefresh: If *True*, the GUI of the **Xepr** application will be refreshed each time the :meth:`~Dataset.update`
                        method is
                        called. If *False*, the GUI is refreshed only by calling the :meth:`~XeprGUIrefresh` method or if the
                        :meth:`~Dataset.update` method is called with the 'refresh' option.
    :type autorefresh:  True or False; default = False
    :param xeprset:     Select the dataset of the **Xepr** application to be used for writing a dataset to
                        (by calling :meth:`~Dataset.update`) or for retrieving a dataset from.
    :type xeprset:      string, default = "primary"
    :param iscomplex:   If *True*, a dataset would be created with a complex ordinate. Only valid if *size* != *None*,
                        i.e. if a dataset is to be created.
    :type iscomplex:    True or False; default = False

    Examples::

        # ...suppose we already have the Xepr object...
        >>> dset_pri = Xepr.XeprDataset()                          # retrieve Xepr's primary dataset
        >>> dset_sec = Xepr.XeprDataset(xeprset = "secondary")     # retrieve Xepr's secondary dataset

        >>> dset1D = Xepr.XeprDataset(size = 1024,                 # create 1D dataset with 1024 abscissa values
                                      xeprset = "secondary")       # associated with Xepr's secondary dataset

        >>> dset2D = Xepr.XeprDataset(size = (1024, 25))           # create 2D dataset with X * Y = 1024 * 25 values
        # this produces the same type of dataset:
        >>> dset2D = Xepr.XeprDataset(shape = (25, 1024))          # using shape argument: Y * X = 25 * 1024 values
"""
        return Dataset(self, *p, **k)

    def XeprExperiment(self, *p, **k):
        """
    Creates Experiment object to create a new experiment or to access an experiment already set up by the operator of the **Xepr**
    application.

    :param name_or_vp:  If *name_or_vp* is an integer value, the :class:`~Experiment` object accesses the experiment corresponding
                        to the **Xepr** viewport specified by *name_or_vp*; by default, the viewport number is *-1*, i.e. the
                        current viewport. If *name_or_vp* is a string, it is used as the name of the experiment in **Xepr** to be
                        created or accessed. If none of the remaining parameters is explicitly set, the :class:`~Experiment` object
                        accesses the **Xepr** experiment by the name given for *name_or_vp*. If in addition to the string in
                        *name_or_vp* any parameter is given, **Xepr** will try to build the experiment described by the parameters.
    :type name_or_vp:   string or integer number; default = -1
    :param exptype:     type of the experiment to be built, e.g. "C.W." or "Pulse".
    :type exptype:      string or None; default = None
    :param axs1:        Type of the first abscissa, e.g. "Field"; required for building a 1D or 2D experiment.
    :type axs1:         string or None; default = None
    :param axs2:        Type of the first abscissa, e.g. "Field"; required for building a 2D experiment.
    :type axs2:         string or None; default = None
    :param ordaxs:      Type of the ordinate, e.g. "Signal channel" or "Transient recorder"; required for building 1D or 2D experiments.
    :type ordaxs:       string or None: default = None
    :param addgrad:     If *True*, add gradient unit to the experiment to be built.
    :param addgonio:    If *True*, add goniometer unit to the experiment to be built.
    :param addvtu:      If *True*, add temperature controller to the experiment to be built.

    Examples::

        # ...suppose we already have the Xepr object...
        >>> cur_exp = Xepr.XeprExperiment()     # access current experiment in Xepr

        >>> cw_exp = Xepr.XeprExperiment("CWExp", exptype="C.W.", axs1="Field",   # create CW experiment
                                         ordaxs="Signal channel", addgrad=True)   # and add a gradient unit

        >>> pulse_exp = Xepr.XeprExperiment("PulseExp", exptype="Pulse",                # create a pulse
                                           axs1="Field", ordaxs="Transient recorder")   # experiment
"""
        return Experiment(self, *p, **k)

    def XeprClose(self):
        """
    Closes the API and tells **Xepr** to shut down its API support as well. After that, the API support of **Xepr**
    has to be re-enabled manually by the **Xepr** operator (menu "*Processing*"  ->  sub-menu "*XeprAPI*"
    ->  menu item "*Enable Xepr API*") to be able to establish the *Xepr API* again.

    :raises: IOError exception in case shutting down the *Xepr API* did not succeed.
"""
        for func in self._dynamicmethods:
            delattr(self, func)

        self._dynamicmethods = []
        self._printmsg('Closing API...', newline=False)
        if self._API.XeprDisableAPI(1) == SUCCESS:
            self._printmsg('done.', prefix=None)
            self._APIopen = False
        else:
            self._printmsg('done.', prefix=None)
            raise IOError('%sCould not close API' % _msgprefix)
        return

    def _popvalue(self):
        dtype_ord = ctypes.c_int()
        data = ctypes.create_string_buffer(255)
        self._API.XeprPopValue(byref(dtype_ord), data)
        dtype = STACK_TYPES[dtype_ord.value]
        if hasattr(ctypes.c_int, 'from_buffer_copy'):
            if dtype != pointer:
                return dtype.from_buffer_copy(data).value
            return dtype.from_buffer_copy(data)
        else:
            if dtype == pointer:
                tmpint = ctypes.c_int32.from_address(ctypes.addressof(data))
                val = pointer(tmpint.value)
                return val
            val = dtype.from_address(ctypes.addressof(data))
            return val.value

    def _pushvalue(self, val):
        dtype = None
        if isinstance(val, pointer):
            dtype = pointer
        else:
            if isinstance(val, Xepr.Xeprbuf):
                dtype = Xepr.Xeprbuf
            elif isinstance(val, bool):
                dtype = ctypes.c_bool
            elif isinstance(val, tuple(INT_TYPES)):
                dtype = ctypes.c_int
            elif isinstance(val, tuple(FLOAT_TYPES)):
                dtype = ctypes.c_double
            elif isinstance(val, char):
                dtype = char
            elif type(val) == str:
                dtype = str
            try:
                stacktype = STACK_TYPES.index(dtype)
            except AttributeError:
                stacktype = [ i for i, x in enumerate(STACK_TYPES) if x == dtype ][0]

        if not isinstance(val, (str, Xepr.Xeprbuf)):
            data = ctypes.string_at(ctypes.addressof(dtype(val)), size=ctypes.sizeof(dtype))
            self._API.XeprPushValue(stacktype, data, len(data))
        else:
            val = val + '\x00' if dtype == str else val.getstr(raw=True)
            self._API.XeprPushValue(stacktype, val, len(val))
        return

    def _callXeprfunc(self, funcidx, returnavalue, *p):
        listofbuffers = []
        for arg in p:
            self._pushvalue(arg)
            if isinstance(arg, Xepr.Xeprbuf):
                listofbuffers.append(arg.buffer)

        assert not self._API.XeprCallFunction(funcidx) != 0, '%sError processing function call' % _msgprefix
        for buf in reversed(listofbuffers):
            tmpbuf = ctypes.create_string_buffer(len(buf.tostring()))
            self._API.XeprGetMutable(ctypes.addressof(tmpbuf), len(buf.tostring()))
            buf[:] = NP.fromstring(tmpbuf, dtype=buf.dtype)

        if returnavalue:
            return self._popvalue()

    def XeprGUIrefresh(self):
        """
    Refreshes the **Xepr** GUI.
"""
        self._API.XeprRefreshGUI()

    def _getprodelprototypes(self, *path):
        dir = os.path.join(*path)
        if not os.path.isdir(dir):
            return dict()
        docdict = dict()
        fnames = [ os.path.join(dir, f) for f in os.listdir(dir) if f.endswith('.doc') ]
        pattern = re.compile('(\\w*\\s*(\\w+)[ \\t]*\\([\\w\\s,]*\\))')
        for fname in fnames:
            f = open(fname)
            content = f.read()
            f.close()
            matches = re.findall(pattern, content)
            for docstr, funcname in matches:
                docdict[funcname] = docstr

        return docdict

    class Xeprbuf:

        def __init__(self, preset='', length=None, dtype=NP.byte):
            if isinstance(preset, int) and length == None:
                length, preset = preset, ''
            buflen = 1 + (length if length != None else len(preset))
            self.buffer = NP.zeros(shape=buflen, dtype=dtype)
            if dtype == NP.byte:
                self.setstr(preset)
            return

        def setstr(self, s):
            self.buffer[:(len(s))] = NP.fromstring(s, dtype=NP.byte)
            self.buffer[len(s)] = 0

        def getstr(self, raw=False):
            s = self.buffer.tostring()
            if raw:
                return s
            return s[:s.index('\x00')]

        def __repr__(self):
            return self.buffer.tostring()

        def __len__(self):
            return self.buffer.size - 1

        def __getitem__(self, idx):
            return self.buffer.__getitem__(idx)

        def __setitem__(self, idx, val):
            return self.buffer.__setitem__(idx, val)

        def size(self):
            return len(self.buffer.tostring())

    class _cmds:
        pass


STACK_TYPES = (NP.nan, pointer, ctypes.c_bool, ctypes.c_double, ctypes.c_float,
 ctypes.c_long, ctypes.c_int, ctypes.c_short, char,
 str, Xepr.Xeprbuf)
INT_TYPES = frozenset((int, NP.int, NP.int32, NP.int64))
try:
    FLOAT_TYPES = frozenset((float, NP.float, NP.float32, NP.float64, NP.float128))
except AttributeError:
    FLOAT_TYPES = frozenset((float, NP.float, NP.float32, NP.float64))


class DatasetError(Exception):
    """
        raised when a dataset cannot be retrieved or accessed
    """
    pass


class DimensionError(Exception):
    """
        raised when a dataset does not match the number of dimensions of target/source data to be retrieved/written
    """
    pass


class ExperimentError(Exception):
    """
        raised when an experiment cannot be created, retrieved or accessed
    """
    pass


class ParameterError(Exception):
    """
        raised when a parameter is not available in an experiment or the type of parameter (scalar/multi-dimensional) does not match the
        type being written to/read from the parameter.
    """
    pass


class Dataset(object):
    _xeprsets = dict(pri={'_getcopy': 'getCopyOfPrimary', '_copyto': 'copyDsetToPrimary'}, sec={'_getcopy': 'getCopyOfSecondary', '_copyto': 'copyDsetToSecondary'}, res={'_getcopy': 'getCopyOfResult', '_copyto': 'copyDsetToResult'}, qua={'_getcopy': 'getCopyOfQualifier', '_copyto': 'copyDsetToQualifier'})
    _implicitdset = ('getTitle setTitle get2DValue getNrOfPoints getAbscType getSPLReal\n                     getCopyOfSlice getDimension getMax getMin getValue\n                     storeCopyOfDset appendPoint copyDsetToPrimary copyDsetToQualifier\n                     copyDsetToResult copyDsetToSecondary fillAbscissa insertPoint\n                     isComplex removePoint set2DValue setAbscType setValue').split()
    _toberenamed = 'isComplex'

    def __init__(self, parent, size=None, autorefresh=False, xeprset='primary', iscomplex=False, shape=None):
        self._parent = parent
        self.autorefresh = autorefresh
        self.setXeprSet(xeprset)
        self._dset = self._parent.NIL
        self._upstream = False
        self._arrays = dict()
        self._modified = set()
        assert not size and shape, '%seither size or shape argument allowed only' % _msgprefix
        if shape:
            if isinstance(shape, tuple):
                size = shape[::-1]
            else:
                size = shape
        if size:
            if isinstance(size, tuple) and len(size) == 1:
                size = size[0]
            assert not not isinstance(size, int) and not (isinstance(size, tuple) and len(size) == 2 and isinstance(size[0], int) and isinstance(size[1], int)), '%ssize argument has to be an integer number or a tuple of one/two integer numbers' % _msgprefix
            if isinstance(size, int):
                dset = self._parent.createDset(iscomplex == True, size)
                size = (size,)
            else:
                dset = self._parent.create2DDset(iscomplex == True, size[0], size[1])
                size = size[::-1]
            self._dset = dset
            self._upstream = True
            self.shape = size
            self.size = self.shape[::-1]
            self.isComplex = self.iscomplex = iscomplex
        if not hasattr(self, self._implicitdset[0]):
            for fkt in self._implicitdset:
                setattr(self, fkt if not hasattr(self, fkt) and fkt not in self._toberenamed else '_%s_' % fkt, types.MethodType(eval('lambda self,*p : self._parent.%s(self.getDset(), *p)' % fkt), self, self.__class__))

    def datasetAvailable(self):
        """
            Check whether dataset is available

            :returns:    *True* if the dataset has been created by the user or if the dataset is available in **Xepr**.
                        In the latter case, the dataset in **Xepr** is copied to the :class:`~Dataset` object. If *False* is returned
                        a subsequent access to attributes of the :class:`~Dataset` object would raise an exception.
        """
        dset = None
        try:
            dset = self._getcopy()
        except:
            pass

        if dset != None:
            self._parent.destroyDset(dset)
            return True
        else:
            return False
            return

    def getDset(self, force=False):
        if self._dset == self._parent.NIL or force:
            try:
                self._dset = self._getcopy()
            except:
                raise DatasetError('%scould not retrieve dataset from Xepr' % _msgprefix)

            self._arrays = dict()
            self._modified = set()
            self.isComplex = self.iscomplex = self._parent.isComplex(self._dset)
            getNrOfPoints = self._parent.getNrOfPoints
            if self._parent.getDimension(self._dset) == 1:
                self.shape = (
                 getNrOfPoints(self._dset, self._parent.X_ABSC),)
            else:
                self.shape = (
                 getNrOfPoints(self._dset, self._parent.Y_ABSC),
                 getNrOfPoints(self._dset, self._parent.X_ABSC))
            self.size = self.shape[::-1]
        return self._dset

    def getN2DValues(self, xIdx, xN, yIdx, yN, ordtype):
        dset = self.getDset()
        size = xN * ctypes.sizeof(ctypes.c_double)
        buf = self._parent.Xeprbuf(size)
        data = NP.empty(shape=(yN, xN), dtype=NP.double)
        for y in range(yN):
            self._parent.getN2DValues(dset, 0, xN, y, 1, ordtype, buf)
            data[y][:] = NP.fromstring(buf.getstr(raw=True)[:size], dtype=NP.double)[:]

        return data

    def __del__(self):
        try:
            if self._dset != self._parent.NIL:
                self._parent.destroyDset(self._dset)
                self._dset = self._parent.NIL
                self._upstream = False
                self._arrays = dict()
                self._modified = set()
                delattr(self, 'shape')
                delattr(self, 'isComplex')
                delattr(self, 'iscomplex')
        except:
            pass

    def _updateupstream(self):
        is2D = len(self.shape) == 2
        x, y = self.shape[(-1)], self.shape[0] if is2D else None
        iscomplex = self.isComplex
        for modified in self._modified:
            if modified in self._arrays:
                if modified == 'X':
                    for i, val in enumerate(self._arrays['X']):
                        self.setValue(i, self._parent.X_ABSC, val)

                if modified == 'Y':
                    for i, val in enumerate(self._arrays['Y']):
                        self.setValue(i, self._parent.Y_ABSC, val)

                if modified == 'O':
                    if is2D:
                        dsetP = self.getDset()
                        valarr_real = self._arrays['O'].real.astype(NP.double)
                        for j in xrange(y):
                            self._parent.setN2DValues(dsetP, 0, x, j, 1, self._parent.REAL_ORD, valarr_real[j].tostring())

                        if iscomplex:
                            valarr_imag = self._arrays['O'].imag.astype(NP.double)
                            for j in xrange(y):
                                self._parent.setN2DValues(dsetP, 0, x, j, 1, self._parent.IMAG_ORD, valarr_imag[j].tostring())

                    else:
                        for i, val in enumerate(self._arrays['O']):
                            self.setValue(i, self._parent.REAL_ORD, val.real)
                            if iscomplex:
                                self.setValue(i, self._parent.IMAG_ORD, val.imag)

        return

    def fromXepr(self, xeprset=None):
        """
            Update the dataset in the :class:`~Dataset` instance with data from **Xepr**. Calls :meth:`~Dataset.update` with
            the *reverse* parameter set accordingly. See :meth:`~Dataset.update` for a description of the remaining parameter(s).

            Examples::

                # ...suppose we already have the Xepr object...
                >>> exp = Xepr.XeprExperiment()                         # get object to control current experiment in Xepr
                >>> exp.aqExpRunAndWait()                               # run the experiment once
                >>> dset = Xepr.XeprDataset()                           # retrieve Xepr's primary dataset
                >>> print max(dset.O)                                   # print maximum ordinate value
                >>> exp.aqExpRunAndWait()                               # run the experiment again
                >>> dset.fromXepr()                                     # update the Dataset instance with the new data
                >>> print max(dset.O)                                   # print maximum ordinate value for this run
        """
        reverse = self._upstream
        return self.update(reverse=reverse, xeprset=xeprset)

    def toXepr(self, refresh=False, xeprset=None, store=False):
        """
            Update the dataset in **Xepr** with the data in the :class:`~Dataset` instance. Calls :meth:`~Dataset.update` with
            the *reverse* parameter set accordingly. See :meth:`~Dataset.update` for a description of the remaining parameters.

            Examples::

                # ...suppose we already have the Xepr object...
                >>> dset_sec = Xepr.XeprDataset(xeprset = "secondary")  # retrieve Xepr's secondary dataset
                >>> dset_sec.O -= dset_sec.O.sum() / len(dset_sec.O)    # subtract DC signal
                >>> dset_sec.toXepr(refresh=True)                       # update the secondary dataset in the Xepr application
                                                                        # and refresh the GUI
        """
        reverse = not self._upstream
        return self.update(reverse=reverse, refresh=refresh, xeprset=xeprset, store=store)

    def update(self, reverse=False, refresh=False, xeprset=None, store=False):
        """
            Update the dataset in **Xepr** with the data in the :class:`~Dataset` instance (if the dataset
            has been created upon instantiation using the *size* parameter) or update the :class:`~Dataset` instance with data originating
            from the corresponding dataset in **Xepr** (if the :class:`~Dataset` has been instantiated without the *size* parameter).

            :param reverse:     If *False*, the update takes place as described above. If *True*, the direction of the update is reversed.
            :type reverse:      True or False; default = False
            :param refresh:     If *True*, the GUI of the **Xepr** application is refreshed after updating the dataset.
                                Useful if the dataset in the **Xepr** application is to be updated from the data in the :class:`~Dataset`,
                                since only after refreshing the **Xepr** GUI the changes will be displayed.
            :type refresh:      True or False; default = False
            :param xeprset:     If not *None*, the dataset of the **Xepr** application the :class:`~Dataset` has been associated with upon
                                instantiation will be changed prior to updating. Same as calling the :meth:`~Dataset.setXeprSet` method
                                before calling :meth:`~Dataset.update`
            :type xeprset:      string or None; default=None
            :param store:       If *True*, the dataset content will be stored in **xepr** memory and can be accessed from the drop-down
                                menu of the viewport. The title of the dataset will be used as the designator of the menu entry.
            :type store:        True or False; default = False

            Examples::

                # ...suppose we already have the Xepr object...
                >>> dset_sec = Xepr.XeprDataset(xeprset = "secondary")  # retrieve Xepr's secondary dataset
                >>> dset_sec.O -= dset_sec.O.sum() / len(dset_sec.O)    # subtract DC signal
                >>> dset_sec.update(reverse=True,                       # update the secondary dataset in the Xepr application
                                    refresh=True)                       # and refresh the GUI

                >>> exp = Xepr.XeprExperiment()                         # get object to control current experiment in Xepr
                >>> exp.aqExpRunAndWait()                               # run the experiment once
                >>> dset = Xepr.XeprDataset()                           # retrieve Xepr's primary dataset
                >>> print max(dset.O)                                   # print maximum ordinate value
                >>> exp.aqExpRunAndWait()                               # run the experiment again
                >>> dset.update()                                       # update the Dataset instance with the new data
                >>> print max(dset.O)                                   # print maximum ordinate value for this run
        """
        if xeprset:
            self.setXeprSet(xeprset)
        if self._upstream ^ reverse:
            self._updateupstream()
            self._copyto(self._dset)
            if self.autorefresh or refresh:
                self._parent.XeprGUIrefresh()
            if store != False:
                return self.storeCopyOfDset()
        elif self._dset != self._parent.NIL:
            self._parent.destroyDset(self._dset)
        else:
            self._dset = self.getDset(force=True)

    def setXeprSet(self, xeprset):
        """
            Change the dataset of the **Xepr** application the :class:`~Dataset` instance is currently associated with.

            :param xeprset:     Name of the dataset of the **Xepr** application (e.g. "primary" or "secondary" etc.) the
                                :class:`~Dataset` instance is to be associated with.
            :type xeprset:      string
        """
        try:
            setinfo = self._xeprsets[xeprset.lower()[:3]]
        except:
            raise ValueError("%sno such Xepr dataset '%s'" % (_msgprefix, str(xeprset)))

        for tok in setinfo:
            setattr(self, tok, getattr(self._parent, setinfo[tok]))

    def __getattr__(self, name):
        if name in ('X', 'Y', 'O'):
            assert not name == 'Y' and len(self.shape) < 2, '%s1D dataset, does not have second abscissa' % _msgprefix
            if name not in self._arrays:
                if name == 'O':
                    is2D = len(self.shape) == 2
                    x, y = self.shape[(-1)], self.shape[0] if is2D else None
                    iscomplex = self.isComplex
                    if iscomplex:
                        if is2D:
                            val = NP.empty(shape=(y, x), dtype=NP.complex64)
                            val.real[:] = self.getN2DValues(0, x, 0, y, self._parent.REAL_ORD)[:]
                            val.imag[:] = self.getN2DValues(0, x, 0, y, self._parent.IMAG_ORD)[:]
                        else:
                            it = (complex(self.getValue(i, self._parent.REAL_ORD), self.getValue(i, self._parent.IMAG_ORD)) for i in xrange(x))
                            val = NP.fromiter(it, dtype=NP.complex64)
                    elif is2D:
                        val = NP.empty(shape=(y, x), dtype=NP.float64)
                        val[:] = self.getN2DValues(0, x, 0, y, self._parent.REAL_ORD)[:]
                    else:
                        it = (self.getValue(i, self._parent.REAL_ORD) for i in xrange(x))
                        val = NP.fromiter(it, dtype=NP.float64)
                    if is2D:
                        val = val.reshape(y, x)
                elif name in ('X', 'Y'):
                    ax = self._parent.X_ABSC if name == 'X' else self._parent.Y_ABSC
                    imax = self.shape[(-1)] if name == 'X' else self.shape[0]
                    it = (self.getValue(i, ax) for i in xrange(imax))
                    val = NP.fromiter(it, dtype=NP.float64)
                self._arrays[name] = val
                self._modified.add(name)
            return self._arrays[name]
        else:
            if name in ('shape', 'size'):
                self.getDset()
                return object.__getattribute__(self, name)
            else:
                if name in ('isComplex', 'iscomplex'):
                    self.getDset()
                    return object.__getattribute__(self, name)
                return object.__getattribute__(self, name)

            return

    def __setattr__(self, name, val):
        if name not in ('X', 'Y', 'O'):
            object.__setattr__(self, name, val)
        elif not NP.iterable(val):
            raise TypeError('%svalue is not iterable', _msgprefix)
        else:
            try:
                self.getDset()
            except:
                raise DatasetError('%sno dataset available, cannot set %s attribute' % _msgprefix)

        assert not name == 'Y' and len(self.shape) < 2, '%s1D dataset, does not have second abscissa' % _msgprefix
        val = NP.array(val)
        if name == 'O' and val.shape != self.shape:
            raise ValueError('%sshape of the ordinate value does not match the shape of the dataset' % _msgprefix)
        elif name == 'X' and val.shape[(-1)] != self.shape[(-1)] or name == 'Y' and val.shape[0] != self.shape[0]:
            raise ValueError('%ssize of the abscissa value does not match the size of the dataset abscissa' % _msgprefix)
        else:
            self._arrays[name] = val
            self._modified.add(name)


class Experiment(object):
    _implicitexp = ('aqExpRunAndWait aqExpActivate aqExpInstall aqExpAbort aqExpPause aqExpStop aqExpEdit aqExpSync aqExpRun\n                      aqGetParCoarseSteps aqGetRealParValue aqGetBoolParValue aqGetParFineSteps aqStepParValue aqGetStrParValue\n                      aqGetIntParValue aqGetParMaxValue aqGetParMinValue aqGetParDimSize aqGetParUnits aqGetParLabel\n                      aqGetParNbDim aqGetExpState aqGetParType aqSetRealParValue aqSetBoolParValue aqSetStrParValue aqSetIntParValue\n                      aqMbcFineTune aqMbcOperate aqMbcStandby aqGetExpFuList aqGetExpFuParList\n                   ').split()

    def __init__(self, parent, name_or_vp=-1, exptype=None, axs1=None, axs2=None, ordaxs=None, addgrad=False, addgonio=False, addvtu=False):
        self._fupardict = dict()
        self._fuparhist = dict()
        self._parent = parent
        anyextraparam = any((exptype, axs1, axs2, ordaxs, addgrad, addgonio, addvtu))
        self._expstates = dict(isActive=parent.AQ_EXP_ACTIVE, isEdit=parent.AQ_EXP_EDIT, isPaused=parent.AQ_EXP_PAUSED, isClosed=parent.AQ_EXP_CLOSED, isInstalled=parent.AQ_EXP_INSTALLED, isRunning=parent.AQ_EXP_RUNNING)
        if isinstance(name_or_vp, int):
            if anyextraparam:
                raise ValueError('%swith a vievport number given no extra arguments are allowed' % _msgprefix)
            else:
                self._exp = self._parent.aqGetSelectedExp(name_or_vp)
                if self._exp.value == 0:
                    raise ExperimentError('%sunable to retrieve experiment from viewport %i' % (_msgprefix, name_or_vp))
                else:
                    buf = self._parent.Xeprbuf(256)
                    self._parent.aqGetExpNameToBuf(self._exp, buf, 255)
                    self._expname = buf.getstr()
        elif isinstance(name_or_vp, basestring):
            if not anyextraparam:
                self._exp = self._parent.aqGetExpByName(name_or_vp)
                if self._exp.value == 0:
                    raise ExperimentError("%sno such experiment '%s'" % (_msgprefix, name_or_vp))
                else:
                    self._expname = name_or_vp
            else:
                requiredparams = (
                 exptype, axs1, ordaxs)
                if not all(requiredparams):
                    raise ValueError('%sat least experiment type, first abscissa and ordinate is required to build the experiment')
                else:
                    if not axs2:
                        axs2 = 'None'
                    self._parent.XeprCmds.aqExpNew(*(map(quote, (name_or_vp, exptype, axs1, axs2, ordaxs)) + [ 'On' if x else 'Off' for x in (addgrad, addgonio, addvtu) ]))
                    self._exp = self._parent.aqGetSelectedExp(-1)
                    if self._exp.value == 0:
                        raise ExperimentError("%sunable to create experiment '%s'" % (_msgprefix, name_or_vp))
                    else:
                        self._expname = name_or_vp
        else:
            raise ValueError('%sfirst argument must be either the experiment name or the viewport number' % _msgprefix)
        if not hasattr(self, self._implicitexp[0]):
            for fkt in self._implicitexp:
                setattr(self, fkt, types.MethodType(eval('lambda self,*p : self._parent.%s(self.getExp(), *p)' % fkt), self, self.__class__))

    def getFuList(self):
        """
            Get the list of functional units for the experiment.

            Example::

                # ...suppose we already have an Experiment object...
                >>> print hidden.getFuList()    # print functional units of hidden experiment
                ['specJet', 'freqCounter', 'sysConf', 'gTempCtrl', 'cwBridge', 'sctCalib', 'ffLock', 'ftBridge']
        """
        if self._fupardict:
            return self._fupardict.keys()
        else:
            buf = self._parent.Xeprbuf(10000)
            self.aqGetExpFuList(buf, 10000)
            return buf.getstr().split(',')

    def getFuParList(self, funame):
        """
            Get the list of paramater names for the functional unit *funame*.

            :param funame:      Specifies the name of the functional unit to list the parameter names for.
            :type funame:       string
            :returns:           List of the parameter names of the functional unit; empty list if the functional unit could not be found.

            Example::

                # ...suppose we already have an Experiment object...
                >>> print exp.getFuParList("cwbridge")      # print list of parameter for cwbridge unit
                ['AcqFineTuning', 'Power', 'PowerAt0dBMon', 'PowerAtten', 'PowerAttenMon']
        """
        if not self._fupardict:
            buf = self._parent.Xeprbuf(10000)
            for fu in self.getFuList():
                self.aqGetExpFuParList(fu, buf, 10000)
                parlist = [ x for x in buf.getstr().split(',') if self.aqGetParType('%s.%s' % (fu, x)) != self._parent.AQ_DT_UNKNOWN
                          ]
                self._fupardict[fu] = parlist

        if funame not in self._fupardict:
            for fu in self.getFuList():
                if fu.upper() == funame.upper():
                    funame = fu
                    break

        assert not funame not in self._fupardict, "%sno such functional unit '%s' in experiment '%s'" % (_msgprefix, funame, self.aqGetExpName())
        return self._fupardict[funame]

    def findParam(self, param, findall=False):
        """
            Finds the fully qualified parameter name for the name given by *param*

            :param param:   Name of the parameter to look for.
            :type param:    string, case-insensitive
            :param findall: If *True*, all matching parameters will be returned as a list; if *False*, only the first matching
                            parameter will be returned.
            :type findall:  *True* or *False*, default = *False*
            :returns:       List of matching parameters if *findall=True*, parameter string otherwise.

        """
        param = param.replace('*', '').strip()
        if not param:
            if not findall:
                return
            return []
        if param in self._fuparhist and not findall:
            return self._fuparhist[param]
        else:
            p = param.split('.')
            if len(p) not in (1, 2):
                if not findall:
                    return
                return []
            if len(p) == 1 or not p[0]:
                fulist = self.getFuList()
            else:
                fulist = [ fu for fu in self.getFuList() if fu.upper() == p[0].upper() ]
            parlist = []
            for fu in fulist:
                for par in self.getFuParList(fu):
                    if p[(-1)].upper() == par.upper():
                        parlist.append('%s.%s' % (fu, par))
                        if not findall:
                            break

                if not findall and parlist:
                    break

            if parlist:
                if len(parlist) == 1:
                    self._fuparhist[param] = '%s' % parlist[0]
                if findall:
                    return parlist
                return parlist[0]
            if findall:
                return []
            return
            return

    def __contains__(self, param):
        param = param.replace('*', '').strip()
        if not param:
            return False
        else:
            p = param.split('.')
            if len(p) not in (1, 2):
                return False
            if len(p) == 2 and not p[1]:
                for fu in self.getFuList():
                    if fu.upper() == p[0].upper():
                        return True

            else:
                return self.findParam(param) != None
            return False

    def getExp(self):
        return self._exp

    def aqGetExpName(self):
        """
        Get the name of the experiment.

        :returns: Name of the experiment represented by the :class:`~Experiment` instance as a string.
        """
        return self._expname

    def __getattr__(self, name):
        if name in self._expstates:
            return self.aqGetExpState() == self._expstates[name]
        else:
            return object.__getattribute__(self, name)

    def select(self, viewport=-1):
        self._parent.aqSetSelectedExp(viewport, self._expname)
        self._parent.XeprGUIrefresh()

    def __getitem__(self, name):
        return Parameter(self, name)

    def getParam(self, name, enum=None):
        """
            Equivalent to using the operator *[]*, except for the additional *enum* parameter.

            :param name:    Specifies the parameter of the experiment represented by the :class:`~Experiment` instance to be accessed.
            :type name:     string, case-insensitive
            :param enum:    Specifies the type to return for the *value* attribute in case the parameter addressed is an enumerating
                            type (represented in **Xepr** e.g. by a pull-down list). if *enum* == *str* the string corresponding to
                            the ordinal number is returned, if *enum* == *int*, the ordinal number is returned.
            :type enum:     str or int or None; default = None

            :returns:       Instance of :class:`~XeprAPI.Parameter` for the experiment parameter specified by *<operand string>*.
        """
        return Parameter(self, name, enum)


class Parameter(object):
    _implicitpar = ('aqGetParCoarseSteps aqGetRealParValue aqGetBoolParValue aqGetParFineSteps aqStepParValue aqGetStrParValue\n                      aqGetIntParValue aqGetParMaxValue aqGetParMinValue aqGetParDimSize aqGetParUnits aqGetParLabel\n                      aqGetParNbDim aqGetParType aqSetRealParValue aqSetBoolParValue aqSetStrParValue aqSetIntParValue\n                   ').split()

    def __init__(self, parent, name, enum=None):
        self._parent = parent
        self._name = name
        self._type = self._parent.aqGetParType(name)
        if self._type == self._parent._parent.AQ_DT_UNKNOWN:
            self._name = self._parent.findParam(name, findall=True)
            if isinstance(self._name, list):
                if len(self._name) > 1:
                    raise ParameterError("%sparameter name '%s' is ambiguous in experiment '%s'" % (_msgprefix, name, self._parent.aqGetExpName()))
                else:
                    self._name = self._name[0] if len(self._name) == 1 else None
            if self._name != None:
                name = self._name
                self._type = self._parent.aqGetParType(name)
            if self._type == self._parent._parent.AQ_DT_UNKNOWN:
                raise ParameterError("%sno such parameter '%s' in experiment '%s'" % (_msgprefix, name, self._parent.aqGetExpName()))
        self._dim = self._parent.aqGetParNbDim(name)
        if not hasattr(self, self._implicitpar[0]):
            for fkt in self._implicitpar:
                setattr(self, fkt if not hasattr(self, fkt) else '_%s_' % fkt, types.MethodType(eval('lambda self,*p : self._parent.%s(self._name, *p)' % fkt), self, self.__class__))

        xepr = self._parent._parent
        if self._type == xepr.AQ_DT_BOOLEAN:
            getpar, setpar = self.aqGetBoolParValue, self.aqSetBoolParValue
        elif self._type == xepr.AQ_DT_ENUM:
            getpar, setpar = self.aqGetEnumParValue, self.aqSetEnumParValue
        elif self._type == xepr.AQ_DT_STRING:
            getpar, setpar = self.aqGetStrParValue, self.aqSetStrParValue
        else:
            getpar, setpar = self.aqGetRealParValue, self.aqSetRealParValue
        self._getpar = getpar
        self._setpar = setpar
        if self._type == xepr.AQ_DT_ENUM:
            assert not enum and enum not in (int, str), "%san enum type parameter may only return 'int' or 'str' values" % _msgprefix
            self._enum = enum if enum else str
        return

    def aqGetEnumParValue(self, *p):
        if self._enum == str:
            return self.aqGetStrParValue(*p)
        else:
            return self.aqGetIntParValue(*p)

    def aqSetEnumParValue(self, dimSz, dimP, value):
        if isinstance(value, basestring):
            return self.aqSetStrParValue(dimSz, dimP, value)
        if isinstance(value, int):
            return self.aqSetIntParValue(dimSz, dimP, value)
        raise TypeError('%sneed integer or string value to set enum type parameter' % _msgprefix)

    def aqStepParValue(self, steps=1, finesteps=False):
        self._aqStepParValue_(1, self._parent._parent.NIL, finesteps, steps)

    def __getitem__(self, idx):
        assert not self._dim == 0, "%sparameter is a scalar, use 'value' attribute to get its value" % _msgprefix
        if not NP.iterable(idx):
            idx = (
             idx,)
        assert not len(idx) != self._dim, '%sparameter has %u dimensions, given index has %u dimensions' % (_msgprefix, self._dim, len(idx))
        buf = self._parent._parent.Xeprbuf(self._dim, dtype=NP.int32)
        for i, d in enumerate(idx):
            buf.buffer[i] = d

        return self._getpar(self._dim, buf)

    def __setitem__(self, idx, value):
        assert not self._dim == 0, "%sparameter is a scalar, use 'value' attribute to set it" % _msgprefix
        if not NP.iterable(idx):
            idx = (
             idx,)
        assert not len(idx) != self._dim, '%sparameter has %u dimensions, given index has %u dimensions' % (_msgprefix, self._dim, len(idx))
        buf = self._parent._parent.Xeprbuf(self._dim, dtype=NP.int32)
        for i, d in enumerate(idx):
            buf.buffer[i] = d

        return self._setpar(self._dim, buf, value)

    def __getattr__(self, name):
        if name == 'value':
            if self._dim != 0:
                raise ParameterError("%sparameter '%s' in experiment '%s' is not a scalar (has %u dimensions)" % (_msgprefix, self._name,
                 self._parent.aqGetExpName(), self._dim))
            else:
                return self._getpar(0, self._parent._parent.NIL)
        else:
            return object.__getattribute__(self, name)

    def __setattr__(self, name, value):
        if name != 'value':
            object.__setattr__(self, name, value)
        elif self._dim != 0:
            raise ParameterError("%sparameter '%s' in experiment '%s' is not a scalar (has %u dimensions)" % (_msgprefix, self._name,
             self._parent.aqGetExpName(), self._dim))
        else:
            return self._setpar(0, self._parent._parent.NIL, value)


if __name__ == '__main__':
    xepr = Xepr(verbose=True)
    print "\n>>> Xepr API now accessible via 'xepr' instance! <<<\n"