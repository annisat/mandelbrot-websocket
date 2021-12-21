from collections import namedtuple
Section = namedtuple("Section", "up, down, high")
import numpy as np
from math import floor



def split2sec(split, I):
    sec = []
    sec_s = 0
    for interval in split:
        sec_e = sec_s + interval
        mask = np.where((sec_s<I if sec_s else sec_s<=I) & (I<=sec_e), 1, 0)
        sec.append(Section._make([
            mask*(I-sec_s)*255/interval, mask*(sec_e-I)*255/interval, mask*255]))
        sec_s = sec_e
    return sec



def coloring_func(self, I, prog_snapshot):
    ### Prepare I to log scale
    I = np.log10(I+1)
    I = np.clip(I.astype(np.float32)/np.log10(self.iterations+1), 0, 1)
        
    ### Choose style
    # 0: icy; Black -> Blue -> Cyan -> White
    # 1: flamboyant:
    # 2: flame:
    draw_type = self.draw_type
    split = {
        1: [255,255,255,255,255,255,255,255,765],
        }.get(draw_type, [255, 255, 255])
    
    I *= sum(split)
    sec = split2sec(split, I)
    
    blue, green, red = {
        0: _icy, 1: _flamboyant, 2: _flame,
        }.get(draw_type, 0)(sec)
    
    ### Convert data type and return
    return np.stack( [
        blue.astype(np.uint8), green.astype(np.uint8), red.astype(np.uint8), ],
        axis=-1 ), floor(prog_snapshot*1000)/10



def _icy(sec):
    return \
        sec[0].up + sec[1].high + sec[2].high,\
                    sec[1].up   + sec[2].high,\
                                  sec[2].up,

def _flamboyant(sec):
    return \
        sec[0].up   + sec[1].high + sec[2].high + sec[3].down               + sec[5].up +\
        sec[6].high + sec[7].high + sec[8].high,\
                      sec[1].up   + sec[2].high + sec[3].down + sec[4].up   + sec[5].high +\
        sec[6].down + sec[7].up   + sec[8].high,\
                                    sec[2].up   + sec[3].high + sec[4].high + sec[5].high +\
        sec[6].down               + sec[8].up,

def _flame(sec):
    return \
                                  sec[2].up,\
                    sec[1].up   + sec[2].high,\
        sec[0].up + sec[1].high + sec[2].high,