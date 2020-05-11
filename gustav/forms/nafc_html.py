# -*- coding: utf-8 -*-

# Copyright (c) 2010-2020 Christopher Brown
#
# This file is part of gustav.
#
# gustav is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# gustav is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with gustav.  If not, see <http://www.gnu.org/licenses/>.
#
# Comments and/or additions are welcome. Send e-mail to: cbrown1@pitt.edu.
#
#Todo check for Python 2 compatibility of these libraries
import webbrowser
import threading
import http.server
import socketserver
from string import Template

# Good libs
import os,sys



# Adapted from https://gist.github.com/bradmontgomery/2219997
class CustomRequestHandler(http.server.SimpleHTTPRequestHandler):
    Interface = None

    if (os.name=='nt'): # Windows
        nullFile = 'C:\\nul'
    elif (os.name == 'posix'): # Linux
        nullFile = '/dev/null'

    def connect_interface(self,InterfaceInstance):
        self.Interface = InterfaceInstance

    # https://stackoverflow.com/questions/25360798/save-logs-simplehttpserver
    # Output is not needed from Server
    def log_message(self, format, *args):
        log_file = open(self.nullFile, 'a', 1) # output not needed
        log_file.write("%s - - [%s] %s\n" %
                            (self.client_address[0],
                             self.log_date_time_string(),
                             format%args))

    def set_html_headers(self):
        self.send_response(200)
        self.send_header("Content-type","text/html")
        self.end_headers()

    def set_ajax_headers(self):
        self.send_response(200)
        self.send_header("Content-type","application/json")
        self.end_headers()

    def parse_json(data):
        return json.loads(data_string)

    def do_GET(self):
        #Response to page fetch happens here
        print("Receieved GET")
        self.set_html_headers()
        self.wfile.write(self.Interface.generate_page())

    def do_POST(self):
        # Response to Website AJAX happens here
        length = int(self.headers['Content-Length'])
        data_string = self.rfile.read(length).decode('UTF-8')
        try:
            data = parse_json(data)
            result = data['dummy_val']
        except:
            result = 'Error parsing data'

        response_str = json.dumps({"result":result})
        self.wfile.write(bytes(response_str,'UTF-8'))

class CustomTCPServer(socketserver.TCPServer):
    def __init__(self,server_address,RequestHandler,InterfaceInstance):
        RequestHandler.Interface = InterfaceInstance # TODO clean this up
        super(CustomTCPServer,self).__init__(server_address,RequestHandler)

