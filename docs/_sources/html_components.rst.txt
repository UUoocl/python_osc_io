HTML Components
===============

This project includes several HTML files designed to work as OBS Browser Sources or standalone monitors. They utilize the ``BroadcastChannel`` API to communicate between different browser instances (e.g., between an OBS source and an external browser window).

OSC Monitor
-----------
**File:** ``osc_monitor.html``

**Purpose:**
Listens for custom window events dispatched by the ``osc_io_browserSource.py`` script and displays the received OSC address and arguments. It acts as a bridge, forwarding these events to a ``BroadcastChannel``.

**Usage:**
Add this file as a Browser Source in OBS. Append the ``event`` query parameter to specify the event name to listen for.

Example URL:
``file:///path/to/osc_monitor.html?event=my_osc_event``

**Developer Commentary:**
The script checks for the ``event`` query parameter. It sets up an event listener on the ``window`` object. When an event is received, it:
1. Parses ``event.detail`` (handling both JSON strings and objects).
2. Updates the "Last OSC Message" display.
3. Adds the message to a history queue.
4. Posts the data to a ``BroadcastChannel`` with the same name as the event.

Broadcast Listener
------------------
**File:** ``broadcast_listener.html``

**Purpose:**
A generic listener page that connects to a specified ``BroadcastChannel`` and logs all incoming messages. This is useful for debugging or for displaying data on a separate machine or screen (if the browser context allows).

**Usage:**
Open this file in a web browser. Append the ``channel`` query parameter to specify the channel to listen to.

Example URL:
``file:///path/to/broadcast_listener.html?channel=my_osc_event``

**Developer Commentary:**
Uses the ``BroadcastChannel`` API.
- Reads ``?channel=NAME`` from URL.
- Instantiates ``new BroadcastChannel(NAME)``.
- Logs ``onmessage`` events to a scrolling console-like display.

Keyboard Monitor
----------------
**File:** ``keyboard_monitor.html``

**Purpose:**
Visualizes keyboard input events. While primarily for keyboard data, it serves as the template and precursor for the OSC monitor.

**Usage:**
Add as a Browser Source. It listens for ``keyboard_event`` (typically dispatched by a script or test harness).

**Developer Commentary:**
- Maintains a visual history of key presses.
- Broadcasts received keys to the ``keyboard_event`` channel.
- Uses CSS animations for visual feedback ("flashing" cards).

Keyboard Listener
-----------------
**File:** ``keyboard_listener.html``

**Purpose:**
Demonstrates how external applications or separate browser windows can consume the keyboard events broadcast by the ``keyboard_monitor.html``.

**Usage:**
Open in a separate browser window while ``keyboard_monitor.html`` is active.

**Developer Commentary:**
- Subscribes specifically to the ``keyboard_event`` channel.
- Logs received key data with timestamps.
