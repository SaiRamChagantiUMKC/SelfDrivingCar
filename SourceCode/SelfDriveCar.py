import socketio #
import eventlet
import numpy as np
from flask import Flask #flask is used to build webapplications, to create instances
from keras.models import load_model
import base64
from io import BytesIO
from PIL import Image # python image library to read images
import cv2

sio = socketio.Server() #initialize webserver, used to perform realtime communication between client and server.
#When a client creates a single connection to websocket server, it keeps listening for new events from server, allows
# us to contineously update the client with server. It establishes bidirectional communication with the server.

app = Flask(__name__) #'__main__' #app is the instance created using flask
speed_limit = 10
def preprocess_image(img): # for preprocessing the image features so that better compatible with NVIDEA model
    img = img[60:135,:,:]
    img = cv2.cvtColor(img, cv2.COLOR_RGB2YUV)
    img = cv2.GaussianBlur(img,  (3, 3), 0)
    img = cv2.resize(img, (200, 66))
    img = img/255
    return img

@sio.on('telemetry')
def telemetry(sid, data): #as soon as connection is establishes, we are setting the initial values,
#simulator is going to send the image details, based on the image, our model extracts features from the images
#and predicts steering angle. It sends back to simulator and this process keeps on repeats.
    speed = float(data['speed'])
    image = Image.open(BytesIO(base64.b64decode(data['image']))) #reading image
    image = np.asarray(image) #converting as array
    image = preprocess_image(image) # image pre processing
    image = np.array([image])
    steering_angle = float(model.predict(image)) #predicting the steering angle from the model
    throttle = 1.0 - speed/speed_limit # to provide constant speed for better control
    print('{} {} {}'.format(steering_angle, throttle, speed))
    send_control(steering_angle, throttle) # send the details to simulator

@sio.on('connect') # when there is connection with client, we can fire an event handler
def connect(sid, environ):
    print('Connected')
    send_control(0, 0)

def send_control(steering_angle, throttle): #to invoke when connection establishes, we will send this data to simulator
    sio.emit('steer', data = { #steer is the event listened by the simulator
        'steering_angle': steering_angle.__str__(),
        'throttle': throttle.__str__()
    })


if __name__ == '__main__':
    model = load_model('selfDriveModel.h5')
    app = socketio.Middleware(sio, app) # to combine socketio server with the flask web app
    eventlet.wsgi.server(eventlet.listen(('', 4567)), app) # webserver gateway interface (wsgi), opens up listening socket on that port
