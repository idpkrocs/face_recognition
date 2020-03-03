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
from parameters import *

app = flask.Flask(__name__)
CORS(app)
def check_faces(path):
    try:
        rimg = face_recognition.load_image_file(path)
        img_face_encoding = face_recognition.face_encodings(rimg)[0]
        return img_face_encoding
    except:
        return "rotate"
def check_image(path, img):
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
# Registration Images
def img_encoding(path):
    picture = face_recognition.load_image_file(path)
    face_encoding = face_recognition.face_encodings(picture)[0]
    # print("face encoding <===>",face_encoding)
    return face_encoding
def files(reg_id, directory):
    print("here")
    print(directory)
    if not os.path.exists(directory):
        os.makedirs(directory)
        encode_path = "{}{}_encode.pickle".format(encode_dir, reg_id)
        data = {"encodings": [], "names": []}
        f = open(encode_path, "wb")
        f.write(pickle.dumps(data))
        f.close()
        print("created directory {}".format(directory))
    fils = list(glob.glob(directory + "/*"))
    [os.rename(fil, re.sub(" ", "_", fil)) for fil in fils]
    fils = list(glob.glob(directory+"/*"))
    return fils
def registration(Directory, encode_dir, reg_id):
    directory = '{}/{}'.format(Directory, reg_id)
    encode_path = "{}{}_encode.pickle".format(encode_dir, reg_id)
    fils1 = files(reg_id, directory)
    encod = []
    for i in fils1:
        try:
            print(i)
            enc = img_encoding(i)
        except:
            print("invalid image : {} please uplaod a clear face image".format(i.split("/")[-1]))
            continue
        encod.append(enc)
    with open(encode_path, 'rb') as fp:
        enc = pickle.load(fp)
        enc = enc['encodings']
    encod = enc + encod
    lbl = [reg_id] * len(encod)
    print("encod length=====",len(encod))
    data = {"encodings": encod, "names": lbl}
    f = open(encode_path, "wb")
    f.write(pickle.dumps(data))
    f.close()
if __name__ == '__main__':

    UPLOAD_FOLDER = Directory
    ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])
    app = Flask(__name__)
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    def api_parameter(reg_id):
        registration(Directory, encode_dir,reg_id)
        return jsonify({"status":"registration succesfully "})
    def allowed_file(filename):
        # print(filename)
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    @app.route('/Face_Registration', methods=['POST', 'GET'])
    def upload_file():
        if request.method == 'POST':
            reg_id = flask.request.args.get('reg_id', type=int, default=None)
            print("reg ============",reg_id)
            # check if the post request has the file part
            files=[]
            for f in request.files:
                files.append(request.files.get(str(f)))
            if reg_id is None:
                return jsonify({"error": "please inter valid registration id"})
            fpath = []
            if len(files) < 1:
                return jsonify({"error": "please upload a valid face images"})
            for file in files:
                if file.filename == '':
                    return redirect(request.url)
                    # return redirect(url_for('results')
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(temperary_dir, filename))
                    img = Image.open(os.path.join(temperary_dir, filename))
                    print("uploaded file ---------",os.path.join(temperary_dir, filename))
                    im = check_image(os.path.join(temperary_dir, filename),img)
                    if len(im) == 0:
                        return jsonify({"error": "{} has face not detect".format(filename)})
                    directory = '{}/{}/'.format(Directory, reg_id)
                    if not os.path.exists(directory):
                        os.makedirs(directory)
                        encode_path = "{}{}_encode.pickle".format(encode_dir, reg_id)
                        data = {"encodings": [], "names": []}
                        f = open(encode_path, "wb")
                        f.write(pickle.dumps(data))
                        f.close()
                        print("created directory {}".format(directory))
                    print(directory)
                    img.save(os.path.join(directory, filename))
            return api_parameter(reg_id)
        return '''
        <!doctype html>
        <title>Upload Image Files</title>
        <h1>Upload Image Files</h1>
        <form method=post enctype=multipart/form-data>
          <input type="file" name="files[]" multiple="true">
          <input type=submit value=Upload>
        </form>
        '''
    @app.route('/uploads/<filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'],
                                   filename)
    app.add_url_rule('/uploads/<filename>', 'uploaded_file',
                     build_only=True)
    app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
        '/uploads': app.config['UPLOAD_FOLDER']
    })
    app.run(host='0.0.0.0', debug=True, use_reloader=True,port=5001)