from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler



def update_time(arg_func):
    def rtn_func(self, sid, *args, **kwargs):
        self.data[sid]['updated_at'] = datetime.now()
        return arg_func(self, sid, *args, **kwargs)
    return rtn_func

class RedisIpsum():
    def __init__(self):
        self.data = {}
        self.cleaner = BackgroundScheduler()
        self.cleaner.add_job(self.clean_trash, 'interval', hours=3)
        self.cleaner.start()
        
        
    def add(self, sid, worker):
        if sid in self.data: raise IndexError("sid already exists")
        self.data[sid] = {
            "worker": worker,
            "stop_signal": False,
            "pause_signal": False,
            "updated_at": datetime.now(),
        }
    
    def delete(self, sid):
        if sid in self.data:
            self.data[sid]['worker'].kill_job()
            del self.data[sid]
    
    def clean_trash(self):
        trash_key = []
        for key in self.data.keys():
            if datetime.now() - self.data[key]['updated_at'] > timedelta(hours=6):
                trash_key.append(key)
        for key in trash_key: del self.data[key]
    
    @update_time
    def worker(self, sid):
        return self.data[sid]['worker']
    @update_time
    def stop_signal(self, sid, action=None):
        if action is not None: self.data[sid]['stop_signal'] = action
        return self.data[sid]['stop_signal']
    
    def pause_signal(self, sid, action=None):
        if action is not None: self.data[sid]['pause_signal'] = action
        return self.data[sid]['pause_signal']
    