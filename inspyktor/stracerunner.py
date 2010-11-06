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

from PyQt4.QtCore import (
    QObject,
    QFile,
    QIODevice,
    QStringList,
    QFileSystemWatcher,
    SIGNAL)
from PyKDE4 import kdeui, kdecore
import re


class Parser():
    def __init__(self):
        self.regexp = re.compile(
            '^(?P<PID>[0-9]+)\s+(?P<time>[0-9]+\.[0-9]+) '
            '(?P<name>[a-z_0-9]+)\((?P<parameters>.*)\) += '
            '(?P<return_value>(?:[0-9]+)|(?:0x[0-9a-f]+)|(?:-[0-9]+)) '
            '(?P<return_comment>\(in.*\) )?'
            '(?P<errno>E[A-Z]+ .*)?<(?P<elapsed_time>[0-9]+\.[0-9]+)>')

    def parse_lines(self, lines):
        parsed_lines = []
        for line in lines:
            match = self.regexp.match(line)
            if match:
                parsed_info = match.groupdict()
                parsed_info['line'] = match.group()
                parsed_lines.append(parsed_info)
            else:
                print line
        return parsed_lines


class StraceRunner(QObject):
    def __init__(self):
        QObject.__init__(self)
        self._command = None
        self._running = False
        self._pid = None
        self._partial_line = ''
        self._parser = Parser()
        self._strace = None

    def set_trace_command(self, command, args=None):
        self._command = command
        if args is None:
            args = []
        self._args = args

    def trace_command(self):
        return self._command

    def trace_args(self):
        return self._args

    def set_pid(self, pid):
        self._pid = pid

    def pid(self):
        return self._pid

    def _prepare_trace(self):
        temp_file = kdecore.KTemporaryFile()
        temp_file.setAutoRemove(False)
        temp_file.open()
        temp_file_name = temp_file.fileName()
        temp_file.close()
        self._out_file = QFile(temp_file_name)
        self._out_file.open(QIODevice.ReadOnly | QIODevice.Text)

        kproc_args = []
        kproc_args.extend(['-o', temp_file_name, '-ttt', '-T', '-f'])
        if self.pid() is  None:
            kproc_args.append(self._command)
            kproc_args.extend(self.trace_args())
        else:
            kproc_args.extend(["-p", self.pid()])

        self._strace = kdecore.KProcess(self)
        self._strace.setProgram("/usr/bin/strace", kproc_args)
        print kproc_args

        # Create watcher for temporary ile as that's where strace
        # is oging to dump its output
        self._file_watcher = QFileSystemWatcher([temp_file_name], self)

        self.connect(self._strace,
            SIGNAL('finished(int,QProcess::ExitStatus)'),
            self._slot_process_finished)

        self.connect(self._file_watcher, SIGNAL('fileChanged (QString)'),
            self._slot_ready_read)

    def _slot_process_finished(self, exitCode, exitStatus):
        self._strace.deleteLater()
        self._file_watcher.deleteLater()
        self._strace = None
        print "Process finished with exit code %i" % exitCode

    def _slot_ready_read(self):
        lines = []
        while True:
            line = self._out_file.readLine()
            if line.isEmpty():
                break
            if not  str(line).endswith("\n"):
                self._partial_line = line
            else:
                lines.append(self._partial_line + line)
                self._partial_line = ''

        self.emit(SIGNAL('syscall_parsed'), self._parser.parse_lines(lines))

    def start_trace(self):
        self._prepare_trace()
        self._strace.setOutputChannelMode(kdecore.KProcess.MergedChannels)
        self._strace.start()

    def slot_trace_command(self):
        self.start_trace()

    def slot_stop_trace(self):
        if self._strace:
            self._strace.kill()
