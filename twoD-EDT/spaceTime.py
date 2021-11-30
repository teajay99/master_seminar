import random
from panda3d.core import *
from direct.showbase.ShowBase import ShowBase
from direct.gui.DirectGui import *
from direct.interval.IntervalGlobal import *
from direct.task import Task

import trimesh
import schedule
import math

FACE_CLR = Vec4(1.0, 0.5, 0.0, 1.0)
LINE_CLR = Vec4(0.0, 0.0, 0.0, 1.0)

TETRAHEDRON = [[0, 1], [0, 2], [0, 3], [1, 2], [1, 3], [2, 3]]

NORMALIZE_SPEED = 5.0


class spaceTime:

    links = []
    vertices = {}

    freeVertices = []

    def __init__(self, mesh):
        self.triangles = [{'verts': [l[0], l[1], l[2]]} for l in mesh.faces]

        self.vertices = {}
        for i in range(mesh.vertices.shape[0]):
            self.vertices[i] = {
                'xyz':
                Vec3(mesh.vertices[i, 0], mesh.vertices[i, 1],
                     mesh.vertices[i, 2])
            }

        self.findNeighbours()

        self.last_task_time = 0

    def findNeighbours(self):

        #Find Neighbouring Triangles
        for i in range(len(self.triangles)):
            self.triangles[i]['neighbours'] = []
            for j in range(len(self.triangles)):
                commonCounter = 0
                for k in self.triangles[i]['verts']:
                    if k in self.triangles[j]['verts']:
                        commonCounter += 1
                if commonCounter == 2:
                    self.triangles[i]['neighbours'].append(j)
            if len(self.triangles[i]['neighbours']) != 3:
                print("Horrible Things have happened")

        #Find Neighbouring Vertices
        for i in self.vertices.keys():
            self.vertices[i]['neighbours'] = []
            for j in range(len(self.triangles)):
                if i in self.triangles[j]['verts']:
                    for k in self.triangles[j]['verts']:
                        if (k != i) and (not k
                                         in self.vertices[i]['neighbours']):
                            self.vertices[i]['neighbours'].append(k)

    def centerVertices(self):
        sum = Vec3(0., 0., 0.)
        for i in self.vertices.keys():
            sum += self.vertices[i]['xyz']
        sum /= len(self.vertices.items())
        for i in self.vertices.keys():
            self.vertices[i]['xyz'] -= sum

    def normalizeVertices(self, task):
        adj_order = list(self.vertices.keys())
        random.shuffle(adj_order)

        for i in adj_order:

            force = Vec3(0., 0., 0.)

            for j in self.vertices[i]['neighbours']:
                diff = self.vertices[i]['xyz'] - self.vertices[j]['xyz']
                force -= diff - diff.normalized()

            self.vertices[i]['xyz'] += force * (
                task.time - self.last_task_time) * NORMALIZE_SPEED

        #self.centerVertices()

        self.last_task_time = task.time

        return Task.cont

    def findCommonNeighbours(self, i1, i2):
        out = []
        for i in self.vertices[i1]['neighbours']:
            for j in self.vertices[i2]['neighbours']:
                if i == j:
                    out.append(i)
        return out

    def pachner13(self):

        #pick random link to flip
        t = random.randrange(len(self.triangles))

        if len(self.freeVertices) != 0:
            newVertex = self.freeVertices.pop()
        else:
            newVertex = max(self.vertices.keys()) + 1

        self.vertices[newVertex] = {
            'xyz':
            (self.vertices[self.triangles[t]['verts'][0]]['xyz'] +
             self.vertices[self.triangles[t]['verts'][1]]['xyz'] +
             self.vertices[self.triangles[t]['verts'][2]]['xyz']) * (1.0 / 2.8)
        }

        oldT = [v for v in self.triangles[t]['verts']]

        for i in range(2):
            newT = [v for v in oldT]
            newT[i] = newVertex
            self.triangles.append({'verts': [v for v in newT]})

        self.triangles[t]['verts'][2] = newVertex

        self.findNeighbours()

        return True

    def pachner31(self):

        #find all vertices with three neighbours
        triples = []

        for t in range(len(self.triangles)):
            for i in self.triangles[t]['neighbours']:
                for j in self.triangles[i]['neighbours']:
                    if j in self.triangles[t]['neighbours']:
                        triples.append([i, j, t])


        if len(triples) == 0:
            return False
        v = random.choice(triples)
        v.sort()


        commonVert = 0
        commonVertCounter = 0

        for i in self.triangles[v[0]]['verts']:
            if (i in self.triangles[v[1]]['verts']) and (
                    i in self.triangles[v[2]]['verts']):
                commonVert = i
                commonVertCounter += 1

        if commonVertCounter != 1:
            return False

        if not (len(self.vertices[commonVert]['neighbours']) == 3):
            return False

        self.triangles[v[0]]['verts'] = [
            k for k in self.vertices[commonVert]['neighbours']
        ]
        self.triangles.pop(v[2])
        self.triangles.pop(v[1])

        del self.vertices[commonVert]
        self.freeVertices.append(commonVert)

        self.findNeighbours()

        return True

    def pachner22(self):

        #pick random triangle
        t1 = random.randrange(len(self.triangles))
        #random neighbour triangle
        t2 = self.triangles[t1]['neighbours'][random.randrange(3)]

        opposingVerts = []
        sharedVerts = []

        for i in self.triangles[t1]['verts']:
            if not (i in self.triangles[t2]['verts']):
                opposingVerts.append(i)
            else:
                sharedVerts.append(i)

        for i in self.triangles[t2]['verts']:
            if not (i in self.triangles[t1]['verts']):
                opposingVerts.append(i)

        #Check whether rotated link already exists
        if opposingVerts[0] in self.vertices[opposingVerts[1]]['neighbours']:
            return False

        self.triangles[t1]['verts'] = [
            opposingVerts[0], opposingVerts[1], sharedVerts[0]
        ]
        self.triangles[t2]['verts'] = [
            opposingVerts[0], opposingVerts[1], sharedVerts[1]
        ]

        self.findNeighbours()

        return True

    def start_metropolis(self):
        self.metro_job = schedule.every(0.1).seconds.do(
            self.make_metropolis_step)

    def make_metropolis_step(self):

        N = (2 / 3) * len(self.links)

        steps = [self.pachner13, self.pachner22, self.pachner31]
        steps[random.randrange(3)]()

    def stop_metropolis(self):
        schedule.cancel_job(self.metro_job)

    def get3DGeometry(self):
        vtx_fmt = GeomVertexFormat.get_v3c4()

        vtx_data = GeomVertexData("manifold_data", vtx_fmt, Geom.UH_static)

        vtx_writer = GeomVertexWriter(vtx_data, "vertex")
        face_clr_writer = GeomVertexWriter(vtx_data, "color")

        for i in range(max(self.vertices.keys()) + 1):
            if i in self.vertices.keys():
                vtx_writer.add_data3(self.vertices[i]["xyz"])
            else:
                vtx_writer.add_data3(0, 0, 0)
            #line_clr_writer.add_data4(LINE_CLR)
            face_clr_writer.add_data4(FACE_CLR)

        prim = GeomTriangles(Geom.UH_static)

        for t in self.triangles:
            prim.add_vertices(t['verts'][0], t['verts'][1], t['verts'][2])
            prim.add_vertices(t['verts'][0], t['verts'][2], t['verts'][1])

        geom = Geom(vtx_data)
        geom.add_primitive(prim)
        node = GeomNode("space_time")
        node.add_geom(geom)
        spacetime = NodePath(node)

        return spacetime
