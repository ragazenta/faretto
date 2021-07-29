from imutils import paths
import face_recognition
import pickle
import cv2
import os


def encode_student_data(student_id):
    # Grabbing the input images in our dataset
    # print("[INFO] quantifying faces..")
    student_image_path = os.path.join("dataset", student_id)
    imagePaths = list(paths.list_images(student_image_path))
    encodings_file = "encodings.pickle"

    # initialise the list of known encodings and known names
    knownEncodings = []
    knownNames = []

    # loop over the image paths
    for (i, imagePath) in enumerate(imagePaths):
        # Extract person name from the image path
        # print("[INFO] processing image {}/{}".format(i+1,len(imagePaths)))
        name = imagePath.split(os.path.sep)[-2]

        # load the image and convert it frim RGM (OpenCV ordering)
        # to dlib ordering (RGB)
        image = cv2.imread(imagePath)
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # detect the coordinates of face
        box = face_recognition.face_locations(rgb, model='hog')

        # Now as we have face coordinates now compute the encodings
        encodings = face_recognition.face_encodings(rgb, box)

        # Loop over the encodings :
        for encoding in encodings:
            # add the values and names in the empty list
            knownEncodings.append(encoding)
            knownNames.append(name)
    # now save the list
    # print("[INFO] Serializing encodings..")
    old_data = {
        "encodings": [],
        "names": [],
    }
    # Load the known face and encodings
    if os.path.getsize(encodings_file) > 0:
        with open(encodings_file, "rb") as f:
            old_data = pickle.loads(f.read(), encoding="latin1")

    old_data['encodings'] += knownEncodings
    old_data['names'] += knownNames
    # print(old_data)
    with open("encodings.pickle", "wb") as f:
        f.write(pickle.dumps(old_data))
