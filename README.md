# Faretto
Face Recogniton based Attendance Automation


## Tested environments
- Python 3.6+
- Linux: Ubuntu 18.04 LTS, requires CMake
- Windows: Windows 10 20H2, requires CMake, Microsoft Visual Studio 2015 (or newer) with C/C++ Compiler


## Installation

### Clone this repo

	git clone https://github.com/ragazenta/faretto.git
	cd faretto

### Virtual environment

Create a venv folder:

    python3 -m venv venv

On Windows:

    py -3 -m venv venv

#### Activate the environment

Before you work on your project, activate the corresponding environment:

    . venv/bin/activate

On Windows:

    venv\Scripts\activate

Your shell prompt will change to show the name of the activated environment.


### Install requirements.txt

Within the activated environment, use the following command to install
requirements:

	python -m pip install --upgrade pip
    pip install wheel
    pip install -r requirements.txt


## Running the application

	python main.py


## Python libraries
- [face_recognition](https://github.com/ageitgey/face_recognition): The world's simplest facial recognition api for Python
- [eel](https://github.com/ChrisKnott/Eel): A little Python library for making simple Electron-like HTML/JS GUI apps
- [opencv-python-headless](https://github.com/opencv/opencv-python)
- [imutils](https://github.com/jrosebr1/imutils)


This repo is for learning purpose only, based on [original repo](https://github.com/kuntal811/automatic-attendance-using-face-recognition).
