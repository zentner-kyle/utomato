#!/usr/bin/env python3
import curses
import curses.textpad
import curses.ascii
import time
import calendar
import os.path
import json

class Title(object):

    def __init__(self, window):
        self.window = window
        self.string = "uTomato"

    def put(self):
        self.window.addstr(0, 0, self.string)
        self.window.chgat(0, 0, len(self.string), curses.A_BOLD)
        self.window.noutrefresh()

def to_sec(t):
    if isinstance(t, time.struct_time):
        return calendar.timegm(t)
    else:
        return t

class Timer(object):

    def __init__(self, window, duration):
        self.window = window
        self.duration = to_sec(duration)
        self.start_time = None
        self.finished = False

    def start(self):
        self.start_time = time.gmtime()
        self.finished = False

    def accumulated(self):
        if self.start_time is None:
            return 0
        return to_sec(time.gmtime()) - to_sec(self.start_time)

    def remaining(self):
        return self.duration - self.accumulated()

    def done(self):
        if self.finished:
            return True
        if self.start_time is None:
            return False
        time_out = self.remaining() <= 0
        self.finished = time_out
        return time_out

    def get_str(self):
        return "{:2}:{:02}".format(self.remaining() // 60, 
                                   self.remaining() %  60)

    def stop(self):
        self.start_time = None
        self.finished = False

    def put(self):
        t_str = self.get_str()
        self.window.addstr(0, 0, t_str)
        self.window.noutrefresh()

    def finish(self):
        self.stop()
        self.finished = True

    def running(self):
        return self.start_time is not None

_done_tasks = []

def add_done(task):
    _done_tasks.append(task)

def save_db():
    string = json.dumps(_done_tasks)
    save_to_db(string)

def save_to_db(contents):
    filename = (time.strftime("%Y.%m.%d %H:%M:%S (%A)", time.localtime()) +
                ".tasklist")
    with open(filename, mode='a+') as f:
        try:
            if not f.read():
                f.write(contents)
                return
        except Exception:
            pass
        print("Problem writing {}!".format(filename))
        print("The contents which could not be saved are:")
        print(contents)


work_duration = 25 * 60
break_duration = 5 * 60

class NoKey(Exception):
    pass

def main(window):
    curses.use_default_colors()
    window.timeout(200)
    title = Title(window.derwin(0, 0))
    timer = Timer(window.derwin(1, 0), work_duration)
    pad = curses.textpad.Textbox(window.subpad(1, 80, 2, 0))
    on_break = False
    while True:
        #try:
            #char = window.getch()
        #except KeyboardInterrupt:
            #break
        #if char != -1:
            #key = chr(char)
        try:
            key = window.getkey()
        except KeyboardInterrupt as e:
            raise e
        except Exception:
            pass
        else:
            if key == '\n':
                if not timer.running():
                    timer.start()
            elif key == 's':
                timer.stop()
            elif key == 'q':
                break
            elif key == 'f':
                timer.finish()
        title.put()
        timer.put()
        if timer.done():
            if on_break:
                timer.duration = work_duration
                timer.stop()
                on_break = False
            else:
                add_done(pad.edit())
                timer.duration = break_duration
                timer.start()
                on_break = True
        curses.doupdate()

def main_wrapper(window):
    try:
        main(window)
    except Exception:
        pass

curses.wrapper(main_wrapper)
save_db()
