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
import cv2
from parameters import *

app = flask.Flask(__name__)
CORS(app)
app.config["DEBUG"] = True
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
def image_recognize(path,reg_id):
    img1 = Image.open(path)
    unknown_face_encoding = check_image(path, img1)
    if len(unknown_face_encoding) == 0:
        return {"error": "please give correct and clear image"}
    encode_path = "{}{}_encode.pickle".format(encode_dir, reg_id)
    print("encode============",encode_path)
    with open(encode_path, 'rb') as fp:
        enc = pickle.load(fp)
        my_face_encoding = enc['encodings']
    results = face_recognition.compare_faces(my_face_encoding, unknown_face_encoding,tolerance=0.4)
    distance = face_recognition.face_distance(my_face_encoding, unknown_face_encoding)
    accuracy = get_accuracy(distance[0])
    if results[0] == True and accuracy>0.86:
        return {"status": "matched", "accuracy": accuracy * 100}
    else:
        return {"status": "not matched", "accuracy": accuracy * 100}
if __name__ == '__main__':
    ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])
    # app = Flask(__name__)
    # app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    def api_parameter(img_path,reg_id):
        print("img_pth  :", img_path)
        path = os.path.join(temperary_dir, img_path[0])
        en = img_encoding(path)
        result = image_recognize(path,reg_id)
        return jsonify(result)
    def allowed_file(filename):
        # print(filename)
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    @app.route('/Face_Recognition', methods=['GET'])
    def upload_file():

        if 'reg_id' in request.args:
            reg_id = request.args.get('reg_id', type=int, default=None)
            file = request.args.get('img_path', type=str, default=None)
            # print("reg id =======================",reg_id)
            # print(file)
            t_id=[]
            for i in glob.glob(Directory+"/*"):
                idd = i.split("/")[-1]
                t_id.append(idd)
            if reg_id is None or str(reg_id) not in t_id:
                return jsonify({"error": "please inter valid registration id"})
            if file is None :
                return jsonify({"error": "please inter valid image path"})
            fpath = []
            filename =file.split("/")[-1]
            if file and allowed_file(filename):
                # file.save(os.path.join(temperary_dir, filename))
                # os.rename(re.sub(" ","_",file.filename),file.filename)
                img = Image.open(file)
                img.save(os.path.join(temperary_dir, filename))
                im = check_image(os.path.join(temperary_dir, filename),img)
                if len(im) == 0:
                    return jsonify({"error": "{} has face not detect".format(filename)})
                img.save(os.path.join(temperary_dir, filename))
                print("saved image =======",os.path.join(temperary_dir, filename))
                fpath.append(filename)
            return api_parameter(fpath,reg_id)

    app.run(host='0.0.0.0', debug=True, use_reloader=True)