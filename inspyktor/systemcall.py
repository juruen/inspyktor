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

from PyQt4.QtCore import QAbstractTableModel, Qt, QObject
from PyQt4 import QtCore, QtGui
from inspyktor import tree
import re


class SystemCallInfo:
    FIELDS = ['Line', 'PID', 'Time', 'Name', 'Parameters', 'Return', 'Errno']

    FIELD_BY_INDEX = [
        'line',
        'PID',
        'time',
        'name',
        'parameters',
        'return_value',
        'errno',
        'elapsed_time']

    INDEX_BY_FIELD = {
        'line': 0,
        'PID': 1,
        'time': 2,
        'name': 3,
        'parameters': 4,
        'return_value': 5,
        'errno': 6,
        'elapsed_time': 7}

    @staticmethod
    def param_by_index(syscall, index):
        params = syscall['parameters'].split(',')
        return params[index]

class FdInfo:
    FIELDS = ['PID', 'Path', 'Mode', 'Written Bytes', 'Open Time']

    KEY_BY_FIELD = {
        'PID' : 'pid',
        'Path': 'path',
        'Mode': 'mode',
        'Written Bytes': 'write_bytes_success',
        'Open Time': 'open_time',}

    COLUMNS = ['pid', 'path', 'mode', 'write_bytes_success', 'open_time']

class FdTracker:
    def __init__(self):
        self.fds = {}
        self.connect_regexp = None
        self.sock_regexp = None

    def _create_op(self, syscall, init_values):
        pid = ''
        time = 0
        if syscall is not None:
            pid = syscall['PID']
            time = syscall['time']

        fd_op = {
            'pid' : pid,
            'open_time': time,
            'path': '',
            'mode': '',
            'open': True,
            'write_bytes_attempt': 0,
            'write_bytes_success': 0,
            'write_access': 0,
            'fcntl': '',
            'close_on_exec': False,
        }
        return dict(fd_op.items() + init_values.items())

    def init_std(self, pid):
        for fd, name in enumerate(['STDIN', 'STDOUT', 'STDERR']):
            self.fds[fd] = [self._create_op(None, {'pid' : pid, 'path': name})]

    def add_open(self, syscall):
        fd = int(syscall['return_value'])
        if int(fd) < 0:
            return

        fd_ops = self._fd_operations(fd)

        parm_func = SystemCallInfo.param_by_index
        fd_ops.append(
            self._create_op(
                syscall,
                {
                    'path': parm_func(syscall, 0),
                    'mode': parm_func(syscall, 1)
                }
            )
        )

    def add_fcntl(self, syscall):
        fd = int(SystemCallInfo.param_by_index(syscall, 0))
        cmd = SystemCallInfo.param_by_index(syscall, 1)
        flags = SystemCallInfo.param_by_index(syscall, 2)
        if cmd == 'F_SETFD' and flags.find("CLOEXEC"):
            try:
                fd_op = self._fd_operations_syscall(syscall, fd)
                fd_op['close_on_exec'] = True
            except:
                print "fd %i not open" % fd

        print "Setting fd: %i to flags %s" % (fd, flags)

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
        fd_ops.append(
            self._create_op(
                syscall,
                {
                    'path': match.group(2),
                    'mode': match.group(1),
                }
            )
        )

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
        fd_ops.append(
            self._create_op(
                syscall,
                {
                    'path': match.group(3) + ':' + match.group(2),
                    'mode': match.group(1),
                }
            )
        )

    def add_close(self, syscall):
        if syscall['return_value'] != '0':
            return
        fd = int(SystemCallInfo.param_by_index(syscall, 0))
        try:
            fd_op = self._fd_operations_syscall(syscall, fd)
            fd_op['open'] = False
        except:
            print "fd %i not open" % fd

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

    def _fd_operations_syscall(self, syscall, fd):
        if fd not in self.fds[fd]:
            raise Exception("No open", "fd")
        for fd_op in self.fds[fd]:
            if fd_op['pid'] == syscall['PID']:
                return fd_op
        raise Exception("No open", "fd")


