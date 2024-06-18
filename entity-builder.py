from meshtastic.serial_interface import SerialInterface
from meshtastic.tcp_interface import TCPInterface
from meshtastic.ble_interface import BLEInterface
import argparse
import sys

### Add arguments to parse

parser = argparse.ArgumentParser(
        add_help=False,
        epilog="If no connection arguments are specified, we attempt a serial connection and then a TCP connection to localhost.")

helpGroup = parser.add_argument_group("Help")
helpGroup.add_argument("-h", "--help", action="help", help="Show this help message and exit.")

connOuter = parser.add_argument_group('Connection', 'Optional arguments to specify a device to connect to and how.')
conn = connOuter.add_mutually_exclusive_group()
conn.add_argument(
    "--port",
    help="The port to connect to via serial, e.g. `/dev/ttyUSB0`.",
    default=None,
)
conn.add_argument(
    "--host",
    help="The hostname or IP address to connect to using TCP.", 
    default=None,
)
conn.add_argument(
    "--ble",
    help="The BLE device MAC address or name to connect to.",
    default=None,
)

mqtt = parser.add_argument_group("MQTT", "Arguments to specify the gateway node and root MQTT topics")
mqtt.add_argument(
    "--gateway",
    help="The ID of the MQTT gateway node, e.g. !12345678. If not provided, will use the ID of the locally connected node.",
    default=None,
)
# it would be nice to have this request settings if the gateway isn't the remote node
mqtt.add_argument(
    "--root-topic",
    help="The root topic to use in MQTT for the generated files. If not provided, will attempt to get the root path from the local node and use `LongFast` as the channel. Wildcard: `+`. Example: to include all channels with the root topic `msh/`, use `msh/2/json/+`.",
    default=None,
)

includes = parser.add_argument_group("Includes", "Arguments to specify what sensors to generate for each node.")
includes.add_argument(
    "--no-messages",
    help="Don't include a sensor for messages from the node.",
    action='store_true',
)
includes.add_argument(
    "--no-temperature",
    help="Don't include a temperature sensor.",
    action='store_true',
)
includes.add_argument(
    "--no-humidity",
    help="Don't include a humidity sensor.",
    action='store_true',
)
includes.add_argument(
    "--no-pressure",
    help="Don't include a pressure sensor.",
    action='store_true',
)

includes.add_argument(
    "--gas-resistance",
    help="Include a gas resistance sensor.",
    action='store_true',
)
includes.add_argument(
    "--power-ch1",
    help="Include a power & voltage channel 1 sensor.",
    action='store_true',
)
includes.add_argument(
    "--power-ch2",
    help="Include a power & voltage channel 2 sensor.",
    action='store_true',
)
includes.add_argument(
    "--power-ch3",
    help="Include a power & voltage channel 3 sensor.",
    action='store_true',
)

parser.add_argument(
    "--nodes",
    help="Only generate sensors for these nodes. If not provided, all nodes in the NodeDB will be included. Example: `\"!XXXXXXXX\", \"!YYYYYYYY\"`.",
    nargs='*',
    action='store',
)

args = parser.parse_args()

### Create an interface
if args.ble:
    iface = BLEInterface(args.ble)
elif args.host:
    iface = TCPInterface(args.host)
else:
    try:
        iface = SerialInterface(args.port)
    except PermissionError as ex:
        print("You probably need to add yourself to the `dialout` group to use a serial connection.")
    if iface.devPath is None:
        iface = TCPInterface("localhost")

if args.gateway:
    gateway_id = args.gateway
else:
    gateway_id = f"!{iface.localNode.nodeNum:08x}"


if args.root_topic:
    root_topic = args.root_topic
else:
    mqttRoot = iface.localNode.moduleConfig.mqtt.root
    if mqttRoot != "":
        root_topic = mqttRoot + '/2/json/LongFast'

print(f"Using a gateway ID of {gateway_id} and a root topic of {root_topic}")

node_list = []
use_node_list = False # only use nodes from the node list.  If False, create for all nodes in db.
if args.nodes and len(args.nodes) > 0:
    use_node_list = True
    node_list = args.nodes
    print(f"Using node list: {node_list}")


include_messages = not args.no_messages
include_temperature = not args.no_temperature
include_humidity = not args.no_humidity
include_pressure = not args.no_pressure
include_gas_resistance = args.gas_resistance
include_power_ch1 = args.power_ch1
include_power_ch2 = args.power_ch2
include_power_ch3 = args.power_ch3

# initialize the file with the 'sensor' header
with open("mqtt.yaml", "w", encoding="utf-8") as file:
    file.write('sensor:\n')  
