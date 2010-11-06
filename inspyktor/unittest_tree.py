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

from inspyktor import tree
import unittest

class TestTree(unittest.TestCase):
    def setUp(self):
        root = tree.TreeItem()
        root.pid = 1
        leaf2 = tree.TreeItem(root)
        leaf2.pid = 2
        leaf3 = tree.TreeItem(root)
        leaf3.pid = 3
        leaf4 = tree.TreeItem(leaf2)
        leaf4.pid = 4
        self.root = root

    def test_tree(self):
        root = self.root
        self.assertTrue(root.pid == 1)
        self.assertTrue(root.child_count() == 2)

        leaf2 = root.child(0)
        self.assertTrue(leaf2.child_count() == 1)
        self.assertTrue(leaf2.pid == 2)
        self.assertTrue(leaf2.parent.pid == 1)

        leaf3 = root.child(1)
        self.assertTrue(leaf3.pid == 3)
        self.assertTrue(leaf3.parent.pid == 1)

        leaf4 = leaf2.child(0)
        self.assertTrue(leaf4.pid == 4)
        self.assertTrue(leaf4.parent.pid == 2)

        self.assertTrue(root.row() == 0)
        self.assertTrue(leaf2.row() == 0)
        self.assertTrue(leaf3.row() == 1)
        self.assertTrue(leaf4.row() == 0)



    def test_tree_util(self):
        for i in  range(1, 5):
            node = tree.TreeUtil.get_item_by_pid(self.root, i)
            self.assertTrue(node.pid == i)
