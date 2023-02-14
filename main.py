import tkinter
import cv2
import PIL.Image, PIL.ImageTk
import time
import threading
import face_recognition as fc
import os
import pickle
from datetime import datetime
from deepface import DeepFace
from simple_facerec import SimpleFacerec
import numpy as np
import pandas as pd
import check_face
import asyncio
import uuid

TARGET_NUMBER_OF_FRAME = 300
PATH = ""
TEMP_PATH = "./faces_to_check"
KEY = "gugaLima8*"


sfr = SimpleFacerec()


sfr.load_encoding_images("images/")

def print_new_image(filename):
    splash_root = tkinter.Toplevel()
    splash_root.withdraw()

    splash_image = PIL.Image.open(filename)
    splash_image = splash_image.resize((splash_root.winfo_screenwidth(), splash_root.winfo_screenheight()), PIL.Image.ANTIALIAS)
    splash_photo = PIL.ImageTk.PhotoImage(splash_image)

    splash_label = tkinter.Label(splash_root, image=splash_photo)
    splash_label.pack()

    splash_root.update()
    time.sleep(3) # tempo em segundos para exibir a splash page

    splash_root.destroy()

class MyVideoCapture:
    def __init__(self, video_source=0, width=None, height=None, fps=None, cameraName=""):
        self.cameraName = cameraName
        self.counter_number_of_frames = 0
        self.video_source = video_source
        self.width = width
        self.height = height
        self.fps = fps
        
        # Open the video source
        self.vid = cv2.VideoCapture(video_source)
        if not self.vid.isOpened():
            print("[MyVideoCapture] Unable to open video source")
            raise ValueError("[MyVideoCapture] Unable to open video source", video_source)

        # Get video source width and height
        if not self.width:
            self.width = int(self.vid.get(cv2.CAP_PROP_FRAME_WIDTH))    # convert float to int
        if not self.height:
            self.height = int(self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT))  # convert float to int
        if not self.fps:
            self.fps = int(self.vid.get(cv2.CAP_PROP_FPS))  # convert float to int

        if self.fps == 0: self.fps = 32

        # default value at start        
        self.ret = False
        self.frame = None

        # start thread
        self.running = True
        self.thread = threading.Thread(target=self.process)
        self.thread.start()
        
    def process(self):
        while self.running:
            ret, frame = self.vid.read()
            
            if ret:
                if frame is None:
                    print("FRAME VAZIO!")
                    pass
                self.counter_number_of_frames+=1
                
                frame = cv2.resize(frame, (self.width, self.height))
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) 


                if self.counter_number_of_frames == TARGET_NUMBER_OF_FRAME:
                    unknow_face_locations = fc.face_locations(frame)
                    for top, right, bottom, left in unknow_face_locations:
                        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 4)
                        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                        crop_face = frame[top:bottom, left:right]

                        is_face_in_db = sfr.detect_known_faces(crop_face)
                        if is_face_in_db == False: 
                            filename =  "C:/Users/novam/Downloads/rtsp/images/" + self.cameraName + str(uuid.uuid4()) + ".jpeg"
                            print(filename)
                            cv2.imwrite(filename=filename, img = crop_face)
                            print_new_image(filename)
                            sfr.load_encoding_images("./images/")
                        else: 
                            print("Enconding já Conhecido!")
                            continue
                    self.counter_number_of_frames = 0
            else:
                self.vid.release()
                time.sleep(5)
                continue
            # assign new frame
            self.ret = ret
            self.frame = frame
            
            # sleep for next frame
            time.sleep(1 / self.fps)
        
    def get_frame(self):
        return self.ret, self.frame
    
    # Release the video source when the object is destroyed
    def __del__(self):
        # stop thread
        if self.running:
            self.running = False
            self.thread.join()

        # relase stream
        if self.vid.isOpened():
            self.vid.release()

            
 
class tkCamera(tkinter.Frame):
    def __init__(self, window, text="", video_source=0, width=None, height=None):
        super().__init__(window)
        
        # number of frames to await to load face detection functions
        self.counter_number_of_frames = 0;
        
        self.window = window
        
        #self.window.title(window_title)
        self.video_source = video_source
        self.vid = MyVideoCapture(self.video_source, width, height, cameraName=text)

        self.label = tkinter.Label(self, text=text)
        self.label.pack()
        
        self.canvas = tkinter.Canvas(self, width=self.vid.width, height=self.vid.height)
        self.canvas.pack()

        # Button that lets the user take a snapshot
        self.btn_snapshot = tkinter.Button(self, text="Start", command=self.start)
        self.btn_snapshot.pack(anchor='center', side='left')
        
        self.btn_snapshot = tkinter.Button(self, text="Stop", command=self.stop)
        self.btn_snapshot.pack(anchor='center', side='left')
         
        # Button that lets the user take a snapshot
        self.btn_snapshot = tkinter.Button(self, text="Snapshot", command=self.snapshot)
        self.btn_snapshot.pack(anchor='center', side='left')
         
        self.delay = int(1000/self.vid.fps)

        print('[tkCamera] source:', self.video_source)
        print('[tkCamera] fps:', self.vid.fps, 'delay:', self.delay)
        
        self.image = None
        
        self.running = True
        self.update_frame()

    def start(self):
        if not self.running:
            self.running = True
            self.update_frame()

    def stop(self):
        if self.running:
           self.running = False
    
    def snapshot(self):
        if self.image:
            self.image.save(time.strftime("frame-%d-%m-%Y-%H-%M-%S.jpg"))
            
    def update_frame(self):
        ret, frame = self.vid.get_frame()

        if ret:
            self.image = PIL.Image.fromarray(frame)
            self.photo = PIL.ImageTk.PhotoImage(image=self.image)
            self.canvas.create_image(0, 0, image=self.photo, anchor='nw')
        
        if self.running:
            self.window.after(self.delay, self.update_frame)


class App:
    def __init__(self, window, window_title, video_sources):
        self.window = window

        self.window.title(window_title)
        
        self.vids = []

        columns = 2
        for number, source in enumerate(video_sources):
            text, stream = source
            try:
                vid = tkCamera(self.window, text, stream, 400, 300)
                x = number % columns
                y = number // columns
                vid.grid(row=y, column=x)
                self.vids.append(vid)
            except:
                print("Nao foi possivel abrir a camera", source)
                pass
        
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.window.mainloop()
    
    def on_closing(self, event=None):
        print('[App] stoping threads')
        for source in self.vids:
            source.vid.running = False
        print('[App] exit')
        self.window.destroy()

def get_cams_from_csv():
    list_of_cams = pd.read_csv("CAMS.csv", sep=',')['IPv4 Address']
    
    return list_of_cams


if __name__ == '__main__':     
    key = input("Insira sua chave de acesso: ")
    if key != KEY:
        print("Chave inválida. O aplicativo será encerrado.")
        exit()
    # while True:
    #     PATH = input("Insira o caminho da pasta onde as imagens devem ser salvas: ")
    #     if os.path.exists(PATH):
    #         break
    #     print("O caminho informado não é válido.")

    sources = []
    
    list_of_cams = get_cams_from_csv()
    
    for i, ip in enumerate(list_of_cams):
        link = f"rtsp://admin:{KEY}@{ip}:554/Streaming/Channels/101/" 
        sources.append((f'CAM{i}', link))

    # TEST REASONS
    # sources.append(("teste", 0))
    print(sources)
    
    App(tkinter.Tk(), "GERENCIAMENTO DE CAMERAS", sources)
    



