import json
from copy import deepcopy
import threading

def generate_event_js():
    """
        Generate JS that handles UI events
    """

    js="""
    function show_elem(id,show) {
        console.log("Showing id: "+ id);
        this.elem = document.getElementById(id);
        elem = this.elem;
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

    function set_button_borders(_id,borders) {
        var buttons = document.getElementsByClassName("button");
        var num_buttons = buttons.length;
        // Borders are 0-None 1- Light 2-Heavy 3-Double
        var border_widths = ['0px','5px','5px','3px'];
        var border_style = ['none','solid','solid','double'];
        var border_color = ['#277650','#277650','black','black'];
        for (var i = 0; i < num_buttons; i++) {
            var choice = borders[i];
            buttons[i].style.border = border_widths[choice] + " " + border_style[choice] + " " + border_color[choice];
        }
    }

    function set_button_colors(_id,colors) {
        var buttons = document.getElementsByClassName("button");
        var num_buttons = buttons.length;
        for (var i = 0; i < num_buttons; i++) {
            if (colors[i] == "Green") {
                colors[i] = "#277650";
            }
            buttons[i].style.backgroundColor = colors[i];
        }
    }"""
    return js

def generate_key_js():
        """
            Generate JS that handles keypresses
        """

        js = """
        // key handler for page
        document.onkeyup = function(event) {
            var button = findButton(event.keyCode);
            flashButton(button);
            send_key(event.keyCode);
        }
        function buttonClick(button) {
            flashButton(button);
            send_key(button.id.charCodeAt(0)); // send ASCII code of id
        }

        function send_key(keyCode) {
            var d = new Date();
            var now = d.getTime(); // time in ms
            var data = {'EventType':'KeyPress','Value':keyCode, 'Timestamp': now};
            server_post("/nafc/keypress.json", JSON.stringify(data), parse_response)
            if (clearTimeout !== null && clearTimeout !== undefined) {
                currentDelay = 0;
                console.log("KEYPRESS RESET");
            }
        }"""
        return js


def generate_client_ajax_js():
    """
        Generate JS related to AJAX communication
    """

    js = """
    var continuePolling = true; // global condition variable
    var currentDelay = 0;

    function get_request() {
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
        return request;
    }

    function server_post(url, data, callback_func) {
        var request = get_request();
        if (!request) {
            return false;
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

    function make_run_func(func,id,val) {
        return function () {
            func(id,val);
            clearTimeout = true;
        }
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
                currentDelay = currentDelay || 0;
                var commands = result['Commands']; // check if this is a command request
                if (commands) {
                    for(var i = 0; i < commands.length; i++) {
                        var entry = commands[i];
                        var cmd = entry[0];
                        var val = entry[1];
                        var id = entry[2];
                        var func_to_run;
                        switch (cmd) {
                            case 0: // show
                                func_to_run = show_elem;
                                break;
                            case 1: // update
                                func_to_run = update_elem;
                                break;
                            case 2: // set border
                                func_to_run = set_button_borders;
                                break;
                            case 3: // set color
                                func_to_run = set_button_colors
                                break;
                            case 4: // wait_ms
                                currentDelay += val;
                                func_to_run = undefined;
                                break;
                            case 5: // quit
                                console.log("RECEIVED A QUIT COMMAND");
                                continuePolling = false;
                                break;
                            default:
                                console.log("Undefined command: " + cmd);
                                continuePolling = false;
                                func_to_run = undefined;
                                break;
                        }

                        if (func_to_run === null || func_to_run === undefined) {
                            continue;
                        } else {
                            if (currentDelay != 0 ) {
                                clearTimeout = false;
                                setTimeout(make_run_func(func_to_run,id,val),currentDelay);
                                if (clearTimeout) {
                                    console.log("CLEARING TIMEOUT");
                                    currentDelay = 0;
                                }
                            } else {
                                func_to_run(id,val);
                            }
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
