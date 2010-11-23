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

class TreeItem:
    def __init__(self, parent=None):
        self.childItems = []
        self.pid = None
        self.state = None
        self.cmd_line = ''
        self.parent = parent
        if parent is not None:
            parent.append_child(self)

    def append_child(self, child):
        self.childItems.append(child)

    def child(self, row):
        if row >= 0 and row < len(self.childItems):
            return self.childItems[row]
        else:
            return None

    def child_count(self):
        return len(self.childItems)

    def row(self):
        if self.parent is not None:
            return self.parent.childItems.index(self)
        else:
            return 0

    def column_count(self):
        return 2


    def data(self):
        return 1

class TreeUtil:
    @staticmethod
    def get_item_by_pid(root, pid):
        if root is None:
            return None
        toSearch = [root]
        while len(toSearch) > 0:
            node = toSearch.pop(0)
            if node.pid == pid:
                return node
            toSearch.extend(node.childItems)
        return None
