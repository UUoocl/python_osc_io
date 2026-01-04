"""
python-osc 

co-created with google ai studio
"""

import obspython as obs
import json
from pythonosc import udp_client
from pythonosc import dispatcher
from pythonosc import osc_server
import threading

# Defaults
DEFAULT_SERVER_IP = "127.0.0.1"
DEFAULT_SERVER_PORT = 12345
DEFAULT_SHOW_CLIENTS_SOURCE = "Client Settings Output"

# Global variables
server_ip = DEFAULT_SERVER_IP
server_port = DEFAULT_SERVER_PORT
show_clients_source = DEFAULT_SHOW_CLIENTS_SOURCE
script_settings = None # a pointer to the obs settings for this script
clients = []  # List to hold client dictionaries
server = None
server_thread = None
server_running = False

source_signal_handlers = {}

def script_defaults(settings):
    obs.obs_data_set_default_string(settings, "server_ip", DEFAULT_SERVER_IP)
    obs.obs_data_set_default_int(settings, "server_port", DEFAULT_SERVER_PORT)
    obs.obs_data_set_default_string(settings, "text_source_settings", DEFAULT_SHOW_CLIENTS_SOURCE)


def script_description():
    return "OSC IO: Text Source (Send) & Browser Source (Receive)"


def script_load(settings):
    global script_settings, clients

    script_settings = settings
    print(f"script load {obs.obs_data_get_json(settings)}")
    
    # Optionally start OSC server on load
    start_osc_server()
    print("osc server started on script load")

    #load client list for OSC functions
    clients = []
    for i in range(obs.obs_data_get_int(settings, "number_of_clients")):
        client_ip = obs.obs_data_get_string(settings, f"client_ip_{i}")
        client_port = obs.obs_data_get_int(settings, f"client_port_{i}")
        
        # Changed: Load browser source instead of text receive source
        browser_source_name = obs.obs_data_get_string(settings, f"browser_source_name_{i}")
        text_source_send_name = obs.obs_data_get_string(settings, f"text_source_send_{i}")
        osc_address = obs.obs_data_get_string(settings, f"osc_address_{i}")
        event_name = obs.obs_data_get_string(settings, f"event_name_{i}")

        if client_ip: #Only create the client data, if there is an IP
            client_data = {
                "client_ip": client_ip,
                "client_port": client_port,
                "browser_source_name": browser_source_name,
                "text_source_send_name": text_source_send_name,
                "osc_address": osc_address,
                "event_name": event_name if event_name else "osc_event"
            }
            clients.append(client_data)    

    # Attach signal handlers to text sources (Keep existing logic)
    for client in clients:
        source_name = client["text_source_send_name"]
        source = obs.obs_get_source_by_name(source_name)
        if source:
            signal_handler = obs.obs_source_get_signal_handler(source)
            obs.signal_handler_connect(signal_handler,"update", source_signal_callback)
            obs.obs_source_release(source)
        else:
            print(f"Source {source_name} not found for signal handler.")


def script_update(settings):
    print(f"script update {obs.obs_data_get_json(settings)}")
    script_load(settings)


def populate_list_property(list_property, allowed_ids):
    sources = obs.obs_enum_sources()
    if sources is not None:
        for source in sources:
            source_type = obs.obs_source_get_type(source)
            if source_type == obs.OBS_SOURCE_TYPE_INPUT:
                unversioned_id = obs.obs_source_get_unversioned_id(source)
                if unversioned_id in allowed_ids:
                    name = obs.obs_source_get_name(source)
                    obs.obs_property_list_add_string(list_property, name, name)
        obs.source_list_release(sources)


