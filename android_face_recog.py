import flask
from flask_cors import CORS
import glob
from PIL import Image
from flask import request, redirect, jsonify
from werkzeug.utils import secure_filename
from werkzeug import SharedDataMiddleware
import re
import face_recognition
import pickle
import os
from flask import Flask
import math
from parameters import *
import numpy as np
app = flask.Flask(__name__)
CORS(app)
def check_faces(path):
    try:
        print("here",path)
        rimg = face_recognition.load_image_file(path)
        img_face_encoding = face_recognition.face_encodings(rimg)[0]
        return img_face_encoding
    except:
        return "rotate"
def img_encoding(path):
    picture = face_recognition.load_image_file(path)
    face_encoding = face_recognition.face_encodings(picture)[0]
    return face_encoding
def check_image(path, img):
    print("<=======>",path)
    if check_faces(path) == "rotate":
        img1 = img.rotate(90)
        img1.save(path)
        print(1)
        if check_faces(path) == "rotate":
            img1 = img.rotate(-90)
            img1.save(path)
            print(2)
        else:
            img_face_encoding = check_faces(path)
        if check_faces(path) == "rotate":
            return []
        else:
            img_face_encoding = check_faces(path)
            print(3)
    else:
        img_face_encoding = check_faces(path)
    return img_face_encoding
def check_image_size(ipath):
    basewidth = 600
    img = Image.open(ipath)
    if img.size[0] > 1000 or img.size[0] < 1000:
        wpercent = (basewidth / float(img.size[0]))
        hsize = int((float(img.size[1]) * float(wpercent)))
        img = img.resize((basewidth, hsize), Image.ANTIALIAS)
        img.save(ipath)
def get_accuracy(face_distance, face_match_threshold=0.6):
    if face_distance > face_match_threshold:
        range = (1.0 - face_match_threshold)
        linear_val = (1.0 - face_distance) / (range * 2.0)
        return linear_val
    else:
        range = face_match_threshold
        linear_val = 1.0 - (face_distance / (range * 2.0))
        return linear_val + ((1.0 - linear_val) * math.pow((linear_val - 0.5) * 2, 0.2))
def image_recognize(encod,reg_id):

    unknown_face_encoding = encod
    print("encoding ===============",unknown_face_encoding)
    if len(list(unknown_face_encoding)) == 0:
        return {"error": "please give correct and clear image"}
    encode_path = "{}{}_encode.pickle".format(encode_dir, reg_id)
    print("encode============",encode_path)
    with open(encode_path, 'rb') as fp:
        enc = pickle.load(fp)
        my_face_encoding = enc['encodings']
        print("my_face encoding ==============",my_face_encoding)
    results = face_recognition.compare_faces(my_face_encoding, unknown_face_encoding,tolerance=0.4)
    distance = face_recognition.face_distance(my_face_encoding, unknown_face_encoding)
    print(distance)
    accuracy = get_accuracy(distance[0])
    print(("accuracy=====",accuracy),results)
    if results[0] == True and accuracy>0.86:
        return {"status": "matched", "accuracy": accuracy * 100}
    else:
        return {"status": "not matched", "accuracy": accuracy * 100}
if __name__ == '__main__':
    ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])
    app = Flask(__name__)
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    def api_parameter(encod,reg_id):
        result = image_recognize(encod,reg_id)
        return jsonify(result)
    def allowed_file(filename):

        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    @app.route('/Face_Recognition', methods=['POST', 'GET'])
    def upload_file():
        if request.method == 'POST':
            data = request.get_json()
            print(data)
            data = data['nameValuePairs']
            print(data)
            try:
                reg_id = data["reg_id"]
                fe = data["face_encoding"]['values'][0]['values']
                # encod = np.array(data["face_encoding"])
                encod = np.array(fe)
            except:
                return jsonify({"error": "please inter valid registration id and face image"})
            t_id=[]
            for i in glob.glob(Directory+"/*"):
                idd = i.split("/")[-1]
                t_id.append(idd)
            if reg_id is None or str(reg_id) not in t_id:
                return jsonify({"error": "please inter valid registration id"})
            return api_parameter(encod,reg_id)

    app.run(host='0.0.0.0', debug=True, use_reloader=True)