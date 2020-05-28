import json
from copy import deepcopy
import threading

def process_ajax(interface,data_string):
    """ Parse and then respond to AJAX request

    JSON Events are sent as follows:

    From Browser: { 'EventType': 'KeyPress or Poll',
                    'Value'    : 'KeyCode or Null',
                    'Time'     : 'Timestamp or Null' }

    To Browser:   'result': { [
                      'Command':
                        0  - show_notify_left
                        1  - show_notify_right
                        2  - update_notify_left
                        3  - update_notify_right
                        4  - update_status_left
                        5  - update_status_right
                        6  - update_status_center
                        7  - update_title_left
                        8  - update_title_right
                        9  - update_title_center
                        10 - show_buttons
                        11 - show_prompt
                        12 - set_border
                        13 - set_color
                        14 - quit',
                     'Value' : 'Hex Color or Text',
                     'IDs' : 'Alternative Name (e.g. A, B, C)
                   ]
                  }
        E.G.: [ [14,0,0] ] = [ quit ]
    """

    response_dict = {}
    response_dict["result"] = "Error"
    err = False

    try:
        data = json.loads(data_string)
        if data["EventType"] == "KeyPress":
            interface.set_key(data["Value"])
            response_dict["result"] = "KeyPressReceived"

        elif data["EventType"] == "Poll":
            response_dict["result"] = interface.cmd_queue.get_all_cmds()

    except Exception as e:
        print("Encountered exception while processing AJAX JSON: " + str(e))
        err = True

    finally:
        return json.dumps(response_dict), err


class Command:
    def __init__(self,c,val,idval):
        self.cmd = c
        self.value = val
        self.id = idval

    def __str__(self):
        return "Command: %s %s %s" % (self.cmd,self.value,self.id)


class CommandQueue:
    def __init__(self):
        self.cmd_list = []
        self.mutex = threading.Lock()

    def __str__(self):
        ret = "Commands: {"
        for cmd in self.cmd_list:
            ret += str(cmd) + ", "

        return ret + "}"

    def gen_cmd(self,cmd,val,idval):
        return [cmd, val, idval ]

    def length(self):
        return len(self.cmd_list)

    def push_cmd(self,command):
        with self.mutex:
            self.cmd_list.append(command)

    def pop_cmd(self):
        with self.mutex:
            result = self.cmd_list.pop(0)

        return result

    def empty(self):
        return len(self.cmd_list) <= 0

    def get_all_cmds(self):

        with self.mutex:
            cmds = deepcopy(self.cmd_list)
            self.cmd_list = []

        return { 'Commands' : cmds }

    def quit(self):
        return self.push_cmd(self.gen_cmd(14,0,0))
