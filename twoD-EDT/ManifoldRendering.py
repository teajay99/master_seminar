from QPanda3D.Panda3DWorld import Panda3DWorld
from QPanda3D.QPanda3DWidget import QPanda3DWidget
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow

from panda3d.core import *
from direct.showbase.ShowBase import ShowBase
from direct.gui.DirectGui import *
from direct.interval.IntervalGlobal import *

from time import sleep


class ManifoldWorld(Panda3DWorld):
    def __init__(self, spacetime, *args, **kwargs):
        Panda3DWorld.__init__(self, *args, **kwargs)

        self.mouse_pos = Point2(0, 0)

        light_node = PointLight("point_light")
        light_node.set_color((3., 3., 3., 1.))
        light_node.setShadowCaster(True, 1024, 1024)

        self.light = self.camera.attach_new_node(light_node)
        self.light.set_pos(20., 50., 20.)


        self.render.setAntialias(AntialiasAttrib.MAuto)
        #self.render.setShaderAuto()


        #myMaterial = Material()
        #myMaterial.setShininess(5.0) # Make this material shiny
        #myMaterial.setAmbient((0, 0, 1, 1)) # Make this material blue

        self.pivot = self.render.attach_new_node("pivot")

        self.orbit_speed = (0.5, 0.5)
        self.target_hpr = (0, 0, 0)
        self.cam_pos_y = -10

        self.move_weights = [1.0,1.0,1.0]

        self.render_space_time(spacetime)

    def render_space_time(self, spacetime):
        self.spacetime = spacetime
        self.spacetime.reparent_to(self.pivot)
        self.lines = self.spacetime.copy_to(self.pivot)
        self.lines.node().modify_geom(0).make_lines_in_place()
        self.lines.set_render_mode_thickness(3)
        self.lines.set_color(1., 1., 1.)
        self.spacetime.set_light(self.light)
        self.cam_target = self.spacetime.attach_new_node("camera_target")
        self.cam_target.set_pos(Point3(0, 0, 0))
        self.cam_target.set_hpr(*self.target_hpr)
        self.cam.reparent_to(self.cam_target)
        self.cam.set_pos(0, self.cam_pos_y, 0)

    def remove_space_time(self):
        self.pivot.getChildren().detach()
        self.cam_target.getChildren().detach()

    def set_mouse_pos_info(self, p):
        self.mouse_pos = p

    def start_orbiting(self, w, h, x, y):

        self.mouse_prev = Point2(x, y)
        self.task_mgr.add(self.orbit, "orbit")

    def stop_orbiting(self):

        self.task_mgr.remove("orbit")

    def orbit(self, task):
        """
        Orbit the camera about its target point by offsetting the orientation
        of the target node with the mouse motion.

        """

        speed_x, speed_y = self.orbit_speed
        d_h, d_p = (self.mouse_pos - self.mouse_prev)
        d_h *= speed_x
        d_p *= speed_y
        target = self.cam_target
        self.target_hpr = target.get_h() - d_h, target.get_p() + d_p, 0.
        target.set_hpr(*self.target_hpr)
        self.mouse_prev = self.mouse_pos

        return task.cont

    def zoom_step_in(self):
        target_dist = self.cam.get_y()
        self.cam_pos_y += -target_dist * .1
        self.cam.set_pos(0, self.cam_pos_y, 0)

    def zoom_step_out(self):
        target_dist = self.cam.get_y()
        self.cam_pos_y += target_dist * .1
        self.cam.set_pos(0, self.cam_pos_y, 0)


class QManifoldDisplay(QPanda3DWidget):
    def __init__(self, *args, **kwargs):
        QPanda3DWidget.__init__(self, *args, **kwargs)

        #self.setMouseTracking(True)

    def wheelEvent(self, event):
        if event.angleDelta().y() < 0:
            self.panda3DWorld.zoom_step_out()
        else:
            self.panda3DWorld.zoom_step_in()

    def mouseMoveEvent(self, event):
        self.panda3DWorld.set_mouse_pos_info(Point2(event.x(), event.y()))

    def mousePressEvent(self, event):
        self.panda3DWorld.start_orbiting(self.width(), self.height(),
                                         event.x(), event.y())

    def mouseReleaseEvent(self, event):
        self.panda3DWorld.stop_orbiting()

    def getPandaCoords():
        1
