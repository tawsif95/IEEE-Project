import os
import sys
import threading
import urllib.request

import picamera
import socket
import time
from umdieeepb import piprint
from umdieeepb.engine.camera import PhotoBoothCameraEngine
from umdieeepb.engine.loading import PhotoBoothLoadingEngine
from umdieeepb.engine.preview import PhotoBoothPreviewEngine
from umdieeepb.engine.processing import PhotoBoothProcessingLoadingEngine
from umdieeepb.engine.frames import PhotoBoothFramesEngine
from umdieeepb.engine.printopt import PhotoBoothPrintOptEngine
from umdieeepb.engine.printing import PhotoBoothPrintingEngine

from PyQt5 import QtCore
#watercolor
class PhotoBoothEngine(QtCore.QObject):
    def __init__(self):
        QtCore.QObject.__init__(self)
        
        self.loading_eng = PhotoBoothLoadingEngine()
        self.camera_eng = PhotoBoothCameraEngine()
        self.preview_eng = PhotoBoothPreviewEngine()
        self.proc_eng = PhotoBoothProcessingLoadingEngine()
        self.frames_eng = PhotoBoothFramesEngine()
        self.printopt_eng = PhotoBoothPrintOptEngine()
        self.printing_eng = PhotoBoothPrintingEngine()
        
        # States:
        #   0 = Loading/Setup (maybe increment this, logo = 1, this = 1... once all of this is done)
        #   1 = Camera / Live Filter Selection Screen
        #   2 = Preview Picture, ask for retake if necessary
        #   3 = Processing Photo Previews (for borders)
        #   4 = Preview and Select Picture Borders
        #   5 = Printing Options (how many?)
        #   6 = Printing Screen (delay X seconds)
        self.pbstate = 0
        
        self.stopnow = False
        
        self.running = True
        self.thread = threading.Thread(target=self.main)
        self.thread.start()
        
        self.signalmap = {
                            0:
                                {
                                    "url":    "qml/loading.qml",
                                    "engine": self.loading_eng,
                                    "master_signals":
                                        {
                                            self.on_status:     self.loading_eng.on_status
                                        },
                                    "method_signals":
                                        {
                                            self.loading_eng.on_status:     "status",
                                        },
                                    "internal_signals":
                                        {
                                            self.loading_eng.on_change_screen:       self.change_screen,
                                        },
                                },
                            1:
                                {
                                    "url":    "qml/camera.qml",
                                    "engine": self.camera_eng,
                                    "master_signals":
                                        {
                                            self.on_status:                self.camera_eng.on_status,
                                            self.on_update_filter_preview: self.camera_eng.on_update_filter_preview,
                                            self.on_set_border_image:      self.camera_eng.on_set_border_image
                                        },
                                    "method_signals":
                                        {
                                            self.camera_eng.on_status:                "status",
                                            self.camera_eng.on_update_filter_preview: "updateImageFilterPreview",
                                            self.camera_eng.on_set_border_image:      "setBorderForImage"
                                        },
                                    "internal_signals":
                                        {
                                            self.camera_eng.on_change_screen:        self.change_screen,
                                        },
                                },
                            2:
                                {
                                    "url":    "qml/preview.qml",
                                    "engine": self.preview_eng,
                                    "master_signals":
                                        {
                                            self.on_status:     self.preview_eng.on_status
                                        },
                                    "method_signals":
                                        {
                                            self.preview_eng.on_status:     "status",
                                        },
                                    "internal_signals":
                                        {
                                            self.preview_eng.on_change_screen:       self.change_screen,
                                        },
                                },
                            3:
                                {
                                    "url":    "qml/processing.qml",
                                    "engine": self.proc_eng,
                                    "master_signals":
                                        {
                                            self.on_status:     self.proc_eng.on_status
                                        },
                                    "method_signals":
                                        {
                                            self.proc_eng.on_status:     "status",
                                        },
                                    "internal_signals":
                                        {
                                            self.proc_eng.on_change_screen:       self.change_screen,
                                        },
                                },
                            4:
                                {
                                    "url":    "qml/frames.qml",
                                    "engine": self.frames_eng,
                                    "master_signals":
                                        {
                                            self.on_status:                self.frames_eng.on_status,
                                            self.on_set_border_image:      self.frames_eng.on_set_border_image
                                        },
                                    "method_signals":
                                        {
                                            self.frames_eng.on_status:           "status",
                                            self.frames_eng.on_set_border_image: "setBorderForImage",
                                        },
                                    "internal_signals":
                                        {
                                            self.frames_eng.on_change_screen:       self.change_screen,
                                        },
                                },
                            5:
                                {
                                    "url":    "qml/printopt.qml",
                                    "engine": self.printopt_eng,
                                    "master_signals":
                                        {
                                            self.on_status:                self.printopt_eng.on_status,
                                            self.on_set_copies:            self.printopt_eng.on_set_copies
                                        },
                                    "method_signals":
                                        {
                                            self.printopt_eng.on_status:           "status",
                                            self.printopt_eng.on_set_copies:       "setCopies",
                                        },
                                    "internal_signals":
                                        {
                                            self.printopt_eng.on_change_screen:    self.change_screen,
                                        },
                                },
                            6:
                                {
                                    "url":    "qml/printing.qml",
                                    "engine": self.printing_eng,
                                    "master_signals":
                                        {
                                            self.on_status:                self.printing_eng.on_status,
                                        },
                                    "method_signals":
                                        {
                                            self.printing_eng.on_status:           "status",
                                        },
                                    "internal_signals":
                                        {
                                            self.printing_eng.on_change_screen:    self.change_screen,
                                        },
                                },
                        }
    
    def _print(self, text):
        print("[PhotoBoothEngine] %s" % text)
    
    def camera_effect(self, camera, effect):
        n = effect.lower()
        
        if n == 'negative':
            camera.image_effect = 'negative'
        elif n == 'sketch':
            camera.image_effect = 'sketch'
        elif n == 'colorswap':
            camera.image_effect = 'colorswap'
        elif n == 'cartoon':
            camera.image_effect = 'cartoon'
        elif n == 'oilpaint':
            camera.image_effect = 'oilpaint'
        elif n == 'emboss':
            camera.image_effect = 'emboss'
        elif n == 'watercolor':
            camera.image_effect = 'watercolor'
        else:
            camera.image_effect = 'none'
            
    
    def main(self):
        self.fxlist = [
                      'negative',
                      'sketch',
                      'colorswap',
                      'cartoon',
                      'oilpaint',
                      'emboss',
                      'watercolor',
                      'none'
                    ]
        
        self._print("Main started.")
        
        self.socket = socket.socket()
        self.socket.bind(("0.0.0.0", 12345))
        
        self.socket.listen(1)
        
        self.selected_frame_num = 8
        self.num_of_copies = 1
        self.printed = False
        
        with picamera.PiCamera() as camera:
            camera.resolution = 480, 640
            camera.saturation = 50
            camera.brightness = 50
            camera.start_preview()
            
            while not self.stopnow:
                self._print("Loop")
                
                if self.pbstate <= 5:
                    self.printed = False
                
                if self.pbstate == 1:
                    camera.start_preview()
                    
                if self.pbstate == 6:
                    if not self.printed:
                        piprint.printFile(self.selected_frame_num, self.num_of_copies)
                        self.printed = True
                
                conn, addr = self.socket.accept()
                print("Connection from: " + str(addr))
                
                conn.setblocking(0)
                try:
                    data = conn.recv(1024).decode()
                    if not data:
                        break
                except:
                    continue
                
                cmd = data.split(",")
                
                if self.pbstate == 1:
                    if cmd[0] == "filter":
                        sel_filter = cmd[1].strip()
                        self.camera_effect(camera, sel_filter)
                        self.on_set_border_image.emit(self.fxlist.index(sel_filter))
                    elif cmd[0] == "takepic":
                        camera.stop_preview()
                        camera.resolution = 486, 648
                        camera.capture("nice_image.jpg")
                        self.change_screen(2)
                elif self.pbstate == 2:
                    if cmd[0] == "accept":
                        print("pbstate = %i" % self.pbstate)
                        self.change_screen(3)
                    elif cmd[0] == "retake":
                        print("pbstate = %i" % self.pbstate)
                        self.change_screen(1)
                elif self.pbstate == 4:
                    if cmd[0] == "border":
                        print("on_set_border_image | pbstate = %i | cmd[1] = %i" % (self.pbstate, int(cmd[1])))
                        self.on_set_border_image.emit(int(cmd[1]))
                        self.selected_frame_num = int(cmd[1])
                    elif cmd[0] == "select":
                        self.change_screen(5)
                elif self.pbstate == 5:
                    if cmd[0] == "copies":
                        if int(cmd[1]) <= 6 and int(cmd[1]) >= 1:
                            print("on_set_copies | pbstate = %i | cmd[1] = %i" % (self.pbstate, int(cmd[1])))
                            self.on_set_copies.emit(int(cmd[1]))
                            self.num_of_copies = int(cmd[1])
                    elif cmd[0] == "confirm":
                        self.change_screen(6)
                
                conn.send(data.encode())
                conn.close()
                
                #if self.pbstate == 0:
                    #self.on_status.emit("Testing")
                    #self.on_update_filter_preview.emit(1, "test-highlight.jpg")
                    #self.on_change_url.emit('main.qml')
                    
                time.sleep(3)
                
                #if self.pbstate == 0:
                #    self.change_screen(1)
            
    @QtCore.pyqtSlot(int)
    def change_screen(self, state):
        self.disconnect_state(self.pbstate)
        self.stop_state_thread(self.pbstate)
        self.pbstate = state
        self.change_qml(self.pbstate)
        self.connect_state(self.pbstate)
        self.start_state_thread(self.pbstate)
    
    def start_state_thread(self, state):
        self.signalmap[state]["engine"].start()
    
    def stop_state_thread(self, state):
        self.signalmap[state]["engine"].stop()
    
    def change_qml(self, state):
        qmlfile = self.signalmap[state]["url"]
        print("change_qml() called: " + qmlfile)
        self.on_change_url.emit(qmlfile)
    
    def connect_state(self, state):
        print("connect_state() called: state " + str(state))
        self.state_updateable = False
        print(self.signalmap[state]["internal_signals"])
        for signal in self.signalmap[state]["master_signals"]:
            signal.connect(self.signalmap[state]["master_signals"][signal])
        for signal in self.signalmap[state]["internal_signals"]:
            signal.connect(self.signalmap[state]["internal_signals"][signal])
        for signal in self.signalmap[state]["method_signals"]:
            self.on_connect_signal.emit(signal, self.signalmap[state]["method_signals"][signal])
    
    def disconnect_state(self, state):
        for signal in self.signalmap[state]["method_signals"]:
            signal.disconnect()
        for signal in self.signalmap[state]["internal_signals"]:
            signal.disconnect()
        for signal in self.signalmap[state]["master_signals"]:
            signal.disconnect()
    
    def stop(self):
        self.stopnow = True
    
    @QtCore.pyqtSlot()
    def start_download(self):
        if not self.running:
            self.running = True
            thread = threading.Thread(target=self._download)
            thread.start()
    
    on_change_url = QtCore.pyqtSignal(str)
    on_connect_signal = QtCore.pyqtSignal(QtCore.pyqtBoundSignal, str)
    
    on_status = QtCore.pyqtSignal(str)
    on_update_filter_preview = QtCore.pyqtSignal(int, str)
    on_set_border_image = QtCore.pyqtSignal(int)
    on_set_copies = QtCore.pyqtSignal(int)
    
