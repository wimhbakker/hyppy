#!/usr/bin/python3
## quadtree.py
##
## Copyright (C) 2010 Wim Bakker
## 
## This program is free software: you can redistribute it and/or modify it
## under the terms of the GNU General Public License as published by the
## Free Software Foundation, version 3 of the License.
## 
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
## See the GNU General Public License for more details.
## 
## You should have received a copy of the GNU General Public License along
## with this program. If not, see <http://www.gnu.org/licenses/>.
## 
## Contact:
##     Wim Bakker, <bakker@itc.nl>
##     University of Twente, Faculty ITC
##     Hengelosestraat 99
##     7514 AE Enschede
##     Netherlands
##

from gosplit import *
import random

def message(s):
    pass

def area(t):
    x0, x1, y0, y1 = t
    return (x1-x0)*(y1-y0)

class QuadTree:
    node0 = None # ul
    node1 = None # ur
    node2 = None # ll
    node3 = None # lr
    isLeaf = True

    def __init__(self, x0, x1, y0, y1):
#        print "new node ", x0, x1, y0, y1
        self.x0, self.x1 = x0, x1
        self.y0, self.y1 = y0, y1
        self.area = area((x0, x1, y0, y1))

    def split_node(self, rough, arr):
        x0, x1 = self.x0, self.x1
        y0, y1 = self.y0, self.y1
        if (x1-x0 == 1) and (y1-y0 == 1):
            return
        if rough(arr, (x0, x1, y0, y1)): # put criterion for splitting here
            maxarea = 0
            optimal = None
            for midx, midy in gosplit((x0, x1, y0, y1)):
                subarea = 0
                if not midx:
                    t = (x0, x1, y0, midy)
                    if not rough(arr, t):
                        subarea = subarea + area(t)

                    t = (x0, x1, midy, y1)
                    if not rough(arr, t):
                        subarea = subarea + area(t)
                elif not midy:
                    t = (x0, midx, y0, y1)
                    if not rough(arr, t):
                        subarea = subarea + area(t)

                    t = (midx, x1, y0, y1)
                    if not rough(arr, t):
                        subarea = subarea + area(t)
                else:
                    t = (x0, midx, y0, midy)
                    if not rough(arr, t):
                        subarea = subarea + area(t)

                    t = (midx, x1, y0, midy)
                    if not rough(arr, t):
                        subarea = subarea + area(t)

                    t = (x0, midx, midy, y1)
                    if not rough(arr, t):
                        subarea = subarea + area(t)

                    t = (midx, x1, midy, y1)
                    if not rough(arr, t):
                        subarea = subarea + area(t)
                if subarea >= maxarea:
                    maxarea = subarea
                    optimal = midx, midy
                
            midx, midy = optimal
            if not midx: # split y
                self.node0 = QuadTree(x0, x1, y0, midy)
                self.node2 = QuadTree(x0, x1, midy, y1)
                self.node0.split_node(rough, arr)
                self.node2.split_node(rough, arr)
                self.isLeaf = False
            elif not midy: # split x
                self.node0 = QuadTree(x0, midx, y0, y1)
                self.node1 = QuadTree(midx, x1, y0, y1)
                self.node0.split_node(rough, arr)
                self.node1.split_node(rough, arr)
                self.isLeaf = False
            else: # split x and y
                self.node0 = QuadTree(x0, midx, y0, midy)
                self.node1 = QuadTree(midx, x1, y0, midy)
                self.node2 = QuadTree(x0, midx, midy, y1)
                self.node3 = QuadTree(midx, x1, midy, y1)
                self.node0.split_node(rough, arr)
                self.node1.split_node(rough, arr)
                self.node2.split_node(rough, arr)
                self.node3.split_node(rough, arr)
                self.isLeaf = False

    def count_leafs(self, n=0):
        if self.isLeaf:
            return n+1
        else:
            if not self.node0==None:
                n = self.node0.count_leafs(n)
            if not self.node1==None:
                n = self.node1.count_leafs(n)
            if not self.node2==None:
                n = self.node2.count_leafs(n)
            if not self.node3==None:
                n = self.node3.count_leafs(n)
            return n

    def dump_leafs(self, a, n=0, attrib='area'):
        if self.isLeaf:
            if attrib == 'id':
                value = id(self)
            elif attrib == 'random':
                value = random.randint(1, 255)
            elif attrib == 'randclust':
                random.seed(self.cluster)
                value = random.randint(1, 255)
            else:
                value = getattr(self, attrib, 0)
            a[self.y0:self.y1, self.x0:self.x1] = value
            return n+1
        else:
            if not self.node0==None:
                n = self.node0.dump_leafs(a, n, attrib=attrib)
            if not self.node1==None:
                n = self.node1.dump_leafs(a, n, attrib=attrib)
            if not self.node2==None:
                n = self.node2.dump_leafs(a, n, attrib=attrib)
            if not self.node3==None:
                n = self.node3.dump_leafs(a, n, attrib=attrib)
            return n

    def linear_list(self, d):
        if self.isLeaf:
            d[self] = []
        else:
            if self.node0:
                self.node0.linear_list(d)
            if self.node1:
                self.node1.linear_list(d)
            if self.node2:
                self.node2.linear_list(d)
            if self.node3:
                self.node3.linear_list(d)

    def adjacent(q1, q2):
        if (q1.x0 == q2.x1 or q1.x1 == q2.x0) and (q1.y0 < q2.y1 and q2.y0 < q1.y1):
            return True
        elif (q1.y0 == q2.y1 or q1.y1 == q2.y0) and (q1.x0 < q2.x1 and q2.x0 < q1.x1):
            return True
        else:
            return False
    
    def adjacency_list(self, d, message=message):
        k = list(d.keys())
        message("sorting...")
        k.sort(key=lambda x: getattr(x, 'area'), reverse=True)
        message("Building adjacency list...")
        for i in range(len(k)):
            q1 = k[i]
            if i % 100 == 0:
                message('.')
            for j in range(i+1, len(k)):
                q2 = k[j]
                if q1.adjacent(q2):
                    d[q1].append(q2)
                    #d[q2].append(q1)  # need to visit boundaries only once?
        message('\n')
        
    def can_merge(q1, q2, lowThreshold, merge_level, im):
        low_x  = max(q1.x0, q2.x0)
        high_x = min(q1.x1, q2.x1)
        low_y  = max(q1.y0, q2.y0)
        high_y = min(q1.y1, q2.y1)

        if   q1.x0 == q2.x1: # q2 left of q1
            return lowThreshold(im, (low_x, high_x, low_y, high_y),
                                merge_level, vert=False)
        elif q1.x1 == q2.x0: # q2 right of q1
            return lowThreshold(im, (low_x, high_x, low_y, high_y),
                                merge_level, vert=False)
        elif q1.y0 == q2.y1: # q2 below q1
            return lowThreshold(im, (low_x, high_x, low_y, high_y),
                                merge_level, vert=True)
        elif q1.y1 == q2.y0: # q2 above q1
            return lowThreshold(im, (low_x, high_x, low_y, high_y),
                                merge_level, vert=True)
        else:
            raise ValueError("nodes not adjacent")

    def in_quad(q, x, y):
        return (q.x0 <= x < q.x1) and (q.y0 <= y < q.y1)

    def find_quad(q, x, y):
        if q.node0 and q.node0.in_quad(x, y):
            return q.node0.find_quad(x, y)
        elif q.node1 and q.node1.in_quad(x, y):
            return q.node1.find_quad(x, y)
        elif q.node2 and q.node2.in_quad(x, y):
            return q.node2.find_quad(x, y)
        elif q.node3 and q.node3.in_quad(x, y):
            return q.node3.find_quad(x, y)
        elif q.in_quad(x, y):
            return q
        else:
            return None

    def adjacency_list2(self, d, message=message):
        message("Building adjacency list. Pass X...")
        for j in range(self.y0, self.y1):
            if j % 100 == 0:
                message('.')
            for i in range(self.x0, self.x1-1):
                q = self.find_quad(i, j)
                qx = self.find_quad(i+1, j)

                if q is not qx:
                    if q.area >= qx.area:
                        if qx not in d[q]:
                            d[q].append(qx)
                    else:
                        if q not in d[qx]:
                            d[qx].append(q)
        message('\n')

        message("Building adjacency list. Pass Y...")
        for j in range(self.y0, self.y1-1):
            if j % 100 == 0:
                message('.')
            for i in range(self.x0, self.x1):
                q = self.find_quad(i, j)
                qy = self.find_quad(i, j+1)

                if q is not qy:
                    if q.area >= qy.area:
                        if qy not in d[q]:
                            d[q].append(qy)
                    else:
                        if q not in d[qy]:
                            d[qy].append(q)
        message('\n')
