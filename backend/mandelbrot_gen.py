from threading import Thread
from concurrent.futures import ThreadPoolExecutor
import time
import numpy as np, numba as nb, cupy as cp
from coloring_utils import coloring_func



class MandelbrotWorker():
    cuda = False
    max_workers = 1 if cuda else 6
    
    def __init__(self, center, radius, iterations):
        # Define size. Open for input in future verson (L W)
        size = [640, 360]
        
        # Variable for interruption
        self.draw_prog = 0
        self.draw_obj = None
        self.draw_signal = False
        self.kill_signal = False
        self.draw_type = 0
        self.I = None
        
        # Drawing
        self.iterations = iterations
        
        # Threads
        self.main_thread = Thread(
            target=self._main_loop,
            args=(center, radius, size, int(iterations))
        )
        self.draw_thread = ThreadPoolExecutor(max_workers=1)
        self.main_thread.start()
        
        
        
    def _main_loop(self, center, radius, size, iterations):
        ### Calculate granularity
        # Get an odd size value
        size = [s+1 if s%2 else s for s in size]
        half_size = [(s-1)//2 for s in size]
        # Set resolution
        res = radius*2/min(size)
        # Determine data type to be used
        if res > 1e-7: dtype = np.csingle
        elif res > 1e-15: dtype = np.cdouble
        else: dtype = np.clongdouble
        
        ### Take resources
        # One dimensional (width*height) complex
        C = np.zeros(size[0]*size[1], dtype=dtype)
        Z = np.zeros_like(C)
        # Two dimensional (height, width) recording iteration of convergence for every pixel
        self.I = np.zeros((size[1], size[0]), dtype=np.uint)
        # Two dimensional (width*height, 2) holding position of I in C
        pos = np.zeros((size[0]*size[1], 2), dtype=np.uint)

        ### Init values
        cnt = 0
        for r in range(size[0]):
            for i in range(size[1]):
                C[cnt] = center+(r-half_size[0])*res+(half_size[1]-i)*res*1j
                pos[cnt, :] = [i,r]
                cnt+=1
        
        ### Prepare for cuda
        if self.cuda: Z, C, self.I, pos = [cp.asarray(mat) for mat in [Z, C, self.I, pos]]
    
        ### Single thread condition
        if self.max_workers == 1:
            _iter_func = _iterate_cuda if self.cuda else _iterate
            for iter_cnt in range(iterations):
                
                # Update values according to the rules of Mandelbrot set
                Z, C, pos = _iter_func(Z, C, self.I, pos, iter_cnt)
                
                # see if drawing is needed
                if self.draw_signal:
                    self.draw_obj = self.draw_thread.submit( self._output,
                        cp.asnumpy(self.I.copy()) if self.cuda else self.I.copy(),
                        iter_cnt/iterations )
                    self.draw_signal = False
                
                # see if kill is coming
                if self.kill_signal: break
            
            
            
        ### Multithread condition
        else:
            # Progress report
            progress = [0]*self.max_workers
            results = []
            
            # Split
            split = list(range(0, size[0], size[0]//self.max_workers))
            if len(split) < self.max_workers+1: split += [size[0]]
            else: split[-1] = size[0]
            
            # Start
            with ThreadPoolExecutor(max_workers=self.max_workers) as exe:
            
                # Spliting Z, C, pos accordingly
                for i, (_s, _e) in enumerate(zip(split[:-1], split[1:])):
                    results.append( exe.submit( _looping,
                        Z[_s*size[1]:_e*size[1]], C[_s*size[1]:_e*size[1]],
                        self.I, pos[_s*size[1]:_e*size[1], :],
                        iterations, progress, i ) )
                
                # Iterate through workers
                for iter_cnt in range(iterations):
                    while min(progress) <= iter_cnt:
                        time.sleep(0.1)
                        pass

                    # see if drawing is needed
                    if self.draw_signal:
                        self.draw_obj = self.draw_thread.submit(
                            self._output, self.I.copy(), iter_cnt/iterations )
                        self.draw_signal = False
                        
                    # see if kill is coming
                    if self.kill_signal: break
                    
                # Clean up mess
                for r in results: r.cancel()
        
        ### Ends
        # Delete everyting but I for drawing.
        if self.cuda: self.I = cp.asnumpy(self.I)
        
        return None


    def running(self):
        return self.main_thread.is_alive()
        
    def kill_job(self):
        self.kill_signal = True
        self.main_thread.join()
        return None
        
    def get_snapshot(self):
        if not self.main_thread.is_alive():
            self.draw_obj = self.draw_thread.submit( self._output, self.I.copy(), 1 )
        else:
            self.draw_signal = True
            while self.draw_signal: ...
        return self.draw_obj.result()
        
    def change_coloring(self, style):
        num_style = {'icy': 0, 'flamboyant': 1, 'flame': 2}.get(style, style)
        print(num_style)
        if type(num_style) is not int or not 0 <= num_style <= 2: return False
        self.draw_type = num_style
        return True
    
    _output = coloring_func
        
        

def _looping(Z, C, I, pos, iterations, progress, i):
    for iter_cnt in range(iterations):
        Z, C, pos = _iterate(Z, C, I, pos, iter_cnt)
        progress[i] = iter_cnt+1
        if not Z.size:
            progress[i] = iterations
            break
    return Z, C, pos

@nb.jit(nopython=True, nogil=True)
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
    