def script_properties(): #UI
    global script_settings

    print(f"script properties {obs.obs_data_get_json(script_settings)}")

    props = obs.obs_properties_create()
    
    server_group = obs.obs_properties_create()
    obs.obs_properties_add_group(props, "server_group", "OSC Server Settings", obs.OBS_GROUP_NORMAL, server_group)

    obs.obs_properties_add_text(server_group, "server_ip", "Server IP Address", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_int(server_group, "server_port", "Server Port", 1, 65535, 1)
    obs.obs_properties_add_button(server_group, "start_server", "Start Server", start_server_callback)  # Add Start button
    obs.obs_properties_add_button(server_group, "stop_server", "Stop Server", stop_server_callback)  # Add Stop button

    client_count = obs.obs_properties_add_int(props, "number_of_clients", "Number of Clients", 0, 10, 1)
    #modified call back
    obs.obs_property_set_modified_callback(client_count, client_count_callback)    
    
    setting_source = obs.obs_properties_add_list(
        props, 
        "text_source_settings", 
        "Client Settings Text Source", 
        obs.OBS_COMBO_TYPE_LIST,
        obs.OBS_COMBO_FORMAT_STRING
        )
    
    populate_list_property(setting_source, ["text_gdiplus", "text_ft2_source"])

    for i in range(obs.obs_data_get_int(script_settings, "number_of_clients")):
        add_client_properties(props, i)
        
    
    return props


def client_count_callback(props, prop, settings):  # UI
    p = obs.obs_data_get_int(settings, "number_of_clients")
    print(f"callback {p}")

    for remove in range(10):
        obs.obs_properties_remove_by_name(props,f"client_group_{remove}")

    for i in range(p):
        add_client_properties(props, i)
    
    return True


def add_client_properties(props, index): #UI
    # Create property group
    client_group = obs.obs_properties_create()
    
    #Add group's properties
    obs.obs_properties_add_text(client_group, f"client_ip_{index}", f"Client {index+1} IP Address", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_int(client_group, f"client_port_{index}", f"Client {index+1} Port", 1, 65535, 1)

    # Receive Browser Source Selection (New)
    browser_prop = obs.obs_properties_add_list(
        client_group,
        f"browser_source_name_{index}",
        f"Client {index+1} Browser Source (Receive)",
        obs.OBS_COMBO_TYPE_LIST,
        obs.OBS_COMBO_FORMAT_STRING
    )
    populate_list_property(browser_prop, ["browser_source"])

    # Send Text Source Selection (Existing)
    send_prop = obs.obs_properties_add_list(
        client_group,
        f"text_source_send_{index}",
        f"Client {index + 1} Text Source (Send)",
        obs.OBS_COMBO_TYPE_LIST,
        obs.OBS_COMBO_FORMAT_STRING
    )
    populate_list_property(send_prop, ["text_gdiplus", "text_ft2_source"])
    
    obs.obs_properties_add_text(client_group, f"osc_address_{index}", f"Client {index + 1} OSC Address", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_text(client_group, f"event_name_{index}", f"Client {index + 1} Custom Event Name", obs.OBS_TEXT_DEFAULT)

    #Add property group to Properties list
    client_property_group = obs.obs_properties_add_group(props, f"client_group_{index}", f"Client {index+1}", obs.OBS_GROUP_NORMAL, client_group)
    obs.obs_property_set_visible(client_property_group, True)


def source_signal_callback(calldata):
    """
    Signal callback for text source updates.
    message format
    {"address": "/address/filter/", "arguments": ["Arg0","Argument1"]}
    """
    
    try:
        source = obs.calldata_source(calldata,"source")
        source_name = obs.obs_source_get_name(source)

        # find client that matches updated text source
        target_client = next((client for client in clients if client["text_source_send_name"] == source_name), None)
        
        source_settings = obs.obs_source_get_settings(source)
        text = obs.obs_data_get_string(source_settings, "text")

        data = json.loads(text)
        address = data.get("address")
        arguments = data.get("arguments")

        if address and arguments is not None:
            send_osc_message(target_client, address, arguments)
        else:
            print("Invalid JSON format: Missing 'address' or 'arguments'")

        obs.obs_data_release(source_settings)
        obs.obs_source_release(source_name)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
    except Exception as e:
        pass
        # print(f"Error processing OSC send data: {e}")


def send_osc_message(client, address, arguments):
    """Sends an OSC message to the specified address with the given arguments."""
    try:
      client_ip = client.get("client_ip")
      client_port = client.get("client_port")
      osc_client = udp_client.SimpleUDPClient(client_ip, client_port)
      osc_client.send_message(address, arguments)
    
    except Exception as e:
        print(f"Error sending OSC message: {e}")


def start_server_callback(props, property):
    global server_running, server_thread
    if not server_running:
        start_osc_server()
        server_running = True
        print("OSC Server Started via button.")


def stop_server_callback(props, property):
    global server_running, server, server_thread
    if server_running:
        if server:
            server.shutdown()
        if server_thread:
            server_thread.join()
        server_running = False
        print("OSC Server Stopped via button.")


def update_browser(address, *args):
    """
    Callback function to update the browser source with received OSC.
    """
    
    data = {"address": address, "arguments": args}
    json_string = json.dumps(data)

    # Find target client where the OSC address matches
    target_client = next((client for client in clients if address.startswith(client["osc_address"])), None)
    
    if target_client:
        try:
            source_name = target_client["browser_source_name"]
            event_name = target_client["event_name"]
            
            source = obs.obs_get_source_by_name(source_name)
            if source is not None:
                cd = obs.calldata_create()
                obs.calldata_set_string(cd, "eventName", event_name)
                obs.calldata_set_string(cd, "jsonString", json_string)
                
                # Send event to browser source
                proc_handler = obs.obs_source_get_proc_handler(source)
                obs.proc_handler_call(proc_handler, "javascript_event", cd)
                
                obs.calldata_destroy(cd)
                obs.obs_source_release(source)
                print(f"Sent {event_name} to {source_name}")
            else:
                print(f"Browser source '{source_name}' not found!")
        except Exception as e:
            print(f"Error updating Browser Source: {e}")

    
def start_osc_server():
    global server, server_thread, server_running
    if not server_running:
        try:
            disp = dispatcher.Dispatcher()
            # Changed: Use update_browser handler
            disp.set_default_handler(update_browser, True)
            
            server = osc_server.ThreadingOSCUDPServer((server_ip, server_port), disp)
            print(f"Serving on {server.server_address}")
            server_thread = threading.Thread(target=server.serve_forever, daemon=True)
            server_thread.start()
            server_running = True
        except Exception as e:
            print(f"server could not start: {e}")
            server_running = True


def script_unload():
    global script_settings, server, server_thread, clients

    print(f"script unload {obs.obs_data_get_json(script_settings)}")

    #Remove Signal handlers
    for client in clients:
        try:
            source_name = client["text_source_send_name"]
            source = obs.obs_get_source_by_name(source_name)
            if source:
                handler = obs.obs_source_get_signal_handler(source)
                obs.signal_handler_disconnect(handler, "update", source_signal_callback)
                obs.obs_source_release(source)
        except Exception as e:
            pass # print("no source signal to remove")

    if server:
        server.shutdown()
        print("Stopping OSC server...")
    if server_thread:
        server_thread.join()
        print("OSC server stopped.")
    global server_running
    server_running = False
