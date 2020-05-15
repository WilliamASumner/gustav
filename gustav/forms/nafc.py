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

""" This form is intended to be useful for running n-alternative forced-choice 
    experiments, in which a subject chooses one of a number of alternatives. 
    Each alternative is represented as a box, with an identifying char in the 
    middle. You can change the color of the box, and also the border style to 
    provide stimulus timing or response feedback. There is also a prompt that 
    can be updated, shown and hidden, as well as notification boxes and title 
    and status bars as well that should offer enough flexibility to show 
    whatever information is needed at any given time during an experiment.

    Because this is a curses interface, a screenshot can be pasted right here in 
    the text, alas without color:


┌Title Bar Left                               Title Bar Center                                 Title Bar Right┐
│                                                                                                             │
│                                                                                                             │
│                                                                                                             │
│         Left Notify Area                                                         Right Notify Area          │
│           is centered                                                               is centered             │
│          and Multi-line                                                           and Multi-line            │
│                                                                                                             │
│                                           Choose an alternative                                             │
│                                                                                                             │
│                                    ┏━━━━━━━━━━━━━┓      ┌─────────────┐                                     │
│                                    ┃▐███████████▌┃      │▐███████████▌│                                     │
│                                    ┃▐███████████▌┃      │▐███████████▌│                                     │
│                                    ┃▐█████A█████▌┃      │▐█████B█████▌│                                     │
│                                    ┃▐███████████▌┃      │▐███████████▌│                                     │
│                                    ┃▐███████████▌┃      │▐███████████▌│                                     │
│                                    ┗━━━━━━━━━━━━━┛      └─────────────┘                                     │
│                                                                                                             │
│                                                                                                             │
│                                                                                                             │
│                                                                                                             │
│                                                                                                             │
│                                                                                                             │
│                                                                                                             │
│                                                                                                             │
│                                                                                                             │
│                                                                                                             │
│                                                                                                             │
│                                                                                                             │
│                                                                                                             │
└Status Bar Left                             Status Bar Center                                Status Bar Right┘


    You can instantiate the form with:

        from gustav.forms import nafc as theForm
        interface = theForm.Interface(alternatives=3)

    All of the text areas (Title left, center, right, status left, center, 
    right, notify left, right) are format-able in code with foreground and 
    background colors. You can set the text of any of them with something like:

        interface.update_Title_Left("A new title")

    but to optimize performance (all those chars!), the screen is not updated 
    until you request it. This can be done either with:

        interface.update()

    ...or while you are setting text with:

        interface.update_Status_Center("Some status text", redraw=True)

    For title and status text, set to "" to clear. Notify text works a little 
    different, with a little more control since it is intended to be used more 
    for moment-to-moment notifications. So, redraw is True by default when 
    setting notify text, and there are also functions to show or hide each:

        interface.show_Notify_Left(True)

    You can explicitly pass a bool, or leave blank to toggle.

    ## Lateralization-specific notes

    The main function will be:

        interface.set_marker_pos(pos=fpos, diffuse=fdiffuse)

    Both pos and diffuse are expected to be floats 0>=1. You can set both or 
    either. You can also show/hide the position bar and marker with:

        interface.show_Position_Bar()

    ...or just the marker:

        interface.show_Marker()

    See the main loop at the bottom of this file for more usage examples.

    ## Other notes

    This form has been confirmed to work in a number of common terminals, 
    including xfce4-terminal, gnome-terminal, qterminal, konsole, and 
    xterm. It may require the TERM var to be set for color support:

        env TERM=xterm-256color python3 nafc.py

    It is working well on python 3.x. Much of the rendering is based on unicode 
    which is a mess in py2, and since py2 has reached end-of-life, not much work
    has gone into it...

    You can demo the interface by running it. In the demo, no stimulus will be
    presented, but you can get a sense of the different features of the form, 
    and how a force-choice experiment will look to the subject.

"""

#from __future__ import unicode_literals
import os, sys
import curses
import ctypes
import time
import math

