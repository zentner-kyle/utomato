#!/usr/bin/env python3
import calendar
import curses
import curses.ascii
import curses.textpad
import json
import os
import os.path
import time

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
        remaining = self.remaining() 
        fstr = " {:2}:{:02}"
        if remaining < 0:
            fstr = "-" + fstr[1:]
            remaining = -remaining
        return fstr.format(remaining // 60, 
                           remaining %  60)

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
    string = json.dumps(_done_tasks, indent=True)
    save_to_db(string)

time_format_str = "%Y.%m.%d %H:%M:%S (%A) %Z"

def format_time(t):
    return time.strftime(time_format_str, t)

def parse_time(t):
    return to_sec(time.strptime(t, time_format_str))

def save_to_db(contents):
    filename = (format_time(time.localtime()) +
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
    pad_window = window.subpad(1, window.getmaxyx()[1], 2, 0)
    pad = curses.textpad.Textbox(pad_window)
    on_break = False
    while True:
        try:
            char = window.getch()
        except KeyboardInterrupt:
            break
# Check if char is an ascii value.
# Unfortunately, curses.ascii.isascii returns True for -1.
# So it can't be used here.
        if char in range(0x80):
            key = chr(char)
            if key == 's':
                timer.stop()
            elif key == 'q':
                break
            elif key == 'f' or key in '\n ' and timer.done():
                if on_break:
                    old_text = pad.gather().strip()
                    pad_window.addstr(0, 0, ' ' * len(old_text))
                    pad_window.addstr(0, 0, 'Break.')
                    new_text = pad.edit().strip()
                    add_done([new_text,
                        format_time(time.localtime(calendar.timegm(timer.start_time))),
                        format_time(time.localtime())])
                    pad_window.addstr(0, 0, ' ' * len(new_text))
                    pad_window.addstr(0, 0, old_text)
                    pad_window.noutrefresh()
                    timer.duration = work_duration
                    timer.stop()
                    on_break = False
                else:
                    if timer.running():
                        add_done([pad.edit().strip(),
                            format_time(time.localtime(calendar.timegm(timer.start_time))),
                            format_time(time.localtime())])
                    timer.duration = break_duration
                    timer.start()
                    on_break = True
            elif key in '\n ':
                if not timer.running():
                    timer.start()
        title.put()
        timer.put()
        curses.doupdate()

def main_wrapper(window):
    try:
        main(window)
    except Exception as e:
        save_db()
        raise e

os.environ['TERM'] = 'rxvt-unicode-256color'
curses.wrapper(main_wrapper)
save_db()
