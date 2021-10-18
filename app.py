from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import os, cv2, base64
from mandelbrot_gen import mandelbrot_gen
import traceback

# Basic flask app
app = Flask(__name__)
CORS(app, supports_credentials=True)
socketio = SocketIO(app, cors_allowed_origins="*")



@socketio.on('send_task')
def do_mbs(data):
    try:
        print(data)
        center = data['real'] + data['imaginary']*1j
        radius = data['radius']
        for prog, img in mandelbrot_gen(center, radius, [512, 512], iter=1e5, max_workers=5):
            # print(prog)
            img_bin = cv2.imencode('.jpg', img)[1]
            # print(len(img_bin))
            img_b64 = base64.b64encode(img_bin).decode('utf-8')
            # print(len(img_b64))
            emit("server_reponse", {'prog': prog, 'img': img_b64})
        #emit('server_response', {'c':str(msg['c_real']+msg['c_img']*1j), 'r':str(msg['r'])})
        
    except Exception as err:
        print("Something went wrong")
        traceback.print_exc()
    # return None



if __name__ == '__main__':
    socketio.run(app, debug=False, host='0.0.0.0', port=5000)
    # app.run(host='0.0.0.0', port=5000)