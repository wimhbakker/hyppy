#!/usr/bin/python3
## clusters.py
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

def message(s):
    pass

class clusters:
    def __init__(self):
        self.cdict = {}
        self.count = 0

    # merge cluster b into a and delete cluster b
    # merge smallest cluster into largest
    # cluster number of a may change!!
    # number of remaining cluster is returned.
    def merge_clusters(self, a, b):
        if len(self.cdict[b])>len(self.cdict[a]):
            a, b = b, a
        for q in self.cdict[b]:
            q.cluster = a
        self.cdict[a].extend(self.cdict[b])
        del self.cdict[b]
        return a

    # add node q to cluster c
    def addto_cluster(self, c, q):
        self.cdict[c].append(q)
        q.cluster = c

    # start a new cluster and return cluster number
    def new_cluster(self, q):
        self.count = self.count+1
        self.cdict[self.count] = [q]
        q.cluster = self.count
        return self.count

    def do_cluster(self, q, dlist, lowThreshold, merge_level, im, message=message):
        k = list(dlist.keys())
        message("do_cluster: sorting keys...")
        k.sort(key=lambda x: getattr(x, 'area'), reverse=True)
        message("Clustering...")
        for i in range(len(k)):
            q1 = k[i]
            c1 = getattr(q1, 'cluster', None)
            if not c1:
                c1 = self.new_cluster(q1)
            if i % 1000 == 0:
                message('.')
            for q2 in dlist[q1]:
                c2 = getattr(q2, 'cluster', None)
                if c1 != c2 and q1.can_merge(q2, lowThreshold, merge_level, im):
                    if c2:
                        c1 = self.merge_clusters(c1, c2)
                    else:
                        self.addto_cluster(c1, q2)
        message('\n')
        message("%i clusters remaing" % len(self.cdict))
