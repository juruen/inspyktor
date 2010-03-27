#! /usr/bin/env python
# Copyright (c) 2010 Javier Uruen (juruen@warp.es)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from PyQt4.QtCore import QAbstractTableModel, Qt
from PyQt4 import QtCore, QtGui
import re


class SystemCallInfo:
    FIELDS = ['Line', 'Time', 'Name', 'Paramaters', 'Return', 'Errno']

    FIELD_BY_INDEX = [
        'line',
        'time',
        'name',
        'parameters',
        'return_value',
        'errno',
        'elapsed_time']

    INDEX_BY_FIELD = {
        'line': 0,
        'time': 1,
        'name': 2,
        'parameters': 3,
        'return_value': 4,
        'errno': 5,
        'elapsed_time': 6}

    @staticmethod
    def param_by_index(syscall, index):
        params = syscall['parameters'].split(',')
        return params[index]


class FdTracker:
    def __init__(self):
        self.fds = {}
        for i, v in enumerate(['STDIN', 'STDOUT', 'STDERR']):
            self.fds[i] = [{
                'open_time': 0,
                'path': v,
                'mode': '',
                'open': True,
                'write_bytes_attempt': 0,
                'write_bytes_success': 0,
                'write_access': 0}]
        self.connect_regexp = None
        self.bind_regexp = None

    def add_open(self, syscall):
        fd = int(syscall['return_value'])
        if int(fd) < 0:
            return

        fd_ops = self._fd_operations(fd)

        parm_func = SystemCallInfo.param_by_index
        fd_ops.append({
                'open_time': syscall['time'],
                'path': parm_func(syscall, 0),
                'mode': parm_func(syscall, 1),
                'open': True,
                'write_bytes_attempt': 0,
                'write_byts_success': 0,
                'write_access': 0})

    def add_write(self, syscall):
        fd = int(SystemCallInfo.param_by_index(syscall, 0))
        attempt = int(SystemCallInfo.param_by_index(syscall, 0))
        success = int(syscall['return_value'])
        fd_operations = self._fd_operations(fd)
        if not fd_operations:
            return
        last_op = fd_operations[-1]
        last_op['write_access'] += 1
        last_op['write_bytes_attempt'] += attempt
        last_op['write_bytes_success'] += success

    def add_connect(self, syscall):
        fd = int(SystemCallInfo.param_by_index(syscall, 0))
        if not self.connect_regexp:
            self.connect_regexp = re.compile('.*sa_family=(.*), path="(.*)".*')
        match = self.connect_regexp.match(syscall['parameters'])
        fd_ops = self._fd_operations(fd)
        fd_ops.append({
                'open_time': syscall['time'],
                'path': match.group(2),
                'mode': match.group(1),
                'open': True,
                'write_bytes_attempt': 0,
                'write_byts_success': 0,
                'write_access': 0})

    def add_socket(self, syscall):
        name = str(syscall['name'])
        if (name == 'bind'):
            fd = int(SystemCallInfo.param_by_index(syscall, 0))
        else:
            fd = int(syscall['return_value'])

        if not self.sock_regexp:
            self.sock_regexp = re.compile('.*sa_family=(.*), '
                'sin_port=htons\((.*)\), '
                'sin_addr=inet_addr\("(.*)"\)},.*')
        match = self.sock_regexp.match(syscall['parameters'])
        fd_ops = self._fd_operations(fd)
        fd_ops.append({
                'open_time': syscall['time'],
                'path': match.group(3) + ':' + match.group(2),
                'mode': match.group(1),
                'open': True,
                'write_bytes_attempt': 0,
                'write_byts_success': 0,
                'write_access': 0})


    def fd_path(self, fd):
        fd_operations = self._fd_operations(fd)
        if not fd_operations:
            return
        last_op = fd_operations[-1]
        return last_op['path']

    def _fd_operations(self, fd):
        if not fd in self.fds:
            self.fds[fd] = []
        return self.fds[fd]


class SystemCallDecoder:
    def __init__(self):
        self.fd_tracker = FdTracker()

    def process(self, syscalls_info):
        for syscall in syscalls_info:
            name = str(syscall['name'])
            if name == 'open':
                self._decode_open(syscall)
            elif name == 'close':
                self._decode_close(syscall)
            elif name == 'write':
                self._decode_write(syscall)
            elif name == 'read':
                self._decode_read(syscall)
            elif name.startswith('fstat'):
                self._decode_fstat(syscall)
            elif name == 'connect':
                self._decode_connect(syscall)
            elif name == 'send':
                self._decode_send(syscall)
            elif name == 'bind':
                self._decode_socket(syscall)
            elif name == 'accept':
                self._decode_socket(syscall)
            elif name == 'listen':
                self._decode_base(syscall, ['file'])

    def _decode_base(self, syscall, description):
            params = str(syscall['parameters']).split(',')
            for index, desc in enumerate(description):
                if desc == 'file':
                    fd = int(SystemCallInfo.param_by_index(syscall, index))
                    decoded_fd = str(self.fd_tracker.fd_path(fd))
                    if decoded_fd is not None:
                        params[index] = decoded_fd
            syscall['parameters_decoded'] = ','.join(params)

    def _decode_open(self, syscall):
        self.fd_tracker.add_open(syscall)

    def _decode_close(self, syscall):
        self._decode_base(syscall, ['file'])

    def _decode_write(self, syscall):
        self.fd_tracker.add_write(syscall)
        self._decode_base(syscall, ['file'])

    def _decode_read(self, syscall):
        self._decode_base(syscall, ['file'])

    def _decode_fstat(self, syscall):
        self._decode_base(syscall, ['file'])

    def _decode_connect(self, syscall):
        self.fd_tracker.add_connect(syscall)

    def _decode_send(self, syscall):
        self._decode_base(syscall, ['file'])

    def _decode_socket(self, syscall):
        self.fd_tracker.add_socket(syscall)
        self._decode_base(syscall, ['file'])



class SystemCallModel(QAbstractTableModel):
    def __init__(self):
        QAbstractTableModel.__init__(self, None)
        self._syscalls = []
        self.decoder = SystemCallDecoder()

    def set_strace_runner(self, strace_runner):
        self.strace_runner = strace_runner
        self.connect(self.strace_runner,
            QtCore.SIGNAL('syscall_parsed'), self._slot_syscall_parsed)

    def rowCount(self, parent=None):
        return len(self._syscalls)

    def columnCount(self, parent=None):
        return len(SystemCallInfo.FIELDS)

    def data(self, index, role):
        line = self._syscalls[index.row()]

        if role == Qt.TextColorRole and self._syscall_failed(index):
            return QtGui.QColor("red")

        if role != Qt.DisplayRole:
            return  QtCore.QVariant()

        field_name = SystemCallInfo.FIELD_BY_INDEX[index.column()]
        if field_name == 'parameters' and 'parameters_decoded' in line:
            return line['parameters_decoded']
        else:
            return line[field_name]

    def headerData(self, section, orientation, role):
        if role != Qt.DisplayRole:
            return QtCore.QVariant()

        if orientation == Qt.Horizontal:
            return SystemCallInfo.FIELDS[section]
        else:
            return QtCore.QVariant()

    def clearData(self):
        self._syscalls = []

    def _syscall_failed(self, index):
        row = index.row()
        if len(self._syscalls) <= row:
            return False
        try:
            return_value = int(self._syscalls[row]['return_value'])
        except:
            return False

        return (return_value < 0)

    def _slot_syscall_parsed(self, syscall_info):
        self._syscalls.extend(syscall_info)
        self.reset()
        self.decoder.process(syscall_info)
