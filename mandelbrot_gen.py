''' Version Table
v1.2    Using parallel on all parallelable matrix operation
v1.2.1  Continuous Calculation, cuda
v1.2.2  Thread for jit and cuda
'''
# from __future__ import generator_stop
import numpy as np
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor
import os, cv2
from time import time, sleep
import numba as nb
import cupy as cp
from collections import namedtuple
Section = namedtuple("Section", "up, down, high")


def mandelbrot_gen(center=None, radius=None, size=None,
                   iter=int(1e4), max_iter=None, cuda=False, max_workers=1):
    # Basic iteration: 10000
    iter = 10000 if iter is None else int(iter)
    max_iter = iter if max_iter is None else int(max_iter)
    
    # Check setting
    assert all([var is not None for var in [center, radius, size]]), "Center, radius, and size(s) are necessary."
    assert not cuda or (max_workers < 2), "CPU multithreading is not compatible with cuda."
        
    # Init necessary variables
    # Support square mode (e.g., size=1024) or rectangle mode (e.g., size=[1024, 768])
    if type(size) is not list: size = [size, size]
    size = [s+1 if s%2 else s for s in size]
    half_size = [(s-1)//2 for s in size]
    # Set resolution
    res = radius*2/min(size)
    # Starting point of iteration
    last_iter = 0
    # Determine data type to be used
    if res > 1e-7: dtype = np.csingle
    elif res > 1e-15: dtype = np.cdouble
    else: dtype = np.clongdouble
    # Drawing thread
    draw_thread = ThreadPoolExecutor(max_workers=1)
    
    # One dimensional (width*height) complex
    C = np.zeros(size[0]*size[1], dtype=dtype)
    # Two dimensional (height, width) recording iteration of convergence for every pixel
    I = np.zeros((size[1], size[0]), dtype=np.uint)
    # Two dimensional (width*height, 2) holding position of I in C
    pos = np.zeros((size[0]*size[1], 2), dtype=np.uint)

    # Init values
    cnt = 0
    for r in range(size[0]):
        for i in range(size[1]):
            C[cnt] = center+(r-half_size[0])*res+(half_size[1]-i)*res*1j
            pos[cnt, :] = [i,r]
            cnt+=1
    Z = np.zeros_like(C)
    


    # Prepare for cuda
    if cuda: Z, C, I, pos = [cp.asarray(mat) for mat in [Z, C, I, pos]]
    
    # Single thread condition
    draw_job = None
    last_draw = time()
    if max_workers == 1:
        _iter_func = _iterate_cuda if cuda else _iterate
        for iter_cnt in range(last_iter, iter):
            
            # Update values according to the rules of Mandelbrot set
            Z, C, pos = _iter_func(Z, C, I, pos, iter_cnt)
            
            if draw_job is None or (draw_job.done() and time()-last_draw > 1):
                if draw_job is None:
                    draw_I = cp.asnumpy(I).copy() if cuda else I.copy()
                    draw_job = draw_thread.submit(_iter2img, draw_I, max_iter)
                else:
                    img = draw_job.result()
                    last_draw = time()
                    draw_I = cp.asnumpy(I).copy() if cuda else I.copy()
                    draw_job = draw_thread.submit(_iter2img, draw_I, max_iter)
                    output = tuple(iter_cnt/iter, img)
                    yield output
            
    # Multithread condition
    else:
        # Progress report
        progress = [0]*max_workers
        results = []
        # Split
        split = list(range(0, size[0], size[0]//max_workers))
        if len(split) < max_workers+1: split += [size[0]]
        else: split[-1] = size[0]
        # Start
        with ThreadPoolExecutor(max_workers=max_workers) as exe:
            # Spliting Z, C, pos accordingly
            for i, (_s, _e) in enumerate(zip(split[:-1], split[1:])):
                results.append( exe.submit( _looping,
                    Z[_s*size[1]:_e*size[1]], C[_s*size[1]:_e*size[1]],
                    I, pos[_s*size[1]:_e*size[1], :],
                    last_iter, iter, progress, i ) )
            # Iterate through working
            for i in range(last_iter, iter):
                while min(progress) <= i:
                    sleep(1)
                    pass
                if draw_job is None or (draw_job.done() and time()-last_draw > 1):
                    if draw_job is None:
                        draw_job = draw_thread.submit(_iter2img, I.copy(), max_iter)
                    else:
                        img = draw_job.result()
                        last_draw = time()
                        draw_job = draw_thread.submit(_iter2img, I.copy(), max_iter)
                        yield i/iter, img
    yield 1, _iter2img(I, max_iter)
            
                      
                      
def _iter2img(I, max_iter):
    # Turn iteration of convergence into opencv image (height, width, 3)
    I = np.log10(I+1)
    I = np.clip(I.astype(np.float32)/np.log10(max_iter+1), 0, 1)
    
    # Color map: Icy (White -> Cyan(w-r) -> Blue(cy-g) -> Black)
    split = [255,255,255]
    I *= sum(split)
    sec = split2sec(split, I)
    
    blue  = sec[0].up + sec[1].high + sec[2].high
    green = sec[1].up + sec[2].high
    red   = sec[2].up
    
    # Color map: Ice and Flame (Black -> Blue -> Cyan -> White -> Red -> Yellow -> White)
    # split = [255,255,255,255,255,255,255,255,255]
    # I *= sum(split)
    # sec = split2sec(split, I)
    
    # blue  = sec[0].up   + sec[1].high + sec[2].high + sec[3].down               + sec[5].up +\
            # sec[6].high + sec[7].high + sec[8].high
    # green =               sec[1].up   + sec[2].high + sec[3].down + sec[4].up   + sec[5].high +\
            # sec[6].down + sec[7].up   + sec[8].high
    # red   =                             sec[2].up   + sec[3].high + sec[4].high + sec[5].high +\
            # sec[6].down               + sec[8].up

    return np.stack([ blue.astype(np.uint8),
                      green.astype(np.uint8),
                      red.astype(np.uint8), ], axis=-1)
                      


def _looping(Z, C, I, pos, last_iter, iter, progress, i):
    for iter_cnt in range(last_iter, iter):
        Z, C, pos = _iterate(Z, C, I, pos, iter_cnt)
        progress[i] = iter_cnt+1
        if not Z.size:
            progress[i] = iter
            break
    return Z, C, pos

# @nb.jit(nopython=True, nogil=True)
def _iterate(Z, C, I, pos, iter_cnt):
    # One iteration
    Z = np.square(Z) + C
    # Z = _core(Z, C)
    
    # Criterion of divergence
    diverged = np.abs(Z)>2
    # diverged = absZ > 2
    if not diverged.any(): return Z, C, pos
    
    # Newly diverged points are found:
    # "Draw" I with the number of iteration
    for target in pos[diverged, :]: I[target[0], target[1]] = iter_cnt+1
    
    # Remove diverged points from Z, C, and pos, for faster future calculation
    Z = Z[~diverged]
    C = C[~diverged]
    pos = pos[~diverged, :]
    return Z, C, pos
    
    
# @nb.jit(nopython=True)
# def _core(Z, C):
    # Z = np.square(Z)+C
    # return Z
    
# @nb.jit(nopython=True)
# def _judge(Z):
    # return np.abs(Z)
    
def _iterate_cuda(Z, C, I, pos, iter_cnt):
    # One iteration
    Z = cp.square(Z)+C
    
    # Criterion of divergence
    diverged = cp.abs(Z)>2
    if not diverged.any(): return Z, C, pos
    
    # Newly diverged points are found:
    # "Draw" I with the number of iteration
    for target in pos[diverged, :]: I[target[0], target[1]] = iter_cnt+1
    
    # Remove diverged points from Z, C, and pos, for faster future calculation
    Z = Z[~diverged]
    C = C[~diverged]
    pos = pos[~diverged, :]
    return Z, C, pos
    
def split2sec(split, I):
    sec = []
    sec_s = 0
    for interval in split:
        sec_e = sec_s + interval
        mask = np.where((sec_s<I) & (I<=sec_e), 1, 0)
        sec.append(Section._make([
            mask*(I-sec_e), mask*(sec_s-I), mask*255]))
        sec_s = sec_e
    return sec
    
if __name__=="__main__":
    import cv2, os
    import base64
    name = 'test'
    ## Redo
    ctr = -0.48108935+0.6146492j
    eps = 1.4-6.3j
    redo_dict = {
        # "a":[-0.5+0j,   1],
        # "b":[-1.4-0.4j,     5e-1],
        # "c":[-1.3-0.4j, 2e-1],
        # "d":[-1.3-0.4j, 1e-1],
        # "e":[-1.3-0.45j, 5e-2],
        # "f":[-1.28-0.425j, 2e-2],
        # "g":[-1.285-0.425j, 1e-2],
        # "h":[-1.285-0.426j, 5e-3],
        # "i":[-1.285-0.426j, 2e-3],
        # "j":[-1.2845-0.4275j, 1e-3],
        # "k":[-1.2840-0.4275j, 5e-4],
        # "l":[-1.2840-0.4275j, 2e-4],
        # "m":[-1.2840-0.4275j, 1e-4],
        # "n":[-1.28401-0.42755j, 5e-5],
        # "o":[-1.28401-0.42755j, 2e-5],
        # "p":[-1.28401-0.42755j, 1e-5],
        # "q":[-1.284007-0.427555j, 5e-6],
        # "r":[-1.284007-0.427555j, 2e-6],
        # "s":[-1.284007-0.427555j, 1e-6],
        # "t":[-1.284006-0.427555j, 5e-7],
        # "u":[-1.284006-0.427555j, 2e-7],
        # "v":[-1.284006-0.427555j, 1e-7],
        # "w":[-1.284006-0.42755508j, 5e-8],
        # "x":[-1.284006-0.42755508j, 2e-8],
        # "y":[-1.284006-0.42755508j, 1e-8],
        "z":[-1.284005995-0.427555087j, 5e-9],
        "1a":[-1.284005995-0.427555087j, 2e-9],
        "1b":[-1.284005995-0.427555087j, 1e-9],
    }
    
    ## Start
    # c, r = -0.5+0j, 1
    # iter = int(1e4)
    # img = mandelbrot(c, r, [1920, 1080], iter, num_workers=6)
    # cv2.imwrite("{}_{}_ice.png".format(str(c)[1:-1], str(r)), img)
    ## Find new site
    c, r = 0.2501+0j, 1e-4
    #start = time.time()
    # img = mandelbrot(c, r, [1024, 1024], iter=1e4, max_workers=6)
    #print("Done in {:.2f}s".format(time.time()-start))
    # cv2.imwrite("{}{}_{}_ice.png".format(name, str(c)[1:-1], r), img)
    for prog, img in mandelbrot_gen(c, r, [512, 512], iter=1e5, max_workers=6, max_iter=1e7):
        print("receive a yield")
        print(prog)
        cv2.imwrite("{:.3f}.jpg".format(prog), img)
        img_bin = cv2.imencode('.jpg', img)
        img_b64 = base64.b64encode(img_bin)
        
        
    
    