# initialize the file as empty so we have something to append to
with open("automations.yaml", "w", encoding="utf-8") as file:
    file.write('')

for node_num, node in iface.nodes.items():
    node_short_name = f"{node['user']['shortName']}"
    node_long_name = f"{node['user']['longName']}"
    node_id = f"{node['user']['id']}"
    node_num = f"{node['num']}"
    hardware_model = f"{node['user']['hwModel']}"

    automation_config = f"""
- id: 'update_location_{node_num}'
  alias: update {node_id} location
  trigger:
  - platform: mqtt
    topic: "{root_topic}/{gateway_id}"
    payload: 'on'
    value_template: >-
        {{%- if value_json.from == {node_num} and
               value_json.payload.latitude_i is defined and
               value_json.payload.longitude_i is defined -%}}
            on
        {{%- endif -%}}
  condition: []
  action:
  - service: device_tracker.see
    metadata: {{}}
    data:
      dev_id: "{int(node_num):08x}"
      gps:
      - '{{{{ (trigger.payload | from_json).payload.latitude_i | int * 1e-7 }}}}'
      - '{{{{ (trigger.payload | from_json).payload.longitude_i | int * 1e-7 }}}}'
  mode: single
    """

    config = f'''
  - name: "{node_short_name} Last Heard"
    unique_id: "{int(node_num):08x}_last_heard"
    state_topic: "{root_topic}/{gateway_id}"
    state_class: measurement
    device_class: timestamp
    value_template: >-
      {{% if value_json.from == {node_num} and
            value_json.timestamp is defined %}}
        {{{{ as_datetime(value_json.timestamp) }}}}
      {{% else %}}
        {{{{ this.state }}}}
      {{% endif %}}
    device:
      name: "Meshtastic {node_id}"
      identifiers:
        - "meshtastic_{node_num}"


  - name: "{node_short_name} Hops Away"
    unique_id: "{int(node_num):08x}_hops_away"
    state_topic: "{root_topic}/{gateway_id}"
    state_class: measurement
    device_class: distance
    value_template: >-
      {{% if value_json.from == {node_num} and value_json.hops_away is defined %}}
          {{{{ value_json.hops_away | int }}}}
      {{% else %}}
          {{{{ this.state }}}}
      {{% endif %}}
    icon: "mdi:rabbit"
    device:
      identifiers: "meshtastic_{node_num}"
        
  - name: "{node_short_name} Battery Voltage"
    unique_id: "{int(node_num):08x}_battery_voltage"
    state_topic: "{root_topic}/{gateway_id}"
    state_class: measurement
    value_template: >-
      {{% if value_json.from == {node_num} and
          value_json.payload.voltage is defined and
          value_json.payload.temperature is not defined %}}
      {{{{ (value_json.payload.voltage | float) | round(2) }}}}
      {{% else %}}
        {{{{ states('sensor.{node_short_name.lower().replace(" ", "_")}_battery_voltage') }}}}
      {{% endif %}}
    unit_of_measurement: "V"
    icon: "mdi:lightning-bolt"
    device:
      identifiers: "meshtastic_{node_num}"

  - name: "{node_short_name} Battery Percent"
    unique_id: "{int(node_num):08x}_battery_percent"
    state_topic: "{root_topic}/{gateway_id}"
    state_class: measurement
    value_template: >-
      {{% if value_json.from == {node_num} and value_json.payload.battery_level is defined %}}
          {{{{ (value_json.payload.battery_level | float) | round(2) }}}}
      {{% else %}}
          {{{{ states('sensor.{node_short_name.lower().replace(" ", "_")}_battery_percent') }}}}
      {{% endif %}}
    device_class: battery
    unit_of_measurement: "%"
    icon: "mdi:battery-high"
    device:
      identifiers: "meshtastic_{node_num}"

  - name: "{node_short_name} Uptime"
    unique_id: "{int(node_num):08x}_uptime"
    state_topic: "{root_topic}/{gateway_id}"
    state_class: measurement
    device_class: duration
    value_template: >-
      {{% if value_json.from == {node_num} and value_json.payload.uptime_seconds is defined %}}
          {{{{ value_json.payload.uptime_seconds | int }}}}
      {{% else %}}
          {{{{ this.state }}}}
      {{% endif %}}
    unit_of_measurement: "s"
    device:
      identifiers: "meshtastic_{node_num}"

  - name: "{node_short_name} ChUtil"
    unique_id: "{int(node_num):08x}_chutil"
    state_topic: "{root_topic}/{gateway_id}"
    state_class: measurement
    value_template: >-
      {{% if value_json.from == {node_num} and value_json.payload.channel_utilization is defined %}}
          {{{{ (value_json.payload.channel_utilization | float) | round(2) }}}}
      {{% else %}}
          {{{{ states('sensor.{node_short_name.lower().replace(" ", "_")}_chutil') }}}}
      {{% endif %}}
    unit_of_measurement: "%"
    icon: "mdi:signal-distance-variant"
    device:
      identifiers: "meshtastic_{node_num}"

  - name: "{node_short_name} AirUtilTX"
    unique_id: "{int(node_num):08x}_airutiltx"
    state_topic: "{root_topic}/{gateway_id}"
    state_class: measurement
    value_template: >-
      {{% if value_json.from == {node_num} and value_json.payload.air_util_tx is defined %}}
          {{{{ (value_json.payload.air_util_tx | float) | round(2) }}}}
      {{% else %}}
          {{{{ states('sensor.{node_short_name.lower().replace(" ", "_")}_airutiltx') }}}}
      {{% endif %}}
    unit_of_measurement: "%"
    icon: "mdi:percent-box-outline"
    device:
      identifiers: "meshtastic_{node_num}"
    '''

    if include_messages:
      config += f'''
  - name: "{node_short_name} Messages"
    unique_id: "{int(node_num):08x}_messages"
    state_topic: "{root_topic}/{gateway_id}"
    value_template: >-
      {{% if value_json.from == {node_num} and value_json.payload.text is defined %}}
          {{{{ value_json.payload.text }}}}
      {{% else %}}
          {{{{ states('sensor.{node_short_name.lower().replace(" ", "_")}_messages') }}}}
      {{% endif %}}
    device:
      identifiers: "meshtastic_{node_num}"
    icon: "mdi:chat"
        '''
      
    if include_temperature:
      config += f'''
  - name: "{node_short_name} Temperature"
    unique_id: "{int(node_num):08x}_temperature"
    state_topic: "{root_topic}/{gateway_id}"
    state_class: measurement
    value_template: >-
      {{% if value_json.from == {node_num} and value_json.payload.temperature is defined %}}
          {{{{ (((value_json.payload.temperature | float) * 1.8) +32) | round(2) }}}}
      {{% else %}}
          {{{{ states('sensor.{node_short_name.lower().replace(" ", "_")}_temperature') }}}}
      {{% endif %}}
    unit_of_measurement: "F"
    icon: "mdi:sun-thermometer"
    device:
      identifiers: "meshtastic_{node_num}"
    '''
      
    if include_humidity:
      config += f'''
  - name: "{node_short_name} Humidity"
    unique_id: "{int(node_num):08x}_humidity"
    state_topic: "{root_topic}/{gateway_id}"
    state_class: measurement
    value_template: >-
      {{% if value_json.from == {node_num} and value_json.payload.relative_humidity is defined %}}
          {{{{ (value_json.payload.relative_humidity | float) | round(2) }}}}
      {{% else %}}
          {{{{ states('sensor.{node_short_name.lower().replace(" ", "_")}_humidity') }}}}
      {{% endif %}}
    unit_of_measurement: "%"
    icon: "mdi:water-percent"
    device:
      identifiers: "meshtastic_{node_num}"
    '''
      
    if include_pressure:
      config += f'''
  - name: "{node_short_name} Pressure"
    unique_id: "{int(node_num):08x}_pressure"
    state_topic: "{root_topic}/{gateway_id}"
    state_class: measurement
    value_template: >-
      {{% if value_json.from == {node_num} and value_json.payload.barometric_pressure is defined %}}
          {{{{ (value_json.payload.barometric_pressure | float) | round(2) }}}}
      {{% else %}}
          {{{{ states('sensor.{node_short_name.lower().replace(" ", "_")}_pressure') }}}}
      {{% endif %}}
    unit_of_measurement: "hPa"
    icon: "mdi:chevron-double-down"
    device:
      identifiers: "meshtastic_{node_num}"
          '''
      
    if include_gas_resistance:
      config += f'''
  - name: "{node_short_name} Gas Resistance"
    unique_id: "{int(node_num):08x}_gas_resistance"
    state_topic: "{root_topic}/{gateway_id}"
    state_class: measurement
    value_template: >-
      {{% if value_json.from == {node_num} and value_json.payload.gas_resistance is defined %}}
          {{{{ (value_json.payload.gas_resistance | float) | round(2) }}}}
      {{% else %}}
          {{{{ states('sensor.{node_short_name.lower().replace(" ", "_")}_gas_resistance') }}}}
      {{% endif %}}
    unit_of_measurement: "MOhms"
    icon: "mdi:dots-hexagon"
    device:
      identifiers: "meshtastic_{node_num}"
          '''
    
    if include_power_ch1:
      config += f'''
  # {node_long_name}
  - name: "{node_short_name} Battery Voltage Ch1"
    unique_id: "{int(node_num):08x}_battery_voltage_ch1"
    state_topic: "{root_topic}/{gateway_id}"
    state_class: measurement
    value_template: >-
      {{% if value_json.from == {node_num} and value_json.payload.voltage_ch1 is defined %}}
      {{{{ (value_json.payload.voltage_ch1 | float) | round(2) }}}}
      {{% else %}}
        {{{{ states('sensor.{node_short_name.lower().replace(" ", "_")}_battery_voltage_ch1') }}}}
      {{% endif %}}
    unit_of_measurement: "V"
    icon: "mdi:lightning-bolt"
    device:
      identifiers: "meshtastic_{node_num}"

  - name: "{node_short_name} Battery Current Ch1"
    unique_id: "{int(node_num):08x}_battery_current_ch1"
    state_topic: "{root_topic}/{gateway_id}"
    state_class: measurement
    value_template: >-
      {{% if value_json.from == {node_num} and value_json.payload.current_ch1 is defined %}}
      {{{{ (value_json.payload.current_ch1 | float) | round(2) }}}}
      {{% else %}}
        {{{{ states('sensor.{node_short_name.lower().replace(" ", "_")}_battery_current_ch1') }}}}
      {{% endif %}}
    unit_of_measurement: "A"
    icon: "mdi:waves"
    device:
      identifiers: "meshtastic_{node_num}"
        '''
    
    if include_power_ch2:
      config += f'''
  - name: "{node_short_name} Battery Voltage Ch2"
    unique_id: "{int(node_num):08x}_battery_voltage_ch2"
    state_topic: "{root_topic}/{gateway_id}"
    state_class: measurement
    value_template: >-
      {{% if value_json.from == {node_num} and value_json.payload.voltage_ch2 is defined %}}
      {{{{ (value_json.payload.voltage_ch2 | float) | round(2) }}}}
      {{% else %}}
        {{{{ states('sensor.{node_short_name.lower().replace(" ", "_")}_battery_voltage_ch2') }}}}
      {{% endif %}}
    unit_of_measurement: "V"
    icon: "mdi:lightning-bolt"
    device:
      identifiers: "meshtastic_{node_num}"

  - name: "{node_short_name} Battery Current Ch2"
    unique_id: "{int(node_num):08x}_battery_current_ch2"
    state_topic: "{root_topic}/{gateway_id}"
    state_class: measurement
    value_template: >-
      {{% if value_json.from == {node_num} and value_json.payload.current_ch2 is defined %}}
      {{{{ (value_json.payload.current_ch2 | float) | round(2) }}}}
      {{% else %}}
        {{{{ states('sensor.{node_short_name.lower().replace(" ", "_")}_battery_current_ch2') }}}}
      {{% endif %}}
    unit_of_measurement: "A"
    icon: "mdi:waves"
    device:
      identifiers: "meshtastic_{node_num}"
    '''
      
    if include_power_ch3:
      config += f'''
  - name: "{node_short_name} Battery Voltage Ch3"
    unique_id: "{int(node_num):08x}_battery_voltage_ch3"
    state_topic: "{root_topic}/{gateway_id}"
    state_class: measurement
    value_template: >-
      {{% if value_json.from == {node_num} and value_json.payload.voltage_ch3 is defined %}}
      {{{{ (value_json.payload.voltage_ch3 | float) | round(2) }}}}
      {{% else %}}
        {{{{ states('sensor.{node_short_name.lower().replace(" ", "_")}_battery_voltage_ch3') }}}}
      {{% endif %}}
    unit_of_measurement: "V"
    icon: "mdi:lightning-bolt"
    device:
      identifiers: "meshtastic_{node_num}"

  - name: "{node_short_name} Battery Current Ch3"
    unique_id: "{int(node_num):08x}_battery_current_ch3"
    state_topic: "{root_topic}/{gateway_id}"
    state_class: measurement
    value_template: >-
      {{% if value_json.from == {node_num} and value_json.payload.current_ch3 is defined %}}
      {{{{ (value_json.payload.current_ch3 | float) | round(2) }}}}
      {{% else %}}
        {{{{ states('sensor.{node_short_name.lower().replace(" ", "_")}_battery_current_ch3') }}}}
      {{% endif %}}
    unit_of_measurement: "A"
    icon: "mdi:waves"
    device:
      identifiers: "meshtastic_{node_num}"
    '''


    if node_id in node_list or (not use_node_list):
        with open("mqtt.yaml", "a", encoding="utf-8") as file:
            file.write(config + '\n')
        with open("automations.yaml", "a", encoding="utf-8") as file:
            file.write(automation_config)

iface.close()
