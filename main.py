import eel
import cv2
import numpy as np
import base64
import os
import time
import face_recognition
import pickle
import imutils
import datetime
from multiprocessing.pool import ThreadPool
import random
import shutil

from database import *
from SceneChangeDetect import SceneChangeDetect
import photo
import login
import encode_student_data


eel.init('web')

camera_status = 1
capture_status = False
student_id = ""
encodings_file = "encodings.pickle"


def recogFace(data, encoding):
    return face_recognition.compare_faces(data["encodings"], encoding, tolerance=0.5)


def recogEncodings(rgb, boxes):
    return face_recognition.face_encodings(rgb, boxes)


def recogLoc(rgb):
    return face_recognition.face_locations(rgb, model="hog")


def gen1(url, student_class):
    # change camera status for loading
    eel.camera_status(3)

    pool1 = ThreadPool(processes=1)
    pool2 = ThreadPool(processes=2)
    pool3 = ThreadPool(processes=3)
    pool4 = ThreadPool(processes=4)

    conn = create_connection()
    cursor = conn.cursor()
    sql = "SELECT student_id FROM student_data WHERE class = ? "
    val = [student_class]
    cursor.execute(sql, val)
    student_data = cursor.fetchall()

    data = {
        "encodings": [],
        "names": [],
    }
    # Load the known face and encodings
    if os.path.getsize(encodings_file) > 0:
        with open(encodings_file, "rb") as f:
            data = pickle.loads(f.read(), encoding="latin1")

    attendees_names = {}
    encodings = []
    boxes = []
    frame = 0
    Scene = SceneChangeDetect()
    video = cv2.VideoCapture(url)
    time.sleep(1.0)

    global camera_status
    camera_status = 1
    # change the camera status
    eel.camera_status(1)

    while camera_status == 1:
        frame += 1
        if frame == 100:
            frame = 0

        success, img = video.read()
        # if camera can't read frame (Camera error)
        if success is False:
            eel.camera_status(2)
            break
        if (Scene.detectChange(img) is True):
            # Convert the BGR to RGB
            # a width of 750px (to speed up processing)
            rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            rgb = imutils.resize(img, width=750)
            r = img.shape[1] / float(rgb.shape[1])

            # detect boxes
            if frame % 2 == 0:
                boxes = pool1.apply_async(recogLoc, (rgb,)).get()
                encodings = pool3.apply_async(recogEncodings, (rgb, boxes,)).get()
            names = []

            # loop over the facial encodings
            for encoding in encodings:
                # attempt to match each face then initialise a dicationary
                # matches = face_recognition.compare_faces(data["encodings"], encoding,tolerance=0.5)
                matches = pool2.apply_async(recogFace, (data, encoding,)).get()
                name = "Unknown"

                # check to see if we have found a match
                if True in matches:
                    # find the indexes of all matched faces then initialize a
                    # dicationary to count the total number of times each face matched
                    matchedIds = [i for (i, b) in enumerate(matches) if b]
                    counts = {}

                    # loop over the recognized faces
                    for i in matchedIds:
                        name = data["names"][i]
                        counts[name] = counts.get(name, 0) + 1

                    # determine the recognized faces with largest number
                    # of votes (note: in the event of an unlikely tie Python will select first entry in the dictionary)
                    name = max(counts, key=counts.get)
                    if(name not in attendees_names):
                        attendees_names[name] = 1
                        for y in student_data:
                            if name in y:
                                now = datetime.datetime.now()
                                pool4.apply_async(submit_live_attendance, (name, now,))
                                eel.updateAttendance(name)()

                names.append(name)

        # loop over recognized faces
        for ((top, right, bottom, left), name) in zip(boxes, names):
            top = int(top * r)
            right = int(right * r)
            bottom = int(bottom * r)
            left = int(left * r)
            # draw the predicted face name on the image
            cv2.rectangle(img, (left, top), (right, bottom), (0, 255, 0), 2)
            y = top - 15 if top - 15 > 15 else top + 15
            cv2.putText(img, name, (left, y), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)

        ret, jpeg = cv2.imencode('.jpg', img)
        img = jpeg.tobytes()
        yield img
    # camera is stopped by user
    if success is True:
        eel.camera_status(0)


