#!/usr/bin/env python3
# Basic Python Plugin Example
#
# Author: GizMoCuz
#
"""
<plugin key="DomoticzFairlandModbus" name="Fairland Modbus" author="NijeboerFrank" version="0.1.0" wikilink="https://github.com/NijeboerFrank/DomoticzFairlandModbus/wiki">
    <description>
        <h2>Domoticz Fairland Modbus</h2><br/>
    </description>
    <params>
      <param field="Address" label="IP Address" />
      <param field="Port" label="Port Number" />
      <param field="Mode1" label="Pollrate" />
    </params>
</plugin>
"""
from typing import Callable

from pymodbus.client.common import ReadCoilsResponse, ReadHoldingRegistersResponse, ReadInputRegistersResponse
from pymodbus.exceptions import ModbusException
import Domoticz
from pymodbus.client.sync import ModbusTcpClient

RUNNING_MODE_MAPPING = {
    0: "Smart",
    1: "Silent",
    2: "Super Silent",
    3: "Turbo",
}

OPTIONS = {
    "LevelNames": "Off|Smart|Silent|Super Silent|Turbo",
    "LevelOffHidden": "true",
    "SelectorStyle": "0",
}

REVERSE_RUNNING_MODE_MAP = {
    10: 0,
    20: 1,
    30: 2,
    40: 3,
}

ERROR_MESSAGE_MAP = {
    0: "E0 Unknown Error",
    1: "E1 Unknown Error",
    2: "E2 Unknown Error",
    3: "E3 No water protection",
    4: "E4 Three phase sequence protection (three phase only)",
    5: "E5 Power supply excesses operation range",
    6: "E6 Excessive temp difference between inlet and outlet water(Insufficient water flow protection)",
    7: "E7 Unknown Error",
    8: "E8 Unknown Error",
    9: "E9 Unknown Error",
    10: "EA Evaporator overheat protection (only at cooling mode)",
    11: "EB Anti-freezing reminder",
    12: "EC Unknown Error",
    13: "ED Ambient temperature too high or too low protection",
    14: "EE Unknown Error",
    15: "EF Unknown Error",
    16: "P0 Controller communication failure",
    17: "P1 Water inlet temp sensor failure",
    18: "P2 Water outlet temp sensor failure",
    19: "P3 Gas exhaust temp sensor failure",
    20: "P4 Evaporator coil pipe temp sensor failure",
    21: "P5 Gas return temp sensor failure",
    22: "P6 Cooling coil pipe temp sensor failure",
    23: "P7 Ambient temp sensor failure",
    24: "P8 Cooling plate sensor failure",
    25: "P9 Current sensor failure",
    26: "PA Restart memory failure",
    27: "PB Unknown Error",
    28: "PC Unknown Error",
    29: "PD Unknown Error",
    30: "PE Unknown Error",
    31: "PF Unknown Error",
    32: "F0 Unknown Error",
    33: "F1 Compressor drive module failure",
    34: "F2 PFC module failure",
    35: "F3 Compressor start failure",
    36: "F4 Compressor running failure",
    37: "F5 Inverter board over current protection",
    38: "F6 Inverter board overheat protection",
    39: "F7 Current protection",
    40: "F8 Cooling plate overheat protection",
    41: "F9 Fan motor failure",
    42: "FA PFC module over current protection",
    43: "FB Power filter plate No-power protection",
    44: "FC Unknown Error",
    45: "FD Unknown Error",
    46: "FE Unknown Error",
    47: "FF Unknown Error",
}