class PIDTracker(QObject):
    """ A class to track clone and exit system calls """
    def __init__(self):
        QObject.__init__(self)
        self.root_item = tree.TreeItem()
        self.root_item.pid = -1

    def add_clone(self, syscall):
        pid = int(syscall['return_value'])
        if pid < 0:
            return

        parent_pid = int(syscall['PID'])
        parent = tree.TreeUtil.get_item_by_pid(self.root_item, parent_pid)
        if parent is None:
            parent = tree.TreeItem(self.root_item)
            parent.pid = parent_pid

        child = tree.TreeItem(parent)
        child.pid = pid

        self.emit(QtCore.SIGNAL('pid_added'))


class SystemCallDecoder(QObject):
    def __init__(self):
        QObject.__init__(self)
        self.fd_tracker = FdTracker()
        self.pid_tracker = PIDTracker()

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
            elif name.startswith('fcntl'):
                self._decode_fcntl(syscall)
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
            elif name == 'getsockname':
                self._decode_base(syscall, ['file'])
            elif name == 'clone':
                self._decode_clone(syscall)
            elif name.startswith('exec'):
                self.fd_tracker.init_std(syscall['PID'])

        self.emit(QtCore.SIGNAL('syscall_decoded'))

    def _decode_base(self, syscall, description):
            params = str(syscall['parameters']).split(',')
            for index, desc in enumerate(description):
                if desc == 'file':
                    fd = int(SystemCallInfo.param_by_index(syscall, index))
                    if fd in self.fd_tracker.fds:
                        decoded_fd = str(self.fd_tracker.fd_path(fd))
                        if decoded_fd is not None:
                            params[index] = decoded_fd
            syscall['parameters_decoded'] = ','.join(params)

    def _decode_open(self, syscall):
        self.fd_tracker.add_open(syscall)

    def _decode_close(self, syscall):
        self.fd_tracker.add_close(syscall)
        self._decode_base(syscall, ['file'])

    def _decode_write(self, syscall):
        self.fd_tracker.add_write(syscall)
        self._decode_base(syscall, ['file'])

    def _decode_read(self, syscall):
        self._decode_base(syscall, ['file'])

    def _decode_fstat(self, syscall):
        self._decode_base(syscall, ['file'])

    def _decode_fcntl(self, syscall):
        self.fd_tracker.add_fcntl(syscall)
        self._decode_base(syscall, ['file'])

    def _decode_connect(self, syscall):
        self.fd_tracker.add_connect(syscall)

    def _decode_send(self, syscall):
        self._decode_base(syscall, ['file'])

    def _decode_socket(self, syscall):
        self.fd_tracker.add_socket(syscall)
        self._decode_base(syscall, ['file'])

    def _decode_clone(self, syscall):
        self.pid_tracker.add_clone(syscall)


class SystemCallModel(QAbstractTableModel):
    def __init__(self):
        QAbstractTableModel.__init__(self, None)
        self.syscalls = []

    def set_decoder(self, decoder):
        self.decoder = decoder

    def set_strace_runner(self, strace_runner):
        self.strace_runner = strace_runner
        self.connect(self.strace_runner,
            QtCore.SIGNAL('syscall_parsed'), self._slot_syscall_parsed)

    def rowCount(self, parent=None):
        return len(self.syscalls)

    def columnCount(self, parent=None):
        return len(SystemCallInfo.FIELDS)

    def data(self, index, role):
        line = self.syscalls[index.row()]

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
        self.syscalls = []

    def _syscall_failed(self, index):
        row = index.row()
        if len(self.syscalls) <= row:
            return False
        try:
            return_value = int(self.syscalls[row]['return_value'])
        except:
            return False

        return (return_value < 0)

    def _slot_syscall_parsed(self, syscall_info):
        self.syscalls.extend(syscall_info)
        self.reset()
        self.decoder.process(syscall_info)

