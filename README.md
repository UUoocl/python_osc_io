# python_osc_io
An OBS Python Script to manage multiple OSC clients.

**Documentation**
http://uuoocl.github.io/python_osc_io

## Overview
`python_osc_io` is a powerful OBS (Open Broadcaster Software) script designed to bridge Open Sound Control (OSC) messages with OBS sources. It allows you to:
- **Receive OSC Messages:** Automatically update OBS Text Sources or trigger events in Browser Sources when specific OSC messages are received.
- **Send OSC Messages:** Monitor OBS Text Sources and send OSC messages whenever their content changes.
- **Multi-Client Support:** Manage multiple OSC clients with independent IP addresses, ports, and mappings.

## Usage

### Prerequisites
- OBS Studio with Python support enabled.
- The `python-osc` library installed in your OBS Python environment.

### Setting Up the Script
1.  In OBS, go to **Tools** -> **Scripts**.
2.  Add `osc_io_browserSource.py` (for Browser Source integration) or `osc_io_textSource.py` (for Text Source integration).
3.  Configure the **OSC Server Settings** (IP and Port) to listen for incoming messages.
4.  Set the **Number of Clients** you wish to manage.
5.  For each client, configure:
    - **Client IP & Port:** Destination for outgoing OSC messages.
    - **OSC Address:** The filter address to listen for.
    - **Source Mapping:** Select which Browser or Text source should receive the data.

### Message Format
For sending OSC messages via Text Sources, the source text must be a JSON string:
```json
{
  "address": "/your/osc/address",
  "arguments": [1, "example string", 3.14]
}
```

## Developer Overview

### Architecture
The project follows a "bridge" architecture, where a Python script running inside OBS acts as a server/client, and HTML/JS files act as the front-end visualization or consumer.

-   **Python Backend:** Handles UDP communication using `python-osc`. It interacts with the OBS API (`obspython`) to update sources or trigger `javascript_event` calls on Browser Sources.
-   **HTML/JS Frontend:** Browser sources like `osc_monitor.html` listen for custom events dispatched by the Python script. They use the `BroadcastChannel` API to share data with other browser windows or tabs.

### Key Components
- **`osc_io_browserSource.py`**: The primary OBS script that bridges OSC to Browser Source events.
- **`osc_monitor.html`**: A styled visualization for received OSC data. It also forwards events to a Broadcast Channel.
- **`broadcast_listener.html`**: A utility for monitoring any Broadcast Channel from a standard web browser.

### Broadcast Channel API
To facilitate communication between OBS Browser Sources and external browser windows, we use the `BroadcastChannel` API. This allows you to open a dashboard in a separate browser tab that receives real-time updates from OBS without complex networking.
