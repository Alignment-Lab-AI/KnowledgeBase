import sys
import datetime
from PIL import ImageGrab
from Xlib import X, XK, display
from Xlib.ext import record
from Xlib.error import XError
from Xlib.protocol import rq

from Base.models import Process, Window, Geometry, Click, Keys, Activity, Screenshot

def state_to_idx(state):  # this could be a dict, but I might want to extend it.
    if state == 1:
        return 1
    if state == 128:
        return 4
    if state == 129:
        return 5
    return 0


class Sniffer:
    def __init__(self, db_conn):
        self.keysymdict = {}
        for name in dir(XK):
            if name.startswith("XK_"):
                self.keysymdict[getattr(XK, name)] = name[3:]

        self.key_hook = lambda x: True
        self.mouse_button_hook = lambda x: True
        self.mouse_move_hook = lambda x: True
        self.screen_hook = lambda x: True

        self.contextEventMask = [X.KeyPress, X.MotionNotify]

        self.the_display = display.Display()
        self.keymap = self.the_display._keymap_codes

        self.atom_NET_WM_NAME = self.the_display.intern_atom('_NET_WM_NAME')
        self.atom_UTF8_STRING = self.the_display.intern_atom('UTF8_STRING')
        
        self.db_conn = db_conn
        self.last_screenshot_hash = None

    def run(self):
        while True:
            event = self.the_display.next_event()
            self.process_event(event)

    def process_event(self, event):
        cur_class, cur_window, cur_name = self.get_cur_window()
        if cur_class:
            cur_geo = self.get_geometry(cur_window)
            if cur_geo:
                self.screen_hook(cur_class,
                                 cur_name,
                                 cur_geo.xpos,
                                 cur_geo.ypos,
                                 cur_geo.width,
                                 cur_geo.height)
                                 
                screenshot = ImageGrab.grab()
                screenshot_hash = hash(screenshot.tobytes())
                if screenshot_hash != self.last_screenshot_hash:
                    self.last_screenshot_hash = screenshot_hash
                    # Save screenshot to database
                    process_id = self.get_process_id(cur_class)
                    window_id = self.get_window_id(cur_name, process_id)
                    geometry_id = self.save_geometry(cur_geo)
                    self.save_screenshot(process_id, window_id, geometry_id, screenshot)

        if event.type in [X.KeyPress]:
            self.key_hook(*self.key_event(event))
        elif event.type in [X.ButtonPress]:
            self.mouse_button_hook(*self.button_event(event))
        elif event.type == X.MotionNotify:
            self.mouse_move_hook(event.root_x, event.root_y)
        elif event.type == X.MappingNotify:
            self.the_display.refresh_keyboard_mapping()
            newkeymap = self.the_display._keymap_codes
            print('Change keymap!', newkeymap == self.keymap)
            self.keymap = newkeymap

    def get_key_name(self, keycode, state):
        state_idx = state_to_idx(state)
        cn = self.keymap[keycode][state_idx]
        if cn < 256:
            return chr(cn).decode('latin1')
        else:
            return self.lookup_keysym(cn)

    def key_event(self, event):
        flags = event.state
        modifiers = []
        if flags & X.ControlMask:
            modifiers.append('Ctrl')
        if flags & X.Mod1Mask:  # Mod1 is the alt key
            modifiers.append('Alt')
        if flags & X.Mod4Mask:  # Mod4 should be super/windows key
            modifiers.append('Super')
        if flags & X.ShiftMask:
            modifiers.append('Shift')
        return (event.detail,
                modifiers,
                self.get_key_name(event.detail, event.state),
                event.sequence_number == 1)

    def button_event(self, event):
        return event.detail, event.root_x, event.root_y

    def lookup_keysym(self, keysym):
        if keysym in self.keysymdict:
            return self.keysymdict[keysym]
        return "[%d]" % keysym

    def get_wm_name(self, win):
        """
        Custom method to query for _NET_WM_NAME first, before falling back to
        python-xlib's method, which (currently) only queries WM_NAME with
        type=STRING."""


        d = win.get_full_property(self.atom_NET_WM_NAME, self.atom_UTF8_STRING)
        if d is None or d.format != 8:
            # Fallback.
            r = win.get_wm_name()
            if r:
                return r.decode('latin1')  # WM_NAME with type=STRING.
        else:
            try:
                return d.value.decode('utf8')
            except UnicodeError:
                return d.value.encode('utf8').decode('utf8')

    def get_cur_window(self):
        i = 0
        cur_class = None
        cur_window = None
        cur_name = None
        while i < 10:
            try:
                cur_window = self.the_display.get_input_focus().focus
                cur_class = None
                cur_name = None
                while cur_class is None:
                    if type(cur_window) is int:
                        return None, None, None

                    cur_name = self.get_wm_name(cur_window)
                    cur_class = cur_window.get_wm_class()

                    if cur_class:
                        cur_class = cur_class[1]
                    if not cur_class:
                        cur_window = cur_window.query_tree().parent
            except XError:
                i += 1
                continue
            break
        cur_class = cur_class or ''
        cur_name = cur_name or ''
        return cur_class.decode('latin1'), cur_window, cur_name

    def get_geometry(self, cur_window):
        i = 0
        geo = None
        while i < 10:
            try:
                geo = cur_window.get_geometry()
                break
            except XError:
                i += 1
        return Geometry(geo.x, geo.y, geo.width, geo.height) if geo else None
    
    def get_process_id(self, process_name):
        process = self.db_conn.execute("SELECT id FROM process WHERE name = ?", (process_name,)).fetchone()
        if process:
            return process[0]
        else:
            self.db_conn.execute("INSERT INTO process (name) VALUES (?)", (process_name,))
            self.db_conn.commit()
            return self.db_conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    def get_window_id(self, window_title, process_id):
        window = self.db_conn.execute("SELECT id FROM window WHERE title = ? AND process_id = ?", 
                                      (window_title, process_id)).fetchone()
        if window:
            return window[0]
        else:
            self.db_conn.execute("INSERT INTO window (title, process_id) VALUES (?, ?)", 
                                 (window_title, process_id))
            self.db_conn.commit()
            return self.db_conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    def save_geometry(self, geometry):
        self.db_conn.execute("""
            INSERT INTO geometry (xpos, ypos, width, height) 
            VALUES (?, ?, ?, ?)
        """, (geometry.xpos, geometry.ypos, geometry.width, geometry.height))
        self.db_conn.commit()
        return self.db_conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    def save_screenshot(self, process_id, window_id, geometry_id, screenshot):
        self.db_conn.execute("""
            INSERT INTO screenshot (process_id, window_id, geometry_id, image)
            VALUES (?, ?, ?, ?)
        """, (process_id, window_id, geometry_id, screenshot.tobytes()))
        self.db_conn.commit()