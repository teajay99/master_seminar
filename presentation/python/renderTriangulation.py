#!/usr/bin/env python3

import numpy as np
import fresnel
import matplotlib
import matplotlib.pyplot as plt
import PIL
import sys
import os
import math
import sympy as sp

SAMPLES = 128
LIGHT_SAMPLES = 32
RESOLUTION = 800
#SAMPLES = 16
#LIGHT_SAMPLES = 10
#RESOLUTION = 100
ORIENTATION = [0.975528, 0.154508, -0.154508, -0.024472]

PHI = (np.sqrt(5) + 1) / 2

#441963

platonic_solid_vertices = {
    'Tetrahedron':
    [[k[0] * 1.8, k[1] * 1.8, k[2] * 1.8]
     for k in [[0.0, 0.0, 0.612372], [-0.288675, -0.5, -0.204124],
               [-0.288675, 0.5, -0.204124], [0.57735, 0.0, -0.204124]]],
    'Cube': [[k[0] * 1.3, k[1] * 1.3, k[2] * 1.3]
             for k in [[-0.5, -0.5, -0.5], [-0.5, -0.5, 0.5],
                       [-0.5, 0.5, -0.5], [-0.5, 0.5, 0.5], [0.5, -0.5, -0.5],
                       [0.5, -0.5, 0.5], [0.5, 0.5, -0.5], [0.5, 0.5, 0.5]]],
    'Octahedron': [[k[0] * 1.6, k[1] * 1.6, k[2] / 1.6]
                   for k in [[-0.707107, 0.0, 0.0], [0.0, 0.707107, 0.0],
                             [0.0, 0.0, -0.707107], [0.0, 0.0, 0.707107],
                             [0.0, -0.707107, 0.0], [0.707107, 0.0, 0.0]]],
    'Dodecahedron':
    [[k[0] / 1.4, k[1] / 1.4, k[2] / 1.4]
     for k in [[-1.37638, 0.0, 0.262866], [1.37638, 0.0, -0.262866],
               [-0.425325, -1.30902, 0.262866], [-0.425325, 1.30902, 0.262866],
               [1.11352, -0.809017, 0.262866], [1.11352, 0.809017, 0.262866],
               [-0.262866, -0.809017, 1.11352], [-0.262866, 0.809017, 1.11352],
               [-0.688191, -0.5, -1.11352], [-0.688191, 0.5, -1.11352],
               [0.688191, -0.5, 1.11352], [0.688191, 0.5, 1.11352],
               [0.850651, 0.0, -1.11352], [-1.11352, -0.809017, -0.262866],
               [-1.11352, 0.809017, -0.262866], [-0.850651, 0.0, 1.11352],
               [0.262866, -0.809017, -1.11352], [0.262866, 0.809017, -1.11352],
               [0.425325, -1.30902, -0.262866], [0.425325, 1.30902, -0.262866]]
     ],
    'Icosahedron':
    [[k[0] * 1.15, k[1] * 1.15, k[2] * 1.15] for k in
     [[0.0, 0.0, -0.951057], [0.0, 0.0, 0.951057], [-0.850651, 0.0, -0.425325],
      [0.850651, 0.0, 0.425325], [0.688191, -0.5, -0.425325],
      [0.688191, 0.5, -0.425325], [-0.688191, -0.5, 0.425325],
      [-0.688191, 0.5, 0.425325], [-0.262866, -0.809017, -0.425325],
      [-0.262866, 0.809017, -0.425325], [0.262866, -0.809017, 0.425325],
      [0.262866, 0.809017, 0.425325]]],
}


def removeDulicates(points):
    out = []

    for p in points:
        found = False
        for q in out:
            matches = True
            for i in range(3):
                if np.abs(q[i] - p[i]) > 1e-8:
                    matches = False
            if matches == True:
                found = True
                break
        if found is False:
            out.append(p)

    return out


def getSubdivs(v1, v2, v3, subdivs):
    a = v1
    b = v2 - v1
    c = v3 - v1

    rate = 1.0 / (subdivs + 1)

    out = []

    for i in range(subdivs + 2):
        for j in range(subdivs + 2):
            if i + j < subdivs + 2:
                out.append(a + (i * rate * b) + (j * rate * c))
    return out


def getIcoVertices(subdivs=0):
    verts = []
    for i in range(-1, 2, 2):
        for j in range(-1, 2, 2):
            verts.append(np.array([0, i, j * PHI]))
            verts.append(np.array([i, j * PHI, 0]))
            verts.append(np.array([j * PHI, 0, i]))

    verts = [0.9*v / np.linalg.norm(v) for v in verts]

    minDist = 10
    for v in verts[1:]:
        dist = np.linalg.norm(v - verts[0])
        if dist < minDist:
            minDist = dist

    newVerts = []

    for v1 in verts:
        for v2 in verts:
            for v3 in verts:
                if (np.abs(np.linalg.norm(v1 - v2) - minDist) < 1e-8) and (
                        np.abs(np.linalg.norm(v1 - v3) - minDist) < 1e-8) and (
                            np.abs(np.linalg.norm(v2 - v3) - minDist) < 1e-8):
                    newVerts.extend(getSubdivs(v1, v2, v3, subdivs))

    for i in range(len(newVerts)):
        newVerts[i] += 0.1 * newVerts[i] / np.linalg.norm(newVerts[i])

    verts.extend(newVerts)
    return removeDulicates(verts)


def render_triangulation(vertices, fname):
    scene = fresnel.Scene(fresnel.Device("cpu"))
    scene.lights = fresnel.light.rembrandt()
    #scene.lights = fresnel.light.lightbox()

    cmap = matplotlib.cm.get_cmap('tab10')

    poly_info = fresnel.util.convex_polyhedron_from_vertices(vertices)
    geometry = fresnel.geometry.ConvexPolyhedron(scene,
                                                 poly_info,
                                                 position=[2.3, 0, 0],
                                                 orientation=ORIENTATION,
                                                 outline_width=0.01)
    geometry.material = fresnel.material.Material(
        color=fresnel.color.linear([1.4 * 0.65, 1.4 * 0.15, 1.4 * 0.09]))

    geometry.outline_material = fresnel.material.Material(color=(0., 0., 0.),
                                                          roughness=0.1,
                                                          metal=1.0)

    geometry = fresnel.geometry.Sphere(scene, position=[0, 0, 0], radius=1.0)

    geometry.material = fresnel.material.Material(
        color=fresnel.color.linear([2.3 * 0.16, 2.3 * 0.21, 2.3 * 0.34]))

    scene.camera = fresnel.camera.Orthographic.fit(scene,
                                                   view='front',
                                                   margin=0.1)
    out = fresnel.pathtrace(scene,
                            samples=SAMPLES,
                            light_samples=LIGHT_SAMPLES,
                            w=RESOLUTION * 2,
                            h=RESOLUTION)
    PIL.Image.fromarray(out[:], mode='RGBA').save(fname)


def getSpherePoints(N):
    def getCartesianCoords(t, p):
        return [
            math.sin(t) * math.cos(p),
            math.sin(t) * math.sin(p),
            math.cos(t)
        ]

    out = [[0, 0, 0] for i in range(N)]

    for n in range(N):
        t = math.acos(1 - ((2 * (n)) / (N)))
        p = 2 * sp.pi * sp.Mod((n) * ((1 - sp.sqrt(5)) / 2), 1)
        p = float(sp.N(p, 20))
        out[n] = getCartesianCoords(t, p)

    return out


#render_triangulation(getSpherePoints(100), "../pics/triangulation-fib.png")
render_triangulation(getIcoVertices(1), "../pics/triangulation-ico.png")
