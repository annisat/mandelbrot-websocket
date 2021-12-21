from mandelbrot_gen import MandelbrotWorker
import time, cv2


wkr = MandelbrotWorker(-0.5+0j, 1, 1e4)
start_time = time.time()
cnt = 0

while wkr.main_thread.is_alive():
    time.sleep(.1)
    img, prog = wkr.get_snapshot()
    print(prog)
    cv2.imwrite(f"{cnt}.png", img)
    cnt+=1
    if cnt == 10: wkr.kill_job()
    
img, prog = wkr.get_snapshot()
cv2.imwrite("ending.png", img)
wkr.kill_job()