@eel.expose
def start_video_py(cam_type, student_class, url=''):
    switch = {
        '1': 0,
        '2': 1,
        '3': url,
    }
    y = gen1(switch[cam_type], student_class)
    for each in y:
        # Convert bytes to base64 encoded str, as we can only pass json to frontend
        blob = base64.b64encode(each)
        blob = blob.decode("utf-8")
        eel.updateImageSrc(blob)()


@eel.expose
def stop_video_py():
    global camera_status
    camera_status = 0


@eel.expose
def photoUpload(b64_string, student_class):
    encoded_data = b64_string.split(',')[1]
    nparr = np.fromstring(base64.b64decode(encoded_data), np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    photo.recognizeFromPhoto(img, student_class)


@eel.expose
def capture_photo_py(url):
    y = gen(url)
    for each in y:
        # Converted to base64 encoded str, as we can only pass json to frontend
        blob = base64.b64encode(each)
        blob = blob.decode("utf-8")
        eel.updateStudentImageSrc(blob)()


def gen(url):
    video = cv2.VideoCapture(url)
    time.sleep(2.0)
    global camera_status
    global capture_status
    camera_status = 1
    # change the camera status
    while camera_status == 1:
        success, img = video.read()
        # if camera can't read frame
        if success is False:
            # print("cam nt cnt")
            break
        if capture_status is True:
            save_path = 'dataset/' + student_id
            filename = save_path + "/photo" + str(random.randint(0, 999)) + ".jpg"
            if not os.path.exists(save_path):
                os.makedirs(save_path)
            cv2.imwrite(filename, img)
            send_capture_photo(img)
            capture_status = False
        ret, jpeg = cv2.imencode('.jpg', img)
        img = jpeg.tobytes()
        yield img


# add new attendance data
def submit_live_attendance(student_id, dtm):
    # adding data to database
    conn = create_connection()
    cursor = conn.cursor()
    sql = "INSERT INTO attendance_data(date, time, student_id) VALUES (?, ?, ?);"
    datestr = dtm.strftime("%Y-%m-%d")
    timestr = dtm.strftime("%H:%M:%S")
    val = (datestr, timestr, student_id,)
    cursor.execute(sql, val)
    conn.commit()
    conn.close()


@eel.expose
def save_photo(studentId):
    global student_id
    global capture_status
    student_id = studentId
    capture_status = True


def send_capture_photo(img):
    ret, jpeg = cv2.imencode('.jpg', img)
    img = jpeg.tobytes()
    blob = base64.b64encode(img)
    blob = blob.decode("utf-8")
    eel.showCapturePhoto(blob)


# adding new student data
@eel.expose
def submit_student_data(stu_id, fullname, student_class, session):
    try:
        encode_student_data.encode_student_data(stu_id)
        # adding data to database
        conn = create_connection()
        cursor = conn.cursor()
        sql = "INSERT INTO student_data(student_id, fullname, class, session) VALUES (?, ?, ?, ?);"
        val = [stu_id, fullname, student_class, session]
        cursor.execute(sql, val)
        conn.commit()
        eel.student_data_saved()
        conn.close()

    except Exception:
        # delete face data from file
        delete_student_data_file(student_id)
        eel.failed_data_submit()


@eel.expose
def fetch_class_data(search_class):
    conn = create_connection()
    cursor = conn.cursor()
    val = [search_class]
    sql = "SELECT * FROM student_data WHERE class = ?"
    result = cursor.execute(sql, val)
    for x in result:
        eel.setTableData(x[0], x[1], x[2], x[3])
    conn.close()


def delete_student_data_file(student_id):
    # delete face data from file
    # load the face data
    face_data = {
        "encodings": [],
        "names": [],
    }
    # Load the known face and encodings
    if os.path.getsize(encodings_file) > 0:
        with open(encodings_file, "rb") as f:
            face_data = pickle.loads(f.read(), encoding="latin1")

    index = []
    encodings = face_data['encodings']
    names = face_data['names']

    # count face data length
    for i, item in enumerate(names):
        if student_id in item:
            index.append(i)
    # delete id
    for i in index:
        names.remove(student_id)
    # delete encoding
    for i in index:
        del encodings[index[0]]

    # saved modified face data
    face_data['names'] = names
    face_data['encodings'] = encodings

    with open(encodings_file, "wb") as f:
        f.write(pickle.dumps(face_data))


@eel.expose
def deleteStudent(student_id):
    try:
        # delete student image folder
        try:
            path = 'dataset/' + student_id
            shutil.rmtree(path)
        except OSError:
            pass

        # delete student data from database
        conn = create_connection()
        cursor = conn.cursor()
        val = [student_id]
        sql = "DELETE FROM student_data where student_id = ?;"
        cursor.execute(sql, val)
        conn.commit()
        conn.close()

        # delete face data from file
        delete_student_data_file(student_id)
        eel.deleteStatus(student_id)
    except Exception:
        eel.deleteStatus("")


@eel.expose
def fetchAttendance(attendanceClass, attendanceDate):
    student_class = {
        "x": "SELECT DISTINCT(a.student_id), s.fullname, s.class, a.date, a.time FROM attendance_data a INNER JOIN student_data s ON s.student_id = a.student_id WHERE s.class = 'x' AND a.date = ?;",
        "xi": "SELECT DISTINCT(a.student_id), s.fullname, s.class, a.date, a.time FROM attendance_data a INNER JOIN student_data s ON s.student_id = a.student_id WHERE s.class = 'xi' AND a.date = ?;",
        "xii": "SELECT DISTINCT(a.student_id), s.fullname, s.class, a.date, a.time FROM attendance_data a INNER JOIN student_data s ON s.student_id = a.student_id WHERE s.class = 'xii' AND a.date = ?;",
    }
    conn = create_connection()
    cursor = conn.cursor()
    val = [attendanceDate]
    sql = student_class[attendanceClass]
    cursor.execute(sql, val)
    result = cursor.fetchall()
    if len(result) > 0:
        for x in result:
            eel.attendanceTable(x[0], x[1], x[2], x[3], x[4])
    else:
        eel.attendanceTable("No result found", "", "", "", "")
    conn.close()


@eel.expose
def fetch_graph_data(graphClass):
    student_class = {
        "x": "SELECT DISTINCT(a.date) FROM attendance_data a INNER JOIN student_data s ON s.student_id = a.student_id WHERE s.class = 'x' ORDER BY a.date ASC LIMIT 10",
        "xi": "SELECT DISTINCT(a.date) FROM attendance_data a INNER JOIN student_data s ON s.student_id = a.student_id WHERE s.class = 'xi' ORDER BY a.date ASC LIMIT 10",
        "xii": "SELECT DISTINCT(a.date) FROM attendance_data a INNER JOIN student_data s ON s.student_id = a.student_id WHERE s.class = 'xii' ORDER BY a.date ASC LIMIT 10",
    }
    attendance_class = {
        "x": "SELECT COUNT(DISTINCT(a.student_id)) FROM attendance_data a INNER JOIN student_data s ON s.student_id = a.student_id WHERE s.class = 'x' AND a.date = ?;",
        "xi": "SELECT COUNT(DISTINCT(a.student_id)) FROM attendance_data a INNER JOIN student_data s ON s.student_id = a.student_id WHERE s.class = 'xi' AND a.date = ?;",
        "xii": "SELECT COUNT(DISTINCT(a.student_id)) FROM attendance_data a INNER JOIN student_data s ON s.student_id = a.student_id WHERE s.class = 'xii' AND a.date = ?;",
    }

    conn = create_connection()
    cursor = conn.cursor()
    sql = student_class[graphClass]
    result = cursor.execute(sql)
    date_arr = []
    data_arr = []
    for x in result:
        date_arr.append(x[0])
    sql = attendance_class[graphClass]
    for x in date_arr:
        val = [x]
        result = cursor.execute(sql, val)
        for x in result:
            data_arr.append(x[0])
    cursor.close()
    eel.updateGraph(date_arr, data_arr)


@eel.expose
def get_user_details():
    return login.session['username']


eel.start('login.html', size=(1280, 720))
