With a serial-connected node, run this script to covert all the nodes stored in your nodedb into mqtt.yaml compatible entities.


Usage: python entity-builder.py [-h] [--port PORT | --host HOST | --ble BLE] [--gateway GATEWAY] [--root-topic ROOT_TOPIC] [--no-messages] [--no-temperature] [--no-humidity] [--no-pressure] [--gas-resistance] [--power-ch1] [--power-ch2] [--power-ch3] [--nodes [NODES ...]]

Options:
  --nodes [NODES ...]   Only generate sensors for these nodes. If not provided, all nodes in the NodeDB will be included. Example: `"!XXXXXXXX", "!YYYYYYYY"`.

Help:
  -h, --help            Show this help message and exit.

Connection:
  Optional arguments to specify a device to connect to and how.

  --port PORT           The port to connect to via serial, e.g. `/dev/ttyUSB0`.
  --host HOST           The hostname or IP address to connect to using TCP.
  --ble BLE             The BLE device MAC address or name to connect to.

MQTT:
  Arguments to specify the gateway node and root MQTT topics

  --gateway GATEWAY     The ID of the MQTT gateway node, e.g. !12345678. If not provided, will use the ID of the locally connected node.
  --root-topic ROOT_TOPIC
                        The root topic to use in MQTT for the generated files. If not provided, will attempt to get the root path from the local node and use LongFast as the channel. Wildcard: `+`. Example: to include all channels with the root topic `msh/`, use `msh/2/json/+`.

Includes:
  Arguments to specify what sensors to generate for each node.

  --no-messages         Don't include a sensor for messages from the node.
  --no-temperature      Don't include a temperature sensor.
  --no-humidity         Don't include a humidity sensor.
  --no-pressure         Don't include a pressure sensor.
  --gas-resistance      Include a gas resistance sensor.
  --power-ch1           Include a power & voltage channel 1 sensor.
  --power-ch2           Include a power & voltage channel 2 sensor.
  --power-ch3           Include a power & voltage channel 3 sensor.

If no connection arguments are specified, we attempt a serial connection and then a TCP connection to localhost.