class Interface():
    def __init__(self, alternatives=2, prompt="Choose an alternative"):
        # Initialize text areas
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

        # Some stuff for rendering
        # Dict so you can specify colors in curses using standard xterm 256-color palette names.
        self.palette256 = {'Black': 0, 'Maroon': 1, 'Green': 2, 'Olive': 3, 'Navy': 4, 'Purple': 5, 'Teal': 6, 'Silver': 7, 'Grey': 8, 'Red': 9, 'Lime': 10, 'Yellow': 11, 'Blue': 12, 'Fuchsia': 13, 'Aqua': 14, 'White': 15, 'Grey0': 16, 'NavyBlue': 17, 'DarkBlue': 18, 'Blue3-1': 19, 'Blue3-2': 20, 'Blue1': 21, 'DarkGreen': 22, 'DeepSkyBlue4-1': 23, 'DeepSkyBlue4-2': 24, 'DeepSkyBlue4-3': 25, 'DodgerBlue3': 26, 'DodgerBlue2': 27, 'Green4': 28, 'SpringGreen4': 29, 'Turquoise4': 30, 'DeepSkyBlue3': 31, 'DeepSkyBlue3': 32, 'DodgerBlue1': 33, 'Green3': 34, 'SpringGreen3': 35, 'DarkCyan': 36, 'LightSeaGreen': 37, 'DeepSkyBlue2': 38, 'DeepSkyBlue1': 39, 'Green3': 40, 'SpringGreen3': 41, 'SpringGreen2': 42, 'Cyan3': 43, 'DarkTurquoise': 44, 'Turquoise2': 45, 'Green1': 46, 'SpringGreen2': 47, 'SpringGreen1': 48, 'MediumSpringGreen': 49, 'Cyan2': 50, 'Cyan1': 51, 'DarkRed': 52, 'DeepPink4': 53, 'Purple4': 54, 'Purple4': 55, 'Purple3': 56, 'BlueViolet': 57, 'Orange4': 58, 'Grey37': 59, 'MediumPurple4': 60, 'SlateBlue3': 61, 'SlateBlue3': 62, 'RoyalBlue1': 63, 'Chartreuse4': 64, 'DarkSeaGreen4': 65, 'PaleTurquoise4': 66, 'SteelBlue': 67, 'SteelBlue3': 68, 'CornflowerBlue': 69, 'Chartreuse3': 70, 'DarkSeaGreen4': 71, 'CadetBlue': 72, 'CadetBlue': 73, 'SkyBlue3': 74, 'SteelBlue1': 75, 'Chartreuse3': 76, 'PaleGreen3': 77, 'SeaGreen3': 78, 'Aquamarine3': 79, 'MediumTurquoise': 80, 'SteelBlue1': 81, 'Chartreuse2': 82, 'SeaGreen2': 83, 'SeaGreen1': 84, 'SeaGreen1': 85, 'Aquamarine1': 86, 'DarkSlateGray2': 87, 'DarkRed': 88, 'DeepPink4': 89, 'DarkMagenta': 90, 'DarkMagenta': 91, 'DarkViolet': 92, 'Purple': 93, 'Orange4': 94, 'LightPink4': 95, 'Plum4': 96, 'MediumPurple3': 97, 'MediumPurple3': 98, 'SlateBlue1': 99, 'Yellow4': 100, 'Wheat4': 101, 'Grey53': 102, 'LightSlateGrey': 103, 'MediumPurple': 104, 'LightSlateBlue': 105, 'Yellow4': 106, 'DarkOliveGreen3': 107, 'DarkSeaGreen': 108, 'LightSkyBlue3': 109, 'LightSkyBlue3': 110, 'SkyBlue2': 111, 'Chartreuse2': 112, 'DarkOliveGreen3': 113, 'PaleGreen3': 114, 'DarkSeaGreen3': 115, 'DarkSlateGray3': 116, 'SkyBlue1': 117, 'Chartreuse1': 118, 'LightGreen': 119, 'LightGreen': 120, 'PaleGreen1': 121, 'Aquamarine1': 122, 'DarkSlateGray1': 123, 'Red3': 124, 'DeepPink4': 125, 'MediumVioletRed': 126, 'Magenta3': 127, 'DarkViolet': 128, 'Purple': 129, 'DarkOrange3': 130, 'IndianRed': 131, 'HotPink3': 132, 'MediumOrchid3': 133, 'MediumOrchid': 134, 'MediumPurple2': 135, 'DarkGoldenrod': 136, 'LightSalmon3': 137, 'RosyBrown': 138, 'Grey63': 139, 'MediumPurple2': 140, 'MediumPurple1': 141, 'Gold3': 142, 'DarkKhaki': 143, 'NavajoWhite3': 144, 'Grey69': 145, 'LightSteelBlue3': 146, 'LightSteelBlue': 147, 'Yellow3': 148, 'DarkOliveGreen3': 149, 'DarkSeaGreen3': 150, 'DarkSeaGreen2': 151, 'LightCyan3': 152, 'LightSkyBlue1': 153, 'GreenYellow': 154, 'DarkOliveGreen2': 155, 'PaleGreen1': 156, 'DarkSeaGreen2': 157, 'DarkSeaGreen1': 158, 'PaleTurquoise1': 159, 'Red3': 160, 'DeepPink3': 161, 'DeepPink3': 162, 'Magenta3': 163, 'Magenta3': 164, 'Magenta2': 165, 'DarkOrange3': 166, 'IndianRed': 167, 'HotPink3': 168, 'HotPink2': 169, 'Orchid': 170, 'MediumOrchid1': 171, 'Orange3': 172, 'LightSalmon3': 173, 'LightPink3': 174, 'Pink3': 175, 'Plum3': 176, 'Violet': 177, 'Gold3': 178, 'LightGoldenrod3': 179, 'Tan': 180, 'MistyRose3': 181, 'Thistle3': 182, 'Plum2': 183, 'Yellow3': 184, 'Khaki3': 185, 'LightGoldenrod2-1': 186, 'LightYellow3': 187, 'Grey84': 188, 'LightSteelBlue1': 189, 'Yellow2': 190, 'DarkOliveGreen1': 191, 'DarkOliveGreen1': 192, 'DarkSeaGreen1': 193, 'Honeydew2': 194, 'LightCyan1': 195, 'Red1': 196, 'DeepPink2': 197, 'DeepPink1': 198, 'DeepPink1': 199, 'Magenta2': 200, 'Magenta1': 201, 'OrangeRed1': 202, 'IndianRed1': 203, 'IndianRed1': 204, 'HotPink': 205, 'HotPink': 206, 'MediumOrchid1': 207, 'DarkOrange': 208, 'Salmon1': 209, 'LightCoral': 210, 'PaleVioletRed1': 211, 'Orchid2': 212, 'Orchid1': 213, 'Orange1': 214, 'SandyBrown': 215, 'LightSalmon1': 216, 'LightPink1': 217, 'Pink1': 218, 'Plum1': 219, 'Gold1': 220, 'LightGoldenrod2-2': 221, 'LightGoldenrod2-3': 222, 'NavajoWhite1': 223, 'MistyRose1': 224, 'Thistle1': 225, 'Yellow1': 226, 'LightGoldenrod1': 227, 'Khaki1': 228, 'Wheat1': 229, 'Cornsilk1': 230, 'Grey100': 231, 'Grey3': 232, 'Grey7': 233, 'Grey11': 234, 'Grey15': 235, 'Grey19': 236, 'Grey23': 237, 'Grey27': 238, 'Grey30': 239, 'Grey35': 240, 'Grey39': 241, 'Grey42': 242, 'Grey46': 243, 'Grey50': 244, 'Grey54': 245, 'Grey58': 246, 'Grey62': 247, 'Grey66': 248, 'Grey70': 249, 'Grey74': 250, 'Grey78': 251, 'Grey82': 252, 'Grey85': 253, 'Grey89': 254, 'Grey93': 255, }
        # I'm sure there is a better way to do this, but I got tired of looking.
        self.glyphs = { 'blocks':
                            {
                             'block': "█",      # 
                             'block_hu': "▀",   # half up
                             'block_hd': "▄",   # half down
                             'block_hl': "▌",   # half left
                             'block_hr': "▐",   # half right
                             'block_qul': "▘",  # quarter upper left
                             'block_qur': "▝",  # quarter upper right
                             'block_qll;': "▖", # quarter lower left
                             'block_qlr': "▗",  # quarter lower right
                             },
                        'lines':
                           {'light':
                                {'line_h': "─",
                                 'line_hdd': "╌",
                                 'line_hdt': "┄",
                                 'line_hl': "╴",
                                 'line_hr': "╶",
                                 'line_v': "│",
                                 'line_vdd': "╎",
                                 'line_vdt': "┆",
                                 'line_vl': "╷",
                                 'line_vu': "╵",
                                 'corner_ul': "┌",
                                 'corner_ur': "┐",
                                 'corner_ll': "└",
                                 'corner_lr': "┘",
                                },
                            'heavy': 
                                {'line_h': "━",     # horizontal
                                 'line_hdd': "╍",   # horizontal dash double
                                 'line_hdt': "┅",   # horizontal dash triple
                                 'line_hl': "╸",    # horizontal left
                                 'line_hr': "╺",    # horizontal right
                                 'line_v': "┃",     # vertical
                                 'line_vdd': "╏",   # vertical dash double
                                 'line_vdt': "┇",   # vertical dash triple
                                 'line_vu': "╹",    # vertical upper
                                 'line_vl': "╻",    # vertical lower
                                 'corner_ul': "┏",  # corner upper left
                                 'corner_ur': "┓",  # corner upper right
                                 'corner_ll': "┗",  # corner lower left
                                 'corner_lr': "┛",  # corner lower right
                                },
                           'double':
                                {'line_h': "═",
                                 'line_v': "║",
                                 'corner_ul': "╔",
                                 'corner_ur': "╗",
                                 'corner_ll': "╚",
                                 'corner_lr': "╝",
                                },
                            },
                        }


        # Initialize curses stuff
        self.stdscr = curses.initscr()   # Return a window object representing the entire screen
        self.stdscr.keypad(True)         # Accept multibyte special keys (eg., curses.KEY_LEFT)
        self.stdscr.nodelay(True)        # Don't block waiting for input (must then block manually in a while loop)
        curses.cbreak()                  # Accept keypresses without having to hit enter
        curses.noecho()                  # Don't automatically echo keypresses to screen
        curses.curs_set(0)               # Hide the cursor
        curses.start_color()             # Initialize color

        #####################################################################
        ## Begin NAFC-specific stuff
        if isinstance(alternatives, list):
            self.alternatives = alternatives 
        else:
            self.alternatives = []
            for i in range(alternatives):
                self.alternatives.append(str(i+1)) # Text of alternatives
        self.button_colors = []
        self.button_borders = []
        for i in range(len(self.alternatives)):
            self.button_colors.append(0)
            self.button_borders.append(1)

        self.buttons_show = True
        self.prompt_show = True
        self.button_w = 7                   # Button width. odd values allow text to be centered. Height will be 1 less
        self.button_space = 7               # Space between buttons
        self.pad_y = 8                      # offset from top of window (prompt starts here)

        # Set colors
        self.color_default_fg =     self.palette256['Grey']
        self.color_default_bg =     self.palette256['Black']
        self.color_button_fg_1 =    self.palette256['Silver']
        self.color_button_fg_2 =    self.palette256['DarkGreen']
        self.color_button_fg_3 =    self.palette256['Maroon']
        self.color_button_fg_4 =    self.palette256['LightGoldenrod2-2']
        self.color_button_bg =      self.palette256['Black']
        self.color_button_border =  self.palette256['White']
        self.color_button_text =    self.palette256['White']

        self.color_title_fg =       self.palette256['White']
        self.color_title_bg =       self.palette256['Grey']
        self.color_status_fg =      self.palette256['Grey74']
        self.color_status_bg =      self.palette256['Grey23']
        self.color_notify_ul_fg =   self.palette256['White']
        self.color_notify_ul_bg =   self.palette256['DarkGreen']
        self.color_notify_ur_fg =   self.palette256['White']
        self.color_notify_ur_bg =   self.palette256['DarkRed']
        self.color_notify_ll_fg =   self.palette256['White']
        self.color_notify_ll_bg =   self.palette256['DarkGreen']
        self.color_notify_lr_fg =   self.palette256['White']
        self.color_notify_lr_bg =   self.palette256['DarkRed']

        # Create curses fg/bg color pairs
        curses.init_pair(1,  self.color_default_fg,    self.color_default_bg)
        curses.init_pair(2,  self.color_title_fg,      self.color_title_bg)
        curses.init_pair(3,  self.color_status_fg,     self.color_status_bg)
        curses.init_pair(4,  self.color_notify_ul_fg,  self.color_notify_ul_bg)
        curses.init_pair(5,  self.color_notify_ur_fg,  self.color_notify_ur_bg)
        curses.init_pair(6,  self.color_notify_ul_bg,  self.color_default_bg) # Used for padding
        curses.init_pair(7,  self.color_notify_ur_bg,  self.color_default_bg)
        curses.init_pair(8,  self.color_notify_ll_fg,  self.color_notify_ll_bg)
        curses.init_pair(9,  self.color_notify_lr_fg,  self.color_notify_lr_bg)
        curses.init_pair(10, self.color_notify_ll_bg,  self.color_default_bg)
        curses.init_pair(11, self.color_notify_lr_bg,  self.color_default_bg)

        curses.init_pair(12, self.color_button_fg_1,   self.color_button_bg)   # no text
        curses.init_pair(13, self.color_button_text,   self.color_button_fg_1) # Show text
        curses.init_pair(14, self.color_button_fg_1,   self.color_button_fg_1) # Hide text

        curses.init_pair(15, self.color_button_fg_2,   self.color_button_bg)   # no text
        curses.init_pair(16, self.color_button_text,   self.color_button_fg_2) # Show text
        curses.init_pair(17, self.color_button_fg_2,   self.color_button_fg_2) # Hide text

        curses.init_pair(18, self.color_button_fg_3,   self.color_button_bg)   # no text
        curses.init_pair(19, self.color_button_text,   self.color_button_fg_3) # Show text
        curses.init_pair(20, self.color_button_fg_3,   self.color_button_fg_3) # Hide text

        curses.init_pair(21, self.color_button_fg_4,   self.color_button_bg)   # no text
        curses.init_pair(22, self.color_button_text,   self.color_button_fg_4) # Show text
        curses.init_pair(23, self.color_button_fg_4,   self.color_button_fg_4) # Hide text

        curses.init_pair(24, self.color_button_bg,     self.color_button_bg)
        curses.init_pair(25, self.color_button_border, self.color_button_bg)
        curses.init_pair(26, self.color_button_text,   self.color_button_bg)   # Show text

        # A dict, so we can call colors by name
        self.cp = { 'default':       curses.color_pair(1),
                    'title':         curses.color_pair(2),
                    'status':        curses.color_pair(3),
                    'notify_ul':     curses.color_pair(4),
                    'notify_ur':     curses.color_pair(5),
                    'notify_ul_pad': curses.color_pair(6),
                    'notify_ur_pad': curses.color_pair(7),
                    'notify_ll':     curses.color_pair(8),
                    'notify_lr':     curses.color_pair(9),
                    'notify_ll_pad': curses.color_pair(10),
                    'notify_lr_pad': curses.color_pair(11),

                    }

        self.button_b_colors = [
                    curses.color_pair(24), # No border (bg, bg)
                    curses.color_pair(25), # light border (fg, bg)
                    curses.color_pair(25), # Heavy border (fg, bg)
                    curses.color_pair(25), # Heavy border (fg, bg)
                    ]
        self.button_b_weights = [self.glyphs['lines']['light'], 
                                 self.glyphs['lines']['light'], 
                                 self.glyphs['lines']['heavy'],
                                 self.glyphs['lines']['double'],
                                ]

        self.button_f_colors = [
                            [curses.color_pair(24), # No color (bg)  # No text
                             curses.color_pair(26),                  # Show text
                             curses.color_pair(24),                  # Hide text
                            ],
                            [curses.color_pair(12), # First color
                             curses.color_pair(13),
                             curses.color_pair(14),
                            ],
                            [curses.color_pair(15), # Second color
                             curses.color_pair(16),
                             curses.color_pair(17),
                            ],
                            [curses.color_pair(18), # Third color
                             curses.color_pair(19),
                             curses.color_pair(20),
                            ],
                            [curses.color_pair(21), # Fourth color
                             curses.color_pair(22),
                             curses.color_pair(23),
                            ],
                              ]
        self.prompt_color = curses.color_pair(26)
        self.button_color_names = ['None', 'Grey', 'Green', 'Red', 'Yellow'] # Allow user to specify color/border by name
        self.button_border_names = ['None', 'Light', 'Heavy', 'Double']      # Must be in same order as button_f_colors 
                                                                             # button_b_weight and button_b_colors
        self.redraw()


    def destroy(self):
        self.stdscr.nodelay(False)
        self.stdscr.keypad(False)
        curses.curs_set(1)
        curses.echo()
        curses.nocbreak()
        curses.endwin()


    def redraw(self):
        """Draw entire window

            Called when term is resized, or manually by user

        """
        self.win_height,self.win_width = self.stdscr.getmaxyx()
        
        glyph_blocks = self.glyphs['blocks']

        self.stdscr.erase()

        button_space = (self.button_w * 2) + self.button_space

        array_w = (button_space * len(self.alternatives)) - self.button_space # Take one space back for the last one
        array_x1 = int((self.win_width // 2) - (array_w // 2) - array_w % 2)
        array_x2 = array_x1 + array_w
        this_y = self.pad_y

        # Handle prompt
        prompt = self.prompt.strip("\n").split("\n")
        for line in prompt:
            if self.prompt_show:
                this_line = line
            else:
                this_line = " "
            this_x = int((self.win_width // 2) - (len(line) // 2) - len(line) % 2)
            self.stdscr.addstr(this_y, this_x, this_line, curses.A_BOLD | self.prompt_color)
            this_y += 1
        this_y += 1

        # Handle button array
        if self.buttons_show:
            # Draw button face
            for ii in range(len(self.alternatives)):
                this_x = array_x1 + (ii*button_space)
                color = self.button_f_colors[self.button_colors[ii]]
                for y in range (self.button_w-2):
                    self.stdscr.addstr(this_y + y+1,                this_x+2,                     glyph_blocks['block'] * ((self.button_w*2)-2), color[0])
                    self.stdscr.addstr(this_y + y+1,                this_x+1,                     glyph_blocks['block_hr'], color[0]) # Half blocks keep the border
                    self.stdscr.addstr(this_y + y+1,                this_x + (self.button_w*2)-1, glyph_blocks['block_hl'], color[0]) # space equal to that of horizontal
                    self.stdscr.addstr(this_y + (self.button_w//2), this_x + (self.button_w),     self.alternatives[ii],    curses.A_BOLD | color[1])

            # Draw button border
            for ii in range(len(self.alternatives)):
                this_x = array_x1 + (ii*button_space)
                b_color = self.button_b_colors[self.button_borders[ii]]
                b_weight = self.button_b_weights[self.button_borders[ii]]
                self.stdscr.addstr(this_y,                   this_x,                     b_weight['line_h'] * (self.button_w*2), b_color)
                self.stdscr.addstr(this_y + self.button_w-1, this_x,                     b_weight['line_h'] * (self.button_w*2), b_color)
                self.stdscr.addstr(this_y,                   this_x,                     b_weight['corner_ul'],                  b_color)
                self.stdscr.addstr(this_y,                   this_x + (self.button_w*2), b_weight['corner_ur'],                  b_color)
                self.stdscr.addstr(this_y + self.button_w-1, this_x,                     b_weight['corner_ll'],                  b_color)
                self.stdscr.addstr(this_y + self.button_w-1, this_x + (self.button_w*2), b_weight['corner_lr'],                  b_color)
                for y in range (self.button_w-2): # Take an extra for vcenter (can't center both simultanously when both are odd)
                    self.stdscr.addstr(this_y + y+1,         this_x,                     b_weight['line_v'],                     b_color)
                    self.stdscr.addstr(this_y + y+1,         this_x + (self.button_w*2), b_weight['line_v'],                     b_color)

        # Upper Left Notify
        if self.notify_l_show:
            lines = self.notify_l_str.split("\n")
            ii = max(self.notify_offset_v, (self.win_height // 10)) # self.notify_offset_v  # Terminal line to start at
            adj = 0                    # used to adjust if any lines are off the terminal window
            w = 0                      # holds the width of the window
            for line in lines:
                # Check if any lines are off window after centering, adjust if they are
                x = int((array_x1 // 2) - (len(line) // 2) - len(line) % 2)
                adj = min(x, adj)
                w = max(len(line), w)
            if self.notify_pad:
                # Vertical pad with half-down blocks across top of window
                this_line = glyph_blocks['block_hd'] * (w+2)
                x = int((array_x1 // 2) - (len(this_line) // 2) - len(this_line) % 2) - adj
                x = max(x, 1)
                self.stdscr.addstr(ii, x, this_line, self.cp['notify_ul_pad'])
                # we have padded top, so start text 1 line down
                ii += 1
            for line in lines:
                # Pad shorter lines so window is a nice rectangle
                pad = w - len(line)
                this_line = (" " * (pad // 2)) + line + (" " * ((pad // 2) + (pad % 2)))
                if self.notify_pad:
                    # Horizontal pad with a space at beginning and end of each line
                    this_line = " " + this_line + " "
                x = int((array_x1 // 2) - (len(this_line) // 2) - len(this_line) % 2) - adj
                x = max(x, 1)
                self.stdscr.addstr(ii, x, this_line, self.cp['notify_ul'] | curses.A_BOLD)
                ii += 1
            if self.notify_pad:
                # Vertical pad with half-up blocks across bottom of window
                this_line = glyph_blocks['block_hu'] * (w+2)
                x = int((array_x1 // 2) - (len(this_line) // 2) - len(this_line) % 2) - adj
                x = max(x, 1)
                self.stdscr.addstr(ii, x, this_line, self.cp['notify_ul_pad'])

        # Upper Right Notify
        if self.notify_r_show:
            lines = self.notify_r_str.split("\n")
            ii = max(self.notify_offset_v, (self.win_height // 10)) # self.notify_offset_v  # Terminal line to start at
            adj = 0
            w = 0
            for line in lines:
                x = (array_x2+1) + (int(( (self.win_width - array_x2) // 2) - (len(line) // 2) - len(line) % 2) )
                adj = min(self.win_width - (x + len(line)), adj)
                w = max(len(line), w)
            if self.notify_pad:
                this_line = glyph_blocks['block_hd'] * (w+2)
                x = (array_x2+1) + (int(( (self.win_width - array_x2) // 2) - (len(this_line) // 2) - len(this_line) % 2) ) - adj
                x = min(x, self.win_width - len(this_line)-1)
                self.stdscr.addstr(ii, x, this_line, self.cp['notify_ur_pad'])
                ii += 1
            for line in lines:
                pad = w - len(line)
                this_line = (" " * (pad // 2)) + line + (" " * ((pad // 2) + (pad % 2)))
                if self.notify_pad:
                    this_line = " " + this_line + " "
                x = (array_x2 + 1) + (int(( (self.win_width - array_x2) // 2) - (len(this_line) // 2) - len(this_line) % 2) ) - adj
                x = min(x, self.win_width-len(this_line)-1)
                self.stdscr.addstr(ii, x, this_line, self.cp['notify_ur'] | curses.A_BOLD)
                ii += 1
            if self.notify_pad:
                this_line = glyph_blocks['block_hu'] * (w+2)
                x = (array_x2 + 1) + (int(( (self.win_width - array_x2) // 2) - (len(this_line) // 2) - len(this_line) % 2) ) - adj
                x = min(x, self.win_width - len(this_line) - 1)
                self.stdscr.addstr(ii, x, this_line, self.cp['notify_ur_pad'])

        # Lower left and right notifies are not implemented as they seem a bit overkill

        # Border
        self.stdscr.attron(self.cp['default'])
        self.stdscr.box()
        self.stdscr.attroff(self.cp['default'])

        # Title bar
        self.stdscr.addstr(0, 1, " " * (self.win_width-2), self.cp['title'])
        if self.title_l_str:
            self.stdscr.addstr(0, 1, self.title_l_str, curses.A_BOLD | self.cp['title'])
        if self.title_c_str:
            x = int((self.win_width // 2) - (len(self.title_c_str) // 2) - len(self.title_c_str) % 2) -1
            self.stdscr.addstr(0, x, self.title_c_str, curses.A_BOLD | self.cp['title'])
        if self.title_r_str:
            x = self.win_width - len(self.title_r_str) - 1
            self.stdscr.addstr(0, x, self.title_r_str, curses.A_BOLD | self.cp['title'])

        # Status bar
        self.stdscr.addstr(self.win_height-1, 1, " " * (self.win_width-2), self.cp['status'])
        if self.status_l_str:
            self.stdscr.addstr(self.win_height-1, 1, self.status_l_str, self.cp['status'])
        if self.status_c_str:
            x = int((self.win_width // 2) - (len(self.status_c_str) // 2) - len(self.status_c_str) % 2) -1
            self.stdscr.addstr(self.win_height-1, x, self.status_c_str, self.cp['status'])
        if self.status_r_str:
            x = self.win_width - len(self.status_r_str) - 1
            self.stdscr.addstr(self.win_height-1, x, self.status_r_str, self.cp['status'])


        self.stdscr.refresh()


    def rectangle(self, win, uly, ulx, lry, lrx):
        """Draw a rectangle with corners at the provided upper-left
            and lower-right coordinates.

            This is not used ATM, the rect for the posbar is drawn by hand to 
            allow more control over style

            https://stackoverflow.com/questions/52804155/extending-curses-rectangle-box-to-edge-of-terminal-in-python
        """
        win.vline(uly+1, ulx, curses.ACS_VLINE, lry - uly - 1)
        win.hline(uly, ulx+1, curses.ACS_HLINE, lrx - ulx - 1)
        win.hline(lry, ulx+1, curses.ACS_HLINE, lrx - ulx - 1)
        win.vline(uly+1, lrx, curses.ACS_VLINE, lry - uly - 1)
        win.addch(uly, ulx, curses.ACS_ULCORNER)
        win.addch(uly, lrx, curses.ACS_URCORNER)
        win.addch(lry, lrx, curses.ACS_LRCORNER)
        win.addch(lry, ulx, curses.ACS_LLCORNER)


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

        try:
            key = curses.ERR
            waiting = True
            timeout_start = time.time()
            # Debugging:
            #loops = 0
            self.stdscr.timeout(10)
            curses.flushinp()
            while waiting:
                key = self.stdscr.getch()
                if key == curses.ERR: # Default wait response from curses; keep waiting
                    if (timeout is not None) and (time.time() >= timeout_start + timeout):
                        ret = None
                        waiting = False
                    time.sleep(self.keypress_wait) # Avoid cpu race while looping
                elif key == curses.KEY_RESIZE:
                    self.redraw()
                else:
                    # Something else: return key as char and let user evaluate
                    ret = chr(key)
                    waiting = False
                #loops += 1
                #self.update_Title_Left("Interface Loops: {:}".format(loops), redraw=True)
            return ret

        except:
            self.destroy()
            raise Exception("Error getting input")
    
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

        if sys.platform.lower() != 'darwin':
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
        else:
            libsysb = ctypes.CDLL('/usr/lib/libSystem.B.dylib',use_errno=True)
            clock_gettime = libsysb.clock_gettime
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

