#!/usr/bin/env python3

from QPanda3D.Panda3DWorld import Panda3DWorld
from QPanda3D.QPanda3DWidget import QPanda3DWidget
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QDockWidget, QVBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import Qt

from panda3d.core import *
from direct.showbase.ShowBase import ShowBase
from direct.gui.DirectGui import *
from direct.interval.IntervalGlobal import *

import trimesh
import schedule
import sys
import spaceTime
#import nav

from ManifoldRendering import ManifoldWorld, QManifoldDisplay


class controlWidget(QDockWidget):
    def __init__(self, manifoldworld, spacetime, *args, **kwargs):
        QDockWidget.__init__(self, *args, **kwargs)

        self.world = manifoldworld
        self.spacetime = spacetime

        self.vbox_layout = QVBoxLayout()
        self.vbox_layout.addStretch()
        self.vbox_layout.setDirection(QVBoxLayout.BottomToTop)

        self.reset_btn = QPushButton("Reset")
        self.reset_btn.clicked.connect(self.evnt_reset_clicked)

        self.start_stop = QPushButton("Randomize")
        self.start_stop.clicked.connect(self.evnt_start_stop_clicked)

        self.pachner_31 = QPushButton("Pachner (3,1)")
        self.pachner_31.clicked.connect(self.evnt_pachner_31_clicked)
        self.pachner_13 = QPushButton("Pachner (1,3)")
        self.pachner_13.clicked.connect(self.evnt_pachner_13_clicked)
        self.pachner_22 = QPushButton("Pachner (2,2)")
        self.pachner_22.clicked.connect(self.evnt_pachner_22_clicked)

        self.vbox_layout.addWidget(self.reset_btn)
        self.vbox_layout.addWidget(self.pachner_31)
        self.vbox_layout.addWidget(self.pachner_13)
        self.vbox_layout.addWidget(self.pachner_22)
        self.vbox_layout.addWidget(self.start_stop)

        self.control_area = QWidget()
        self.control_area.setLayout(self.vbox_layout)

        self.setWidget(self.control_area)

        self.metro_running = False

        self.world.task_mgr.add(self.normalize_loop, 'norm_loop')

    def normalize_loop(self, task):
        out = self.spacetime.normalizeVertices(task)
        self.world.remove_space_time()
        self.world.render_space_time(self.spacetime.get3DGeometry())
        schedule.run_pending()
        return out
        1

    def evnt_reset_clicked(self, e):
        self.world.task_mgr.remove('norm_loop')
        self.world.remove_space_time()
        self.spacetime = spaceTime.spaceTime(trimesh.creation.icosphere(
            1, 4.0))
        self.world.render_space_time(self.spacetime.get3DGeometry())
        self.world.task_mgr.add(self.normalize_loop, 'norm_loop')

    def evnt_pachner_31_clicked(self, e):
        self.spacetime.pachner31()

    def evnt_pachner_13_clicked(self, e):
        self.spacetime.pachner13()

    def evnt_pachner_22_clicked(self, e):
        self.spacetime.pachner22()

    def evnt_start_stop_clicked(self, e):
        if self.metro_running:
            self.start_stop.setText("Start Metropolis")
            self.spacetime.stop_metropolis()
            self.metro_running = False
        else:
            self.spacetime.start_metropolis()
            self.start_stop.setText("Stop Metropolis")
            self.metro_running = True


if __name__ == "__main__":

    st = spaceTime.spaceTime(trimesh.creation.icosphere(1, 4.0))

    world = ManifoldWorld(st.get3DGeometry())

    app = QApplication(sys.argv)
    appw = QMainWindow()
    appw.setWindowTitle("2D EDT")
    appw.setGeometry(50, 50, 800, 600)

    pandaWidget = QManifoldDisplay(world)
    appw.setCentralWidget(pandaWidget)
    control = controlWidget(world, st)
    appw.addDockWidget(Qt.LeftDockWidgetArea, control)
    control.evnt_reset_clicked(None)

    appw.show()

    sys.exit(app.exec_())