class FairlandModbusClient:

    def __init__(self, ip_address: str, port: int):
        self._client = ModbusTcpClient(host=ip_address, port=port)

    def get_outlet_temperature(self):
        Domoticz.Log("Getting Outlet Temp")
        return self.get_temp(4, self._client.read_input_registers)

    def get_inlet_temperature(self):
        Domoticz.Log("Getting Inlet Temp")
        return self.get_temp(3, self._client.read_input_registers)

    def get_ambient_temperature(self):
        Domoticz.Log("Getting Ambient Temp")
        return self.get_temp(5, self._client.read_input_registers)

    def get_heating_temperature(self):
        Domoticz.Log("Getting Heating Temp")
        return self.get_temp(3, self._client.read_holding_registers)

    def get_temp(self, address: int, function: Callable):
        if not self._client.connect():
            Domoticz.Log("Could not get temp due to connection error")
            return None
        response = function(address=address, count=1, unit=1)
        if isinstance(response, ModbusException):
            Domoticz.Log("Could not get temp due to connection error")
            return None
        degree = ((response.registers[0] - 96) / 2) + 18
        return f"{degree}"

    def get_speed_percentage(self):
        if not self._client.connect():
            Domoticz.Log("Could not get speed percentage due to connection error")
            return None
        Domoticz.Log("Getting Running Speed")
        response: ReadInputRegistersResponse = self._client.read_input_registers(address=0, count=1, unit=1)
        if isinstance(response, ModbusException):
            Domoticz.Log("Could not get speed percentage due to connection error")
            return None
        return f"{response.registers[0]}"

    def get_running_mode(self):
        if not self._client.connect():
            Domoticz.Log("Could not get running mode due to connection error")
            return None
        Domoticz.Log("Getting running mode")
        response: ReadHoldingRegistersResponse = self._client.read_holding_registers(address=1, count=1, unit=1)
        if isinstance(response, ModbusException):
            Domoticz.Log("Could not get running mode due to connection error")
            return None
        return response.registers[0]

    def set_running_mode(self, mode: int):
        if not self._client.connect():
            Domoticz.Log("Could not set running mode due to connection error")
            return None
        new_mode_number = REVERSE_RUNNING_MODE_MAP.get(mode)
        if new_mode_number is None:
            Domoticz.Log(f"Invalid/unknown running mode {mode}")
            return
        new_mode = RUNNING_MODE_MAPPING.get(new_mode_number)
        Domoticz.Log(f"Setting device to mode {mode} ({new_mode})")
        Domoticz.Log(f"Writing {new_mode_number} on address 1")
        response = self._client.write_register(address=1, value=new_mode_number, unit=1)
        if isinstance(response, ModbusException):
            Domoticz.Log("Cannot set running mode due to connection error")

    def set_heating_temp(self, temperature: float):
        if not self._client.connect():
            Domoticz.Log("Could not set heating temp due to connection error")
            return None
        Domoticz.Log(f"Setting device to heating temp {temperature}")
        register_value = (temperature - 18) * 2 + 96
        response = self._client.write_register(address=3, value=int(register_value), unit=1)
        if isinstance(response, ModbusException):
            Domoticz.Log("Cannot set heating temp due to connection error")


    def turn_on_off(self, on: bool):
        if not self._client.connect():
            Domoticz.Log("Could not turn on/off due to connection error")
            return None
        Domoticz.Log(f"Turning device {'on' if on else 'off'}")
        response = self._client.write_coil(address=0, value=int(on), unit=1)
        if isinstance(response, ModbusException):
            Domoticz.Log("Cannot turn on/off due to connection error")


    def get_on_off_state(self):
        if not self._client.connect():
            Domoticz.Log("Could not get on/off state due to connection error")
            return None
        Domoticz.Log("Fetching on/off state")
        response: ReadCoilsResponse = self._client.read_coils(address=0, count=1, unit=1)
        if isinstance(response, ModbusException):
            Domoticz.Log("Could not get on/off state due to connection error")
            return None
        return response.bits[0]


    def get_error_state(self):
        if not self._client.connect():
            Domoticz.Log("Could not get error state due to connection error")
            return None
        Domoticz.Log("Fetching Error State")
        response: ReadDiscreteInputsResponse = self._client.read_discrete_inputs(address=48, count=48, unit=1)
        if isinstance(response, ModbusException):
            Domoticz.Log("Could not get error state due to connection error")
            return None
        indices = [index for index, v in enumerate(response.bits) if v == 1]
        return indices

    def get_wp_state(self):
        if not self._client.connect():
            Domoticz.Log("Could not get wp state due to connection error")
            return None
        Domoticz.Log("Fetching Device State")
        response: ReadDiscreteInputsResponse = self._client.read_discrete_inputs(address=0, count=48, unit=1)
        if isinstance(response, ModbusException):
            Domoticz.Log("Could not get wp state due to connection error")
            return None
        return "".join(map(str, map(int, response.bits)))


