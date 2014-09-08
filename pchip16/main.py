import OpenGL
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import random

import sys

class PChip16Window:

    def __init__(self):
        self.main()

    def init_gl(self):
        glClearColor(0.0, 0.0, 0.0, 0.0)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, self.width, self.height, 0, 0, 1)
        glMatrixMode(GL_MODELVIEW)
        glDisable(GL_DEPTH_TEST)
        glClear(GL_COLOR_BUFFER_BIT)

    def draw_gl_scene(self):
        glBegin(GL_POINTS)
        for x in range(0, 319):
            for y in range(0, 239):
                if x % 15 == 0 or y % 15 == 0:
                    glColor3f(random.random(), random.random(), random.random())
                glVertex2f(x, y)
        glEnd()
        glutSwapBuffers()

    def reshape(self, width, height):
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, width, height, 0, 0, 1)
        glMatrixMode(GL_MODELVIEW)
        #glDisable(GL_DEPTH_TEST)
        #glClear(GL_COLOR_BUFFER_BIT)

    def keyPressed(self, key, x, y):
        # If escape is pressed, kill everything.
        if key == '\x1b':
            sys.exit()
        elif key == 'm':
            print "Now meteoring otherwise peaceful teapot"

    def keySpecialPressed(self, key, x, y):
        if key == 100:
            print 'Left'
        if key == 101:
            print 'Up'
        if key == 102:
            print 'Right'
        if key == 103:
            print 'Down'

    def main(self):
        ## Create window
        self.width = 320
        self.height = 240
        glutInit(sys.argv)
        #glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE | GLUT_DEPTH)
        glutInitWindowSize(self.width, self.height)
        # centering the window
        glutInitWindowPosition((glutGet(GLUT_SCREEN_WIDTH)-self.width)/2,(glutGet(GLUT_SCREEN_HEIGHT)-self.height)/2)
        glutCreateWindow("pchip16 (press esc to quit)")
        ## End create window

        ## Setup display and key event handlers
        glutDisplayFunc(self.draw_gl_scene)
        glutReshapeFunc(self.reshape)
        glutIdleFunc(self.draw_gl_scene)
        glutKeyboardFunc(self.keyPressed)
        glutSpecialFunc(self.keySpecialPressed)
        ## end setup

        self.init_gl()

        ## Start the infinity loop
        glutMainLoop()
        ## end infinity loop

if __name__ == "__main__":
    PChip16Window()
