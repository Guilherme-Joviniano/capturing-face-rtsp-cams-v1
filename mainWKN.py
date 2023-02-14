import nmap
import cv2
import face_recognition
import datetime
import os
import time as tm
import threading
import tkinter as tk
import socket
import pandas as pd
import numpy as np

ips = pd.read_csv("CAMS.csv", sep=',')['IPv4 Address']

print(ips)

KEY = "gugaLima8*"
START_DATE = datetime.datetime(2022, 1, 1)
END_DATE = datetime.datetime(2023, 3, 1)
LAST_FACES = []

key = input("Insira sua chave de acesso: ")
if key != KEY:
    print("Chave inválida. O aplicativo será encerrado.")
    exit()

current_date = datetime.datetime.now()
if current_date < START_DATE or current_date > END_DATE:
    print("A chave não é válida para a data atual. O aplicativo será encerrado.")
    exit()


def scan_network():
    nm = nmap.PortScanner()
    nm.scan(hosts='192.168.18.118', arguments='-p 554')
    hosts = []
    for host in nm.all_hosts():
        if nm[host].has_tcp(80):
            hosts.append(host)
    print("Resultado da varredura da rede: ", hosts)
    return hosts


def capture_faces(ip, folder):
    cap = cv2.VideoCapture(f"rtsp://admin:{KEY}@{ip}:554/Streaming/Channels/101/")
    while True:
        ret, frame = cap.read()

        try:
            small_frame = cv2.resize(frame, None, fx=0.25, fy=0.25,)
        except:
            pass

        if not ret:
            break

        cv2.imshow("Camera " + str(ip), small_frame)

        face_locations = face_recognition.face_locations(small_frame)
        face_encondings = face_recognition.face_encodings(small_frame, face_locations)

        print(len(LAST_FACES))
        for face_enconding in face_encondings:
            match = face_recognition.compare_faces(LAST_FACES, face_enconding)

            if True not in match:
                LAST_FACES.append(face_enconding)
                now = datetime.datetime.now()
                date_str = now.strftime("%Y-%m-%d")
                time_str = now.strftime("%H-%M-%S")
                if not os.path.exists(folder):
                    os.makedirs(folder)
                filename = folder + "/" + ip + "_" + date_str + "_" + time_str + ".jpg"
                cv2.imwrite(filename, frame)

        # Label the results
        for top, right, bottom, left in face_locations:
            # Draw a box around the face
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

            # Draw a label with a name below the face
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


def start_detection():
    # verificando se o caminho é válido
    while True:
        folder = input("Insira o caminho da pasta onde as imagens devem ser salvas: ")
        if os.path.exists(folder):
            break
        print("O caminho informado não é válido.")
    cameras_online = len(ips)
    print(cameras_online)
    # camera_summary_label.config(text="Câmeras online: " + str(cameras_online))
    # t = threading.Thread(target=display_cameras, args=(ips, 10, 8))
    # t.start()
    for host in ips:
        capture_faces(host, folder)


# root = tk.Tk()
# image = tk.PhotoImage(file="image.png")
# image_label = tk.Label(root, image=image)
# image_label.pack()
# start_button = tk.Button(root, text="Iniciar Detecção", command=start_detection)
# camera_summary_label = tk.Label(root, text="Câmeras online: 0")
# camera_summary_label.pack()
# start_button.pack()
# root.mainloop()

start_detection()
