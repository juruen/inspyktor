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

from inspyktor import systemcall
import unittest

class TestFdTracker(unittest.TestCase):
    def setUp(self):
        self.fd_tracker = systemcall.FdTracker()

    def test_add_open(self):
        syscall = {
            'return_value':  3,
            'parameters': '"/foo/bar", O_RDONLY',
            'PID': 1,
            'time': '1.0'
        }

        self.fd_tracker.add_open(syscall);
        self.assertEqual(len(self.fd_tracker.fds.keys()), 1)

    def test_init_std(self):
        self.fd_tracker.init_std(1);
        self.assertEqual(len(self.fd_tracker.fds.keys()), 3)
        self.fd_tracker.init_std(2);
        self.assertEqual(len(self.fd_tracker.fds.keys()), 3)
        for i in range(3):
            self.assertTrue(len(self.fd_tracker.fds[i]), 2)

    def test_add_write(self):
        # Test exception is raised if fd is not found
        syscall = {
            'return_value':  100,
            'parameters': '1, "foo", 3',
            'PID': 1,
            'time': '1.0'
        }
        self.assertRaises(
            systemcall.FdNotOpen,
            self.fd_tracker.add_write,
            syscall
        )

        self._add_files()

        # Write on fd 3 from PID 1
        write_1_syscall = {
            'return_value':  100,
            'parameters': '3, "foo", 100',
            'PID': 1,
            'time': '1.0'
        }
        self.fd_tracker.add_write(write_1_syscall)
        self.assertEqual(self.fd_tracker.fds[3][0]['write_bytes_success'], 100)
        self.assertEqual(self.fd_tracker.fds[3][0]['write_bytes_attempt'], 100)

        # Write on fd 3 from PID 2
        write_2_syscall = {
            'return_value':  200,
            'parameters': '3, "foo", 250',
            'PID': 2,
            'time': '1.0'
        }
        self.fd_tracker.add_write(write_2_syscall)
        self.assertEqual(self.fd_tracker.fds[3][1]['write_bytes_success'], 200)
        self.assertEqual(self.fd_tracker.fds[3][1]['write_bytes_attempt'], 250)

    def test_add_fcntl(self):
        self._add_files()
        syscall = {
            'return_value':  1,
            'parameters': '3, f_setfd, fd_cloexec',
            'PID': 2,
            'time': '1.0'
        }
        self.fd_tracker.add_fcntl(syscall)
        self.assertTrue(self.fd_tracker.fds[3][1]['close_on_exec'])

    def test_add_close(self):
        # Test exception is raised if fd is not found
        syscall = {
            'return_value':  '0',
            'parameters': '70',
            'PID': 1,
            'time': '1.0'
        }
        self.assertRaises(
            systemcall.FdNotOpen,
            self.fd_tracker.add_close,
            syscall
        )

        self._add_files()
        syscall_close = {
            'return_value': '0',
            'parameters': '3',
            'PID': 2,
            'time': '1.0'
        }
        self.fd_tracker.add_close(syscall_close)
        self.assertFalse(self.fd_tracker.fds[3][1]['open'])

    def test_add_connect(self):

    def test_fd_path(self):
        self.assertRaises(
            systemcall.FdNotOpen,
            self.fd_tracker.fd_path,
            1,
            4
        )
        self._add_files()
        self.assertEqual(
            self.fd_tracker.fd_path(1, 3),
            '"/foo/bar1"'
        )
        self.assertEqual(
            self.fd_tracker.fd_path(2, 3),
            '"/foo/bar2"'
        )


    def _add_files(self):
        """ Add several files to the tracker """
        self.fd_tracker.init_std(1);
        self.fd_tracker.init_std(2);

        files_to_add= [
            {
                'return_value':  3,
                'parameters': '"/foo/bar1", O_WRONLY',
                'PID': 1,
                'time': '1.0',
            },
            {
                'return_value':  3,
                'parameters': '"/foo/bar2", O_WRONLY',
                'PID': 2,
                'time': '1.0',

            },
            {
                'return_value':  4,
                'parameters': '"/foo/bar3", O_WRONLY',
                'PID': 2,
                'time': '1.0',

            }
        ]
        for syscall in files_to_add:
            self.fd_tracker.add_open(syscall);
