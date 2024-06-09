import meshtastic.serial_interface

iface = meshtastic.serial_interface.SerialInterface()

gateway_id = "!6d00f4ac"
root_topic = "msh/2/json/LongFast"

# initialize the file with the 'sensor' header
with open("mqtt.yaml", "w") as file:
    file.write('sensor:\n')  

for node_id, node in iface.nodes.items():
    print (node)
    node_short_name = f"{node['user']['shortName']}"
    node_long_name = f"{node['user']['longName']}"
    node_id = f"{node['user']['id']}"
    # mac_address = f"{node['user']['macaddr']}"
    hardware_model = f"{node['user']['hwModel']}"

    config = f'''
  # {node_long_name}
  - name: "{node_short_name} Battery Voltage"
    unique_id: "{node_short_name.lower().replace(" ", "_")}_battery_voltage"
    state_topic: "{root_topic}/{gateway_id}"
    state_class: measurement
    value_template: >-
      {{% if value_json.from == {node_id} and
          value_json.payload.voltage is defined and
          value_json.payload.temperature is not defined %}}
      {{{{ (value_json.payload.voltage | float) | round(2) }}}}
      {{% else %}}
        {{{{ states('sensor.{node_short_name.lower().replace(" ", "_")}_battery_voltage') }}}}
      {{% endif %}}
    unit_of_measurement: "V"
    icon: "mdi:lightning-bolt"
    device:
      identifiers: "meshtastic_{node_id}"

  - name: "{node_short_name} Battery Percent"
    unique_id: "{node_short_name.lower().replace(" ", "_")}_battery_percent"
    state_topic: "{root_topic}/{gateway_id}"
    state_class: measurement
    value_template: >-
      {{% if value_json.from == {node_id} and value_json.payload.battery_level is defined %}}
          {{{{ (value_json.payload.battery_level | float) | round(2) }}}}
      {{% else %}}
          {{{{ states('sensor.{node_short_name.lower().replace(" ", "_")}_battery_percent') }}}}
      {{% endif %}}
    unit_of_measurement: "%"
    icon: "mdi:battery-high"
    device:
      identifiers: "meshtastic_{node_id}"

  - name: "{node_short_name} ChUtil"
    unique_id: "{node_short_name.lower().replace(" ", "_")}_chutil"
    state_topic: "{root_topic}/{gateway_id}"
    state_class: measurement
    value_template: >-
      {{% if value_json.from == {node_id} and value_json.payload.channel_utilization is defined %}}
          {{{{ (value_json.payload.channel_utilization | float) | round(2) }}}}
      {{% else %}}
          {{{{ states('sensor.{node_short_name.lower().replace(" ", "_")}_chutil') }}}}
      {{% endif %}}
    unit_of_measurement: "%"
    icon: "mdi:signal-distance-variant"
    device:
      identifiers: "meshtastic_{node_id}"

  - name: "{node_short_name} AirUtilTX"
    unique_id: "{node_short_name.lower().replace(" ", "_")}_airutiltx"
    state_topic: "{root_topic}/{gateway_id}"
    state_class: measurement
    value_template: >-
      {{% if value_json.from == {node_id} and value_json.payload.air_util_tx is defined %}}
          {{{{ (value_json.payload.air_util_tx | float) | round(2) }}}}
      {{% else %}}
          {{{{ states('sensor.{node_short_name.lower().replace(" ", "_")}_airutiltx') }}}}
      {{% endif %}}
    unit_of_measurement: "%"
    icon: "mdi:percent-box-outline"
    device:
      identifiers: "meshtastic_{node_id}"

  - name: "{node_short_name} Temperature"
    unique_id: "{node_short_name.lower().replace(" ", "_")}_temperature"
    state_topic: "{root_topic}/{gateway_id}"
    state_class: measurement
    value_template: >-
      {{% if value_json.from == {node_id} and value_json.payload.temperature is defined %}}
          {{{{ (((value_json.payload.temperature | float) * 1.8) +32) | round(2) }}}}
      {{% else %}}
          {{{{ states('sensor.{node_short_name.lower().replace(" ", "_")}_temperature') }}}}
      {{% endif %}}
    unit_of_measurement: "F"
    icon: "mdi:sun-thermometer"
    device:
      identifiers: "meshtastic_{node_id}"

  - name: "{node_short_name} Humidity"
    unique_id: "{node_short_name.lower().replace(" ", "_")}_humidity"
    state_topic: "{root_topic}/{gateway_id}"
    state_class: measurement
    value_template: >-
      {{% if value_json.from == {node_id} and value_json.payload.relative_humidity is defined %}}
          {{{{ (value_json.payload.relative_humidity | float) | round(2) }}}}
      {{% else %}}
          {{{{ states('sensor.{node_short_name.lower().replace(" ", "_")}_humidity') }}}}
      {{% endif %}}
    unit_of_measurement: "%"
    icon: "mdi:water-percent"
    device:
      identifiers: "meshtastic_{node_id}"

  - name: "{node_short_name} Pressure"
    unique_id: "{node_short_name.lower().replace(" ", "_")}_pressure"
    state_topic: "{root_topic}/{gateway_id}"
    state_class: measurement
    value_template: >-
      {{% if value_json.from == {node_id} and value_json.payload.barometric_pressure is defined %}}
          {{{{ (value_json.payload.barometric_pressure | float) | round(2) }}}}
      {{% else %}}
          {{{{ states('sensor.{node_short_name.lower().replace(" ", "_")}_pressure') }}}}
      {{% endif %}}
    unit_of_measurement: "hPa"
    icon: "mdi:chevron-double-down"
    device:
      identifiers: "meshtastic_{node_id}"

  - name: "{node_short_name} Gas Resistance"
    unique_id: "{node_short_name.lower().replace(" ", "_")}_gas_resistance"
    state_topic: "{root_topic}/{gateway_id}"
    state_class: measurement
    value_template: >-
      {{% if value_json.from == {node_id} and value_json.payload.gas_resistance is defined %}}
          {{{{ (value_json.payload.gas_resistance | float) | round(2) }}}}
      {{% else %}}
          {{{{ states('sensor.{node_short_name.lower().replace(" ", "_")}_gas_resistance') }}}}
      {{% endif %}}
    unit_of_measurement: "MOhms"
    icon: "mdi:dots-hexagon"
    device:
      identifiers: "meshtastic_{node_id}"

  - name: "{node_short_name} Messages"
    unique_id: "{node_short_name.lower().replace(" ", "_")}_messages"
    state_topic: "{root_topic}/{gateway_id}"
    value_template: >-
      {{% if value_json.from == {node_id} and value_json.payload.text is defined %}}
          {{{{ value_json.payload.text }}}}
      {{% else %}}
          {{{{ states('sensor.{node_short_name.lower().replace(" ", "_")}_messages') }}}}
      {{% endif %}}
    device:
      identifiers: "meshtastic_{node_id}"
    icon: "mdi:chat"
        '''

    with open("mqtt.yaml", "a") as file:
        file.write(config + '\n')

iface.close()