class BasePlugin:
    enabled = False

    def __init__(self):
        self._client = None
        return

    def onStart(self):
        Domoticz.Log("onStart called")

        try:
            pollrate = int(Parameters["Mode1"])
            Domoticz.Log(f"Setting pollrate to {pollrate}")
            Domoticz.Heartbeat(int(pollrate))
        except Exception as e:
            Domoticz.Log(f"Could not set pollrate because of exception '{e}'")

        self._client = FairlandModbusClient(ip_address=Parameters["Address"], port=Parameters["Port"])

        if len(Devices) == 0:
            Domoticz.Device(Name=f"Outlet Temperature", Unit=1, TypeName="Temperature", Used=1).Create()
            Domoticz.Device(Name=f"Inlet Temperature", Unit=2, TypeName="Temperature", Used=1).Create()
            Domoticz.Device(Name=f"Ambient Temperature", Unit=3, TypeName="Temperature", Used=1).Create()
            Domoticz.Device(Name=f"Heating Temperature", Unit=4, Type=242, Subtype=1, Used=1).Create()
            Domoticz.Device(Name=f"Running Speed", Unit=5, TypeName="Percentage", Used=1).Create()
            Domoticz.Device(Name=f"Running Mode", Unit=6, TypeName="Selector Switch", Options=OPTIONS, Image=7, Used=1).Create()
            Domoticz.Device(Name=f"On/Off Switch", Unit=7, TypeName="Selector Switch", Switchtype=0, Image=15, Used=1).Create()
            Domoticz.Device(Name=f"Error Status", Unit=8, Type=243, Subtype=19, Used=1).Create()
            Domoticz.Device(Name=f"Device Status", Unit=9, Type=243, Subtype=19, Used=1).Create()

    def onStop(self):
        Domoticz.Log("onStop called")

    def onConnect(self, Connection, Status, Description):
        Domoticz.Log("onConnect called")

    def onMessage(self, Connection, Data):
        Domoticz.Log("onMessage called")

    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Log("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))

        if self._client is None:
            Domoticz.Log("Could not update values, because ModbusClient is not initialized")
            return

        if Unit==6:
            Domoticz.Log("Received Set Running Mode command")
            self._client.set_running_mode(Level)
            Devices[6].Update(nValue=Devices[7].nValue, sValue=f"{list(REVERSE_RUNNING_MODE_MAP.keys())[self._client.get_running_mode()]}")

        elif Unit==4:
            Domoticz.Log("Received Set Heating temp command")
            self._client.set_heating_temp(float(Level))
            Devices[4].Update(nValue=0, sValue=self._client.get_heating_temperature())

        elif Unit==7:
            Domoticz.Log("Received turn on/off command")
            turn_on = (Command.lower() == 'on')
            self._client.turn_on_off(on=turn_on)
            on_off = self._client.get_on_off_state()
            Devices[7].Update(nValue=on_off, sValue=f"{on_off}")

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Log("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        Domoticz.Log("onDisconnect called")

    def onHeartbeat(self):
        Domoticz.Log("onHeartbeat called")
        if len(Devices) == 0:
            Domoticz.Log("Could not update because devices list is 0")
            return

        if self._client is None:
            Domoticz.Log("Could not update values, because ModbusClient is not initialized")
            return

        # TODO: Make this less ugly
        outlet_temp = self._client.get_outlet_temperature()
        if outlet_temp is None:
            return None
        Devices[1].Update(nValue=0, sValue=outlet_temp)
        inlet_temp = self._client.get_inlet_temperature()
        if inlet_temp is None:
            return None
        Devices[2].Update(nValue=0, sValue=inlet_temp)
        ambient_temp = self._client.get_ambient_temperature()
        if ambient_temp is None:
            return None
        Devices[3].Update(nValue=0, sValue=ambient_temp)
        heating_temp = self._client.get_heating_temperature()
        if heating_temp is None:
            return None
        Devices[4].Update(nValue=0, sValue=heating_temp)
        speed_percentage = self._client.get_speed_percentage()
        if speed_percentage is None:
            return None
        Devices[5].Update(nValue=0, sValue=speed_percentage)
        running_mode = self._client.get_running_mode()
        if running_mode is None:
            return None
        Devices[6].Update(nValue=Devices[7].nValue, sValue=f"{list(REVERSE_RUNNING_MODE_MAP.keys())[running_mode]}")
        on_off = self._client.get_on_off_state()
        if on_off is None:
            return None
        Devices[7].Update(nValue=on_off, sValue=f"{on_off}")

        error_numbers = self._client.get_error_state()
        if error_numbers is None:
            return None
        if len(error_numbers) == 0:
            Devices[8].Update(nValue=0, sValue="Running Normal")
        else:
            Devices[8].Update(nValue=0, sValue=f"{' : '.join([ERROR_MESSAGE_MAP.get(error_number) for error_number in error_numbers])}")

        wp_state = self._client.get_wp_state()
        if wp_state is None:
            return None
        Devices[9].Update(nValue=0, sValue=f"{wp_state}")

global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)

def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)

def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)

def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)

def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

    # Generic helper functions
def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug( "'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
    return
