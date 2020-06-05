import json
from copy import deepcopy
import threading

def generate_event_js():
    js="""
    function show_elem(id,show) {
        show_elem.elem = document.getElementById(id);
        elem = show_elem.elem;
        if (show) {
                elem.style.opacity = 1.0;
        } else {
                elem.style.opacity = 0.0;
        }
    }
    
    function update_elem(id,str) {
        update_elem.elem = document.getElementById(id);
        elem = update_elem.elem;
        elem.innerHTML = str;
    }

    // generally bad practice, but here we want to preserve 
    // the interface to the python scripts, so we need a synchronous wait
    // the alternative is using setTimeout with more complex cmd parsing
    // that waits for the next cmd and wraps it in a setTimeout
    function wait_ms(delay) {
        var startTime = new Date().getTime();
        var now = startTime;
        while (now - startTime < delay) {
            now = new Date().getTime();
        }
    }
    
    function set_button_borders(borders) {
        var buttons = document.getElementsByClassName("button");
        var num_buttons = buttons.length;
        // Borders are 0-None 1- Light 2-Heavy 3-Double
        var border_widths = ['0px','3px','3px','1px'];
        var border_style = ['none','solid','solid','double'];
        var border_color = ['black','#277650','#227145','#277650'];
        for (var i = 0; i < num_buttons; i++) {
            buttons[i].style.border = border_widths[borders[i]] + " " +border_style[i] + " " + border_color[i];
        }
    }

    function set_button_colors(colors) {
        var buttons = document.getElementsByClassName("button");
        var num_buttons = buttons.length;
        for (var i = 0; i < num_buttons; i++) {
            buttons[i].style.backgroundColor = colors[i];
        }
    } """
    return js

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
                if (request.responseText.length == 0) { // no response
                    continuePolling = false;
                    return;
                }
                var data = JSON.parse(request.responseText);
                result = data['result'];
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
                        switch (cmd) {
                            case 0: // show
                                console.log(commands);
                                console.log("Showing " + id + " with " + val);
                                show_elem(id,val);
                                break;
                            case 1: // update
                                update_elem(id,val);
                                break;
                            case 2: // set border
                                console.log("SETTING BORDER: " + val);
                                set_button_borders(val);
                                break;
                            case 3: // set color
                                set_button_colors(val);
                                break;
                            case 4: // wait_ms
                                wait_ms(val);
                                break;
                            case 5: // quit
                                console.log("RECEIVED A QUIT COMMAND");
                                continuePolling = false;
                                break;
                            default:
                                console.log("Undefined command: " + cmd);
                                continuePolling = false;
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
            setTimeout(poll_timeout, 50);
        }
    }

    setTimeout(poll_timeout,10);
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
                        0  - show_elem
                        1  - update_elem
                        2 - set_border
                        3 - set_color
                        4 - wait_ms
                        5 - quit',
                     'Value' : 'Boolean or Hex Color or Text',
                     'IDs' : 'Alternative Name (e.g. A, B, C)
                   ]
                  }
        E.G.: [ [4,0,0] ] = [ quit ]
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

    def show_elem(self,show,elid):
        return self.push_cmd(self.gen_cmd(0,show,elid))

    def update_elem(self,s,elid):
        return self.push_cmd(self.gen_cmd(1,s,elid))

    def set_border(self,borders):
        return self.push_cmd(self.gen_cmd(2,borders,"buttons"))

    def set_color(self,colors):
        return self.push_cmd(self.gen_cmd(3,colors,"buttons"))

    def wait_ms(self,t):
        return self.push_cmd(self.gen_cmd(4,t,"None"))

    def quit(self):
        return self.push_cmd(self.gen_cmd(5,0,0))
