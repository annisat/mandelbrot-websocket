from flask import Flask, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from mandelbrot_gen import MandelbrotWorker
import time, cv2, base64
from RedisIpsum import RedisIpsum

app = Flask(__name__)
CORS(app, supports_credentials=True)
socketio = SocketIO(app, cors_allowed_origins="*")

inst = RedisIpsum()
img2b64 = lambda img: base64.b64encode(cv2.imencode('.jpg', img)[1]).decode('utf-8')



@socketio.on('new_task')
def new_task(data):
    sid = request.sid
    
    # delete job if there is already one
    inst.delete(sid)
    
    # create new job
    print(data['center_r'], data['center_i'])
    inst.add(sid, MandelbrotWorker(
        data['center_r']+data['center_i']*1j, data['radius'], int(data['iterations']) ) )
        
    # serve based on input
    prog = 0
    while prog < 100.0:
        img, prog = inst.worker(sid).get_snapshot()
        img_b64 = img2b64(img)
        emit("update_draw", {'prog':prog, 'img':img_b64})
        
        while inst.pause_signal(sid):
            time.sleep(0.1)
            if inst.stop_signal(sid): break
        if inst.stop_signal(sid):
            inst.delete(sid)
            emit("update_draw", {'prog':0.0, 'img':img_b64})
            break
        
        time.sleep(0.1)


    
@socketio.on('pause')
def pause():
    inst.pause_signal(request.sid, True)
    
@socketio.on('resume')
def resume():
    inst.pause_signal(request.sid, False)
    
@socketio.on('stop')
def stop():
    print("receive stop")
    inst.stop_signal(request.sid, True)

@socketio.on('changeColor')
def change_color(data):
    print(f"change color to {data['coloring']}")
    inst.worker(request.sid).change_coloring(data['coloring'])
    if not inst.worker(request.sid).running():
        img, prog = inst.worker(request.sid).get_snapshot()
        emit('update_draw', {'prog': prog, 'img': img2b64(img)})


if __name__=='__main__':
    # socketio.run(app, '0.0.0.0', 5001, debug=True)
    app.run('0.0.0.0', 5001, debug=True)