class Interface():
    def start_server_thread(self):
        print("Serving on port",self.port)
        try:
            self.server.serve_forever()
        except:
            print("Unexpected error on server:", sys.exc_info()[0])
            sys.exit(1) # Don't continue on an error

    def __init__(self,alternatives=2, prompt="Choose an alternative"):
        self.title_l_str = "Gustav n-AFC!"
        self.title_c_str = ""
        self.title_r_str = ""
        self.notify_l_str = ""
        self.notify_l_show = False
        self.notify_r_str = ""
        self.notify_r_show = False
        self.notify_pad = True
        self.notify_offset_v = 2                # Vertical offset of notifications from top of window
        self.status_l_str = "Press '/' to quit"
        self.status_c_str = ""
        self.status_r_str = ""
        self.prompt = prompt

        self.keypress_wait = .005 # Sleep time in sec during keypress loop to avoid cpu race
                                  # Longer values are better for slower machines
        self.port = 8000
        while True:
            try:
                self.server = CustomTCPServer(("",self.port),CustomRequestHandler,self)
                break
            except OSError:
                self.port += 1

        #TODO clean this up
        self.browser = webbrowser.get() # get befault browser
        self.browser.open("http://localhost:" + str(self.port))
        self.server_thread = threading.Thread(target=self.start_server_thread(),daemon=True) # start server in background

    def destroy(self):
        self.server.server_close()

        #close_url = Template("localhost:$port/close.html").substitute({"port":self.port})
        #self.browser.open(close_url,new=0)

    def generate_page(self):
        return bytes("<!DOCTYPE html>\n<html><body><p>Hello World</p></body></html>",'UTF-8')

    def redraw(self):
        """Draw entire window

            Called when term is resized, or manually by user

        """
        return
    
    def rectangle(self, win, uly, ulx, lry, lrx):
        """Draw a rectangle with corners at the provided upper-left
            and lower-right coordinates.

            This is not used ATM, the rect for the posbar is drawn by hand to 
            allow more control over style

            https://stackoverflow.com/questions/52804155/extending-curses-rectangle-box-to-edge-of-terminal-in-python
        """
        return

    def round_to(self, x, base):
        """Rounds x to the nearest base, which can be any float
        """
        recip = 1/float(base)
        return round(x * recip) / recip


    #########################################################################
    ## USER FACING FUNCTIONS BELOW

    def get_resp(self, timeout=None):
        """Wait modally for a keypress, returns the key as a char. 
            If you want to evaluate arrow keys etc, use ord:

                ret = get_resp()
                if ord(ret) == curses.KEY_LEFT:
                    # do something to the left

            If timeout is None, then block. If it is a float, wait at 
            least that many seconds, return None if no input.
        """
        return

    def update_Title_Left(self, s, redraw=False):
        """Update the text on the left side of the title bar

            redraw is a bool specifying whether to redraw window. 
            A window redraw can also be set with update.
        """
        self.title_l_str = s
        if redraw: 
            self.redraw()

    def update_Title_Center(self, s, redraw=False):
        """Update the text in the center of the title bar

            redraw is a bool specifying whether to redraw window. 
            A window redraw can also be set with update.
        """
        self.title_c_str = s
        if redraw: 
            self.redraw()

    def update_Title_Right(self, s, redraw=False):
        """Update the text on the right side of the title bar

            redraw is a bool specifying whether to redraw window. 
            A window redraw can also be set with update.
        """
        self.title_r_str = s
        if redraw: 
            self.redraw()

    def update_Notify_Left(self, s, show=None, redraw=False):
        """Update the notify text to the left of the face.

            show is a bool specifying whether to show the text,
            set to None to leave this param unchanged [default].
            show can also be set with show_Notify_Left.

            redraw is a bool specifying whether to redraw window. 
            A window redraw can also be set with update.
        """
        self.notify_l_str = s
        if show is not None:
            self.notify_l_show = show
        if redraw: 
            self.redraw()

    def update_Notify_Right(self, s, show=None, redraw=False):
        """Update the notify text to the left of the face.

            show is a bool specifying whether to show the text,
            set to None to leave this param unchanged [default].
            show can also be set with show_Notify_Left.

            redraw is a bool specifying whether to redraw window. 
            A window redraw can also be set with update.
        """
        self.notify_r_str = s
        if show is not None:
            self.notify_r_show = show
        if redraw: 
            self.redraw()

    def show_Notify_Left(self, show=None, redraw=True):
        """Show the left notify text

            If show==None, toggle. Otherwise show should be a bool.

            redraw is a bool specifying whether to redraw window. 
            A window redraw can also be set with update.
        """        
        if show is not None:
            self.notify_l_show = show
        else:
            self.notify_l_show = not self.notify_l_show

        if redraw: 
            self.redraw()

    def show_Notify_Right(self, show=None, redraw=True):
        """Show the right notify text

            If show==None, toggle. Otherwise show should be a bool.

            redraw is a bool specifying whether to redraw window. 
            A window redraw can also be set with update.
        """        

        if show is not None:
            self.notify_r_show = show
        else:
            self.notify_r_show = not self.notify_r_show

        if redraw: 
            self.redraw()

    def update_Status_Left(self, s, redraw=False):
        """Update the text on the left side of the status bar

            redraw is a bool specifying whether to redraw window. 
            A window redraw can also be set with update.
        """
        self.status_l_str = s
        if redraw: 
            self.redraw()

    def update_Status_Center(self, s, redraw=False):
        """Update the text in the center of the status bar

            redraw is a bool specifying whether to redraw window. 
            A window redraw can also be set with update.
        """
        self.status_c_str = s
        if redraw: 
            self.redraw()

    def update_Status_Right(self, s, redraw=False):
        """Update the text on the right side of the status bar

            redraw is a bool specifying whether to redraw window. 
            A window redraw can also be set with update.
        """
        self.status_r_str = s
        if redraw: 
            self.redraw()

    def update(self):
        self.redraw()

    ## NAFC-specific user functions

    def update_Prompt(self, s, show=True, redraw=False):
        """Update the text of the prompt

            redraw is a bool specifying whether to redraw window. 
            A window redraw can also be set with update.
        """
        self.prompt = s
        self.prompt_show = show

        if redraw: 
            self.redraw()

    def set_color(self, button, color, redraw=True):
        """Sets the face color of the specified button

            Available colors are (you can use inds or strings):

                0 - None (Black; same as background)
                1 - Grey
                2 - Green
                3 - Red
                4 - Yellow
        """
        if isinstance(button, int):
            buttons = [button]
        elif isinstance(button, str):
            buttons = [self.alternatives.index(button)]
        else:
            buttons = []
            for b in button:
                if isinstance(b, int):
                    buttons.append(b)
                else:
                    buttons.append(self.alternatives.index(b))

        if isinstance(color, int):
            colos = [color]
        elif isinstance(color, str):
            colors = [self.button_color_names.index(color)]
        else:
            colors = []
            for c in color:
                if isinstance(c, int):
                    colors.append(c)
                else:
                    colors.append(self.button_color_names.index(c))

        for b,c in zip(buttons,colors):
            self.button_colors[b] = c

        if redraw:
            self.redraw()

    def set_border(self, button, border, redraw=True):
        """Sets the border of the specified button

            Button can be an int to specify a particular button by index, 
            a str to specify label, or a list of ints or strings. 

            If button is an int, then border must be an int. If 
            button is a list, border can be an int, in which case each 
            button in the list will be set to border. Or border can be
            a list, in which case it must be the same len as button.

            Available borders are (you can use inds or strings):

                0 - None (no border)
                1 - Light
                2 - Heavy
                3 - Double
        """
        if isinstance(button, int):
            buttons = [button]
        elif isinstance(button, str):
            buttons = [self.alternatives.index(button)]
        else:
            buttons = []
            for b in button:
                if isinstance(b, int):
                    buttons.append(b)
                else:
                    buttons.append(self.alternatives.index(b))

        if isinstance(border, int):
            borders = [border]
        elif isinstance(border, str):
            borders = [self.button_border_names.index(border)]
        else:
            borders = []
            for b in border:
                if isinstance(b, int):
                    borders.append(b)
                else:
                    borders.append(self.button_border_names.index(b))

        for b,c in zip(buttons,borders):
            self.button_borders[b] = c

        if redraw:
            self.redraw()

    def get_button_colors(self):
        return self.button_color_names

    def get_button_borders(self):
        return self.button_border_names

    def show_Buttons(self, show=None, redraw=True):
        """Show the position bar

           If show==None, toggle show and force a redraw. Otherwise 
            show should be a bool.

            redraw is a bool specifying whether to redraw window. 
            A window redraw can also be set with update.
        """        
        if show is not None:
            self.buttons_show = show
            self.redraw()
        else:
            self.buttons_show = not self.buttons_show
            if redraw: 
                self.redraw()

    def show_Prompt(self, show=None, redraw=True):
        """Show the prompt

           If show==None, toggle show and force a redraw. Otherwise 
            show should be a bool.

            redraw is a bool specifying whether to redraw window. 
            A window redraw can also be set with update.
        """        
        if show is not None:
            self.prompt_show = show
            self.redraw()
        else:
            self.prompt_show = not self.prompt_show
            if redraw: 
                self.redraw()

    # High precision timer stuff:
    if (os.name=='nt'): #for Windows:
        def timestamp_us(self):
            "return a high-precision timestamp in microseconds (us)"
            tics = ctypes.c_int64()
            freq = ctypes.c_int64()

            #get ticks on the internal ~2MHz QPC clock
            ctypes.windll.Kernel32.QueryPerformanceCounter(ctypes.byref(tics)) 
            #get the actual freq. of the internal ~2MHz QPC clock
            ctypes.windll.Kernel32.QueryPerformanceFrequency(ctypes.byref(freq))  

            t_us = tics.value*1e6/freq.value
            return t_us

        def timestamp_ms(self):
            "return a high-precision timestamp in milliseconds (ms)"
            tics = ctypes.c_int64()
            freq = ctypes.c_int64()

            #get ticks on the internal ~2MHz QPC clock
            ctypes.windll.Kernel32.QueryPerformanceCounter(ctypes.byref(tics)) 
            #get the actual freq. of the internal ~2MHz QPC clock 
            ctypes.windll.Kernel32.QueryPerformanceFrequency(ctypes.byref(freq)) 

            t_ms = tics.value*1e3/freq.value
            return t_ms

    elif (os.name=='posix'): #for Linux:

        #Constants:
        CLOCK_MONOTONIC_RAW = 4 # see <linux/time.h> here: https://github.com/torvalds/linux/blob/master/include/uapi/linux/time.h

        #prepare ctype timespec structure of {long, long}
        class timespec(ctypes.Structure):
            _fields_ =\
            [
                ('tv_sec', ctypes.c_long),
                ('tv_nsec', ctypes.c_long)
            ]

        #Configure Python access to the clock_gettime C library, via ctypes:
        #Documentation:
        #-ctypes.CDLL: https://docs.python.org/3.2/library/ctypes.html
        #-librt.so.1 with clock_gettime: https://docs.oracle.com/cd/E36784_01/html/E36873/librt-3lib.html #-
        #-Linux clock_gettime(): http://linux.die.net/man/3/clock_gettime
        librt = ctypes.CDLL('librt.so.1', use_errno=True)
        clock_gettime = librt.clock_gettime
        #specify input arguments and types to the C clock_gettime() function
        # (int clock_ID, timespec* t)
        clock_gettime.argtypes = [ctypes.c_int, ctypes.POINTER(timespec)]

        def timestamp_s(self):
            "return a high-precision timestamp in seconds (sec)"
            t = self.timespec()
            #(Note that clock_gettime() returns 0 for success, or -1 for failure, in
            # which case errno is set appropriately)
            #-see here: http://linux.die.net/man/3/clock_gettime
            if self.clock_gettime(self.CLOCK_MONOTONIC_RAW , ctypes.pointer(t)) != 0:
                #if clock_gettime() returns an error
                errno_ = ctypes.get_errno()
                raise OSError(errno_, os.strerror(errno_))
            return t.tv_sec + t.tv_nsec*1e-9 #sec 

        def timestamp_us(self):
            "return a high-precision timestamp in microseconds (us)"
            return self.timestamp_s()*1e6 #us 

        def timestamp_ms(self):
            "return a high-precision timestamp in milliseconds (ms)"
            return self.timestamp_s()*1e3 #ms 

    # Other timing functions
    # Use with caution as these wait functions will cause cpu race when wait times are longer
    # If you don't need the precision or you need longer wait times, consider using time.sleep(s)
    def wait_ms(self, delay_ms):
        "Wait (block) for delay_ms milliseconds (ms) using a high-precision timer"
        t_start = self.timestamp_ms()
        while (self.timestamp_ms() - t_start < delay_ms):
            pass #do nothing 
        return

    def wait_us(self, delay_us):
        "Wait (block) for delay_us microseconds (us) using a high-precision timer"
        t_start = self.timestamp_us()
        while (self.timestamp_us() - t_start < delay_us):
            pass #do nothing 
        return 

