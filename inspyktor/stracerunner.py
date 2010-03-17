#! /usr/bin/env python
# Copyright (c) 2010 Javier Uruen (juruen@warp.es)
# Licensed under the terms of the MIT license

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
            '^([0-9]+\.[0-9]+) ([a-z_0-9]+)\((.*)\) += '
            '((?:[0-9]+)|(?:0x[0-9a-f]+)|(?:-[0-9]+)) '
            '(E[A-Z]+ .*)?<([0-9]+\.[0-9]+)>')

    def parse_lines(self, lines):
        parsed_lines = []
        for line in lines:
            match = self.regexp.match(line)
            if match:
                parsed_info = {}
                parsed_info['line'] = match.group()
                parsed_info['time'] = match.group(1)
                parsed_info['name'] = match.group(2)
                parsed_info['parameters'] = match.group(3)
                parsed_info['return_value'] = match.group(4)
                parsed_info['errno'] = match.group(5)
                parsed_info['elapsed_time'] = match.group(6)
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
        kproc_args.extend(['-o', temp_file_name, '-ttt', '-T'])
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
            self.slot_process_finished)

        self.connect(self._file_watcher, SIGNAL('fileChanged (QString)'),
            self.slot_ready_read)

    def slot_process_finished(self, exitCode, exitStatus):
        self._strace.deleteLater()
        self._file_watcher.deleteLater()
        print "Process finished with exit code %i" % exitCode

    def slot_ready_read(self):
        line = self._out_file.readLine()
        lines = []

        while not line.isEmpty():
            line = self._out_file.readLine()
            lines.append(self._partial_line + line)
            self._partial_line = ''

        if len(lines) > 0:
            last_line = lines[-1]
            if len(last_line) > 0 and last_line[-1] == "\n":
                        self._partial_line = lines.pop(-1)

        self.emit(SIGNAL('syscall_parsed'), self._parser.parse_lines(lines))

    def slot_trace_command(self):
        self._prepare_trace()
        self._strace.setOutputChannelMode(kdecore.KProcess.MergedChannels)
        self._strace.start()