class FdModel(QAbstractTableModel):
    def __init__(self):
        QAbstractTableModel.__init__(self, None)
        self.fds = None

    def set_decoder(self, decoder):
        self.decoder = decoder
        self.fds = self.decoder.fd_tracker.fds
        self.connect(self.decoder,
            QtCore.SIGNAL('syscall_decoded'), self._slot_syscall_decoded)
        self.reset()

    def set_strace_runner(self, strace_runner):
        self.strace_runner = strace_runner

    def rowCount(self, parent=None):
        if self.fds is None:
            return 0
        # FIXME This is totally suboptimal
        rows = 0
        for fd in self.fds.keys():
            rows = rows + len(self.fds[fd])
        return rows

    def columnCount(self, parent=None):
        return len(FdInfo.COLUMNS)

    def data(self, index, role):
        if self.fds is None or role != Qt.DisplayRole:
            return  QtCore.QVariant()

        # FIXME This is suboptimal and related to the way
        # we store fd info. It would be better to flatten
        # the structure
        rows = 0
        fd_info = {}
        for fd in self.fds.keys():
            num_fds = len(self.fds[fd])
            if  (rows + num_fds - 1) >= index.row():
                fd_info = self.fds[fd][(index.row() - rows)]
                break
            else:
                rows = rows + num_fds

        return fd_info[FdInfo.COLUMNS[index.column()]]

    def headerData(self, section, orientation, role):
        if role != Qt.DisplayRole:
            return QtCore.QVariant()

        if orientation == Qt.Horizontal:
            return FdInfo.FIELDS[section]
        else:
            return QtCore.QVariant()

    def clearData(self):
        pass


    def _slot_syscall_decoded(self):
        self.reset()


class SystemCallProxy(QtGui.QSortFilterProxyModel):
    def __init__(self, parent=None):
        super(SystemCallProxy, self).__init__(parent)
        self.pids_to_filter = []

    def slot_add_pid_filter(self, pids):
        self.pids_to_filter = pids
        self.reset()

    def filterAcceptsRow(self, source_row, source_parent):
        if not super(SystemCallProxy, self).filterAcceptsRow(source_row, source_parent):
            return False
        if self.pids_to_filter:
            row_pid = self.sourceModel().syscalls[source_row]['PID']
            if int(row_pid) in self.pids_to_filter:
                    return False
            return True
        else:
            return True

class PidTreeModel(QtCore.QAbstractItemModel):
    def __init__(self,  parent=None):
        super(PidTreeModel, self).__init__(parent)
        root = tree.TreeItem()
        root.pid = -1
        self.rootItem = root

    def set_decoder(self, decoder):
        self.decoder = decoder
        self.pid_tracker = decoder.pid_tracker
        self.rootItem = decoder.pid_tracker.root_item
        self.connect(self.pid_tracker,
            QtCore.SIGNAL('pid_added'), self._slot_pid_added)

    def _slot_pid_added(self):
        self.reset()

    def columnCount(self, parent):
        if parent.isValid():
            return parent.internalPointer().column_count()
        else:
            return self.rootItem.column_count()

    def data(self, index, role):
        if not index.isValid():
            return None
        if role != QtCore.Qt.DisplayRole:
            return None

        item = index.internalPointer()
        return QtCore.QVariant(item.pid)

    def flags(self, index):
         if not index.isValid():
             return QtCore.Qt.NoItemFlags

         return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return "PID"

        return None

    def index(self, row, column, parent):

        if row < 0 or column < 0 or row >= self.rowCount(parent) or column >= self.columnCount(parent):
            return QtCore.QModelIndex()

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QtCore.QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QtCore.QModelIndex()

        childItem = index.internalPointer()
        parentItem = childItem.parent

        if parentItem == self.rootItem:
            return QtCore.QModelIndex()

        return self.createIndex(parentItem.row(), 0, parentItem)

    def rowCount(self, parent):
        if parent.column() > 0:
            return 0

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        return parentItem.child_count()
