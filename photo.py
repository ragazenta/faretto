import face_recognition
import cv2
import eel
import base64
import os
import pickle
import imutils
import datetime
from multiprocessing.pool import ThreadPool
from database import *


def recogFace(data, encoding):
    return face_recognition.compare_faces(data["encodings"], encoding, tolerance=0.5)


def recogEncodings(rgb, boxes):
    return face_recognition.face_encodings(rgb, boxes)


def recogLoc(rgb):
    return face_recognition.face_locations(rgb, model="hog")


def recognizeFromPhoto(img, student_class):
    pool1 = ThreadPool(processes=1)
    pool2 = ThreadPool(processes=2)
    pool3 = ThreadPool(processes=3)
    pool4 = ThreadPool(processes=4)

    # Load the known faces ids
    conn = create_connection()
    cursor = conn.cursor()
    sql = "SELECT student_id FROM student_data WHERE class = ?;"
    val = [student_class]
    cursor.execute(sql, val)
    student_data = cursor.fetchall()
    encodings_file = "encodings.pickle"

    data = {
        "encodings": [],
        "names": [],
    }
    # Load the known face and encodings
    if os.path.getsize(encodings_file) > 0:
        with open(encodings_file, "rb") as f:
            data = pickle.loads(f.read(), encoding="latin1")

    encodings = []
    boxes = []
    attendees_names = {}
    frame = 0

    # Convert the BGR to RGB
    # a width of 750px (to speed up processing)
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    rgb = imutils.resize(img, width=750)
    r = img.shape[1] / float(rgb.shape[1])

    # detect boxes
    if frame % 5 == 0:
        boxes = pool1.apply_async(recogLoc, (rgb,)).get()
        encodings = pool3.apply_async(recogEncodings, (rgb, boxes,)).get()
    names = []

    # loop over the facial encodings
    for encoding in encodings:
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
            if name not in attendees_names:
                attendees_names[name] = 1
                for y in student_data:
                    if name in y:
                        now = datetime.datetime.now()
                        pool4.apply_async(submit_photo_attendance, (name, now,))
                        eel.updateAttendance(name)()

        names.append(name)

    # loop over recognized faces
    for ((top, right, bottom, left), name) in zip(boxes, names):
        top = int(top * r)
        right = int(right * r)
        bottom = int(bottom * r)
        left = int(left * r)
        # draw the predicted face name on the image
        cv2.rectangle(img, (left, top), (right, bottom), (0, 255, 0), 5)
        y = top - 15 if top - 15 > 15 else top + 15
        cv2.putText(img, name, (left, y), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 5)
    retval, buffer = cv2.imencode('.jpg', img)
    jpg_as_text = base64.b64encode(buffer)
    photo_string = "data:image/jpeg;base64, " + jpg_as_text.decode()
    eel.updatePhotoAttendance(photo_string)


def submit_photo_attendance(student_id, dtm):
    conn = create_connection()
    cursor = conn.cursor()
    sql = "INSERT INTO attendance_data(date, time, student_id) VALUES (?, ?, ?);"
    datestr = dtm.strftime("%Y-%m-%d")
    timestr = dtm.strftime("%H:%M:%S")
    val = (datestr, timestr, student_id,)
    cursor.execute(sql, val)
    conn.commit()
    conn.close()
