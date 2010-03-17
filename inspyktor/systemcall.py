#! /usr/bin/env python
# Copyright (c) 2010 Javier Uruen (juruen@warp.es)
# Licensed under the terms of the MIT license

from PyQt4.QtCore import QAbstractTableModel, Qt
from PyQt4 import QtCore


class SystemCallInfo():
    FIELDS = ['Line', 'Time', 'Name', 'Paramaters', 'Return', 'Errno']

    def __init__(self, parts=None):
        if parts is not None:
            pass
        else:
            self.line = None
            self.name = None
            self.parameters = None
            self.return_value = None
            self.errno = None
            self.elapsed_time = None
            self.time = None


class SystemCallModel(QAbstractTableModel):
    def __init__(self):
        QAbstractTableModel.__init__(self, None)
        self._syscalls = []

    def set_strace_runner(self, strace_runner):
        print "Setting strace runner"
        self.strace_runner = strace_runner
        self.connect(self.strace_runner,
            QtCore.SIGNAL('syscall_parsed'), self._slot_syscall_parsed)

    def rowCount(self, parent=None):
        #print "rowCount %i" % len(self._syscalls)
        return len(self._syscalls)

    def columnCount(self, parent=None):
        return len(SystemCallInfo.FIELDS)

    def data(self, index, role):
        if role != Qt.DisplayRole:
            return  QtCore.QVariant()

        FIELD_NUMBER = ['line', 'time', 'name', 'parameters',
                'return_value', 'errno', 'elapsed_time']

        line = self._syscalls[index.row()]
        return line[FIELD_NUMBER[index.column()]]

    def headerData(self, section, orientation, role):
        if role != Qt.DisplayRole:
            return QtCore.QVariant()

        if orientation == Qt.Horizontal:
            return SystemCallInfo.FIELDS[section]
        else:
            return QtCore.QVariant()

    def _slot_syscall_parsed(self, syscall_info):
        self._syscalls.extend(syscall_info)
        self.reset()
