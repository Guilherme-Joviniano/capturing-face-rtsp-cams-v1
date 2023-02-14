from deepface import DeepFace
import pandas as pd 
metrics = ["cosine", "euclidean", "euclidean_l2"]

backends = [
    'opencv',
    'ssd',
    'dlib',
    'mtcnn',
    'retinaface',
    'mediapipe'
]

def extract_faces(frame):
    data = DeepFace.extract_faces(
        frame, align=True, enforce_detection = False
    )
    faces = [];
    for face in data:faces.append(face['facial_area']) 
    return faces

async def is_face_in_db(face):
    try:
        df = await DeepFace.find(img_path=face, db_path="C:/Users/novam/Downloads/rtsp/faces", distance_metric = metrics[2])[0]
        isempty = df.empty
        if isempty: 
            print("Achei Nada, Vou Salvar!")
            return False
        else: print("Já guardei já ta bom amigão?")
        return True
    except:
        return False


if __name__ == "__main__":
    # extract all faces locations 
    faces = extract_faces("./lakers.jpg")
    # check if exist in db to each face
    is_face_in_db("./seed_image.jpg")