if __name__ == "__main__":
    # Initialize interface
    # Alternatives can be a number, in which case labels will be "1", "2" etc., or
    # a list where len = # of alternatives, and each item is a single unique char
    alternatives = ['A', 'B']
    interface = Interface(alternatives=alternatives)
    # Add some text
    interface.show_Prompt(False)
    interface.show_Buttons(False)
    interface.show_Notify_Left(False)
    interface.update_Notify_Right("Press any key\nto begin", show=True, redraw=True)
    # Wait for a keypress
    ret = interface.get_resp()

    # Update some text, show marker
    interface.show_Notify_Left(False)
    interface.show_Prompt(False)
    interface.show_Buttons(False)
    interface.update_Title_Right( "A {:}-AFC interface".format(len(alternatives)))
    interface.update_Notify_Left( "Press space to\nstart a trial", show=True)
    interface.update_Notify_Right("Listen!", show=False, redraw=True)

    # Enter a blocking loop waiting for keypresses
    # Debugging:
    #loops = 0
    trial = 1
    waiting = True
    while waiting:
        key = interface.get_resp(timeout=1.) # Wait for keypress
        # If you set a timeout for get_resp, you need to hand key==None, which is a wait
        if key == None:
            # Nothing happened, keep waiting
            pass
        elif key in ('/', 'q'):
            # User requested to quit. Exit while loop
            waiting = False
            interface.show_Notify_Left()
        elif key == 'l':
            interface.show_Notify_Left()
        elif key == 'r':
            interface.show_Notify_Right()
        elif key == 'p':
            interface.show_Prompt(redraw=True)
        elif key == 's':
            interface.show_Buttons()
        elif key.upper() in alternatives: # User upper-case so subj can just hit a key without shift
            interface.show_Prompt(False)
            interface.show_Buttons(True, redraw=True)
            for i in range(3):
                interface.set_color(key.upper(), 'Green', redraw=True)
                interface.wait_ms(100)
