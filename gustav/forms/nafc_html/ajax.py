import json
import threading

def process_ajax(interface,data_string):
    """ Parse and then respond to AJAX request

    JSON Events are sent as follows:

    From Browser: { 'EventType': 'KeyPress or Poll',
                    'Value'    : 'KeyCode or Null',
                    'Time'     : 'Timestamp or Null' }

    To Browser:   'result': { 'Commands' : '{
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
                   }
                  }
    """

    response_str = "Error processing client JSON"

    try:
        template = '{ "result" : %s }'
        data = json.loads(data_string)

        if data['EventType'] == 'KeyPress':
            interface.set_key(data['Value'])
            response_str = template % ('"KeyPressReceived"')

        elif data['EventType'] == 'Poll':
            response_str = template % interface.cmd_queue.gen_cmdstr()

    except Exception as e:
        print("Encountered exception while processing AJAX JSON: " + str(e))

    finally:
        return response_str


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

    def length(self):
        return len(self.cmd_list)

    def push_cmd(self,command):
        self.mutex.acquire()
        self.cmd_list.append(command)
        self.mutex.release()

    def pop_cmd(self):
        self.mutex.acquire()
        result = self.cmd_list.pop(0)
        self.mutex.release()

        return result

    def empty(self):
        return len(self.cmd_list) <= 0

    def gen_cmdstr(self):
        cmds_dict = dict()
        cmds_dict['Commands'] = []

        while len(self.cmd_list) > 0:
            entry = self.pop_cmd()
            cmd_dict = dict()
            cmd_dict['Command'] = entry.cmd
            cmd_dict['Value'] = entry.value
            cmd_dict['ID'] = entry.id
            cmds_dict['Commands'].append(cmd_dict)

        return json.dumps(cmds_dict)

    def quit(self):
        return self.push_cmd(Command('quit',0,0))
