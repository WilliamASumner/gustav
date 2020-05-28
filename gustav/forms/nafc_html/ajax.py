import json
from copy import deepcopy
import threading

def generate_client_ajax_js():
    js = """
    var continuePolling = true; // global condition variable

    function server_post(url, data, callback_func) {
        var request = false;
        try {
            // Firefox, Opera 8.0+, Safari
            request = new XMLHttpRequest();
        }
        catch (e) {
            // Internet Explorer
            try {
                request = new ActiveXObject("Msxml2.XMLHTTP");
            }
            catch (e) {
                try {
                    request = new ActiveXObject("Microsoft.XMLHTTP");
                }
                catch (e) {
                    alert("Your browser does not support AJAX!");
                    return false;
                }
            }
        }
        request.open("POST", url, true);
        request.onreadystatechange = function() {
            if (request.readyState == 4) {
                callback_func(request);
            }
        }
        request.overrideMimeType("application/json");
        request.send(data);
    }

    function parse_response(request) {
        if (request !== false) {
            var result = null;
            try {
                var data = JSON.parse(request.responseText);
                console.log(data);
                result = data['result'];
                console.log("result:");
                console.log(result);
            } catch (e) {
                console.log(e);
                console.log("No server connection");
                return;
            }

            /* Main Event Processing */
            if (result) {
                var commands = result['Commands']; // check if this is a command request
                if (commands) {
                    for(var i = 0; i < commands.length; i++) {
                        var entry = commands[i];
                        var cmd = entry[0];
                        var val = entry[1];
                        var id = entry[2];
                        console.log("Cmd: ");
                        console.log(cmd);
                        console.log("val: ");
                        console.log(val);
                        console.log("id: ");
                        console.log(id);

                        switch (cmd) {
                            case 14: // quit
                                console.log("RECEIVED A QUIT COMMAND");
                                continuePolling = false;
                                break;
                            default:
                                console.log("Undefined command: " + cmd);
                                break;
                        }
                    }
                }
            }

        } else {
            console.log("Bad request");
        }
    }

    // Poll loop
    // TODO maybe replace this with long polling... this creates a lot of requests
    function poll_timeout() {
        var d = new Date();
        var now = d.getTime(); // time in ms
        var data = {'EventType':'Poll','Value': 0, 'Timestamp': now};
        server_post("/nafc/poll.json", JSON.stringify(data), parse_response)
        if (continuePolling) {
            setTimeout(poll_timeout, 5000);
        }
    }

    setTimeout(poll_timeout,5000);
    """

    return js


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