#                time.sleep(.1)
                interface.set_color(key.upper(), 'None', redraw=True)
                interface.wait_ms(100)
#                time.sleep(.1)
            interface.show_Notify_Left(True)
            interface.show_Buttons(False)
            interface.show_Prompt(False, redraw=True)

        elif key == " ":
            interface.update_Status_Right("Trial {:}".format(trial))
            trial += 1
            interface.show_Notify_Left(False)    # Hide the 'press space' text since they just pressed it
            interface.show_Notify_Right(True)    # Show the listen text
            interface.show_Prompt(False)         # Don't show prompt during presentation b/c we don't want a response
            interface.show_Buttons(True, redraw=True) # Show buttons so user gets visual feedback on interfal playback
            interface.wait_ms(750)
#            time.sleep(.75)
            # We would play a trial here, with both intervals being .5 s long, and the isi being .25 s
            for i in range(len(interface.alternatives)):
                interface.set_border(i, 'Heavy', redraw=True)
                interface.wait_ms(500)
#                time.sleep(.5)
                interface.set_border(i, 'Light', redraw=True)
                interface.wait_ms(250)
                #time.sleep(.25)
            interface.show_Notify_Right(False)
            interface.show_Prompt(True, redraw=True)

    # We are quitting. Let use know, and wait for final keypress to exit interface
    interface.update_Status_Left("")
    interface.update_Notify_Left("Finished.\nPress any key\nto exit...", show=True)
    interface.show_Notify_Right(False, redraw=True)
    ret = interface.get_resp()

    # # # Screenshot layout:
    # interface.update_Status_Left("Status Bar Left")
    # interface.update_Status_Center("Status Bar Center")
    # interface.update_Status_Right("Status Bar Right")

    # interface.update_Title_Left("Title Bar Left")
    # interface.update_Title_Center("Title Bar Center")
    # interface.update_Title_Right("Title Bar Right")

    # interface.update_Notify_Left("Left Notify Area\nis centered\nand Multi-line", show=True)
    # interface.update_Notify_Right("Right Notify Area\nis centered\nand Multi-line", show=True)

    # interface.show_Buttons(True)
    # interface.set_color([0], 'Green')
    # interface.set_border([0,1], 'Heavy')

    # ret = interface.get_resp()

    interface.destroy()

