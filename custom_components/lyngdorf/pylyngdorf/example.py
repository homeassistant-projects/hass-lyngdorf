"""Example usage of pylyngdorf synchronous API."""

import time
from pylyngdorf import get_lyngdorf

# connect to MP-50 via serial port
device = get_lyngdorf('mp50', '/dev/ttyUSB0')

# or connect via IP socket
# device = get_lyngdorf('mp50', 'socket://192.168.1.100:84')

# power control
print('Power on')
device.power.on()
time.sleep(2)

print(f'Power status: {device.power.get()}')

# volume control (dB scale)
print('Setting volume to -30.0 dB')
device.volume.set(-30.0)
time.sleep(1)

print(f'Current volume: {device.volume.get()} dB')

# increase volume by 2 dB
device.volume.up(2.0)
time.sleep(1)

print(f'Volume after increase: {device.volume.get()} dB')

# mute control
print('Muting')
device.mute.on()
time.sleep(1)

print(f'Mute status: {device.mute.get()}')

device.mute.off()

# source control
print('\nDiscovering sources...')
sources = device.source.discover()
for idx, name in sources.items():
    print(f'  {idx}: {name}')

print('\nGetting current source')
source_info = device.source.get()
print(f'Current source: {source_info}')

# switch to source 1 (typically HDMI)
print('Switching to source 1')
device.source.set(1)
time.sleep(1)

# RoomPerfect control
print('\nRoomPerfect positions:')
positions = device.roomperfect.discover_positions()
for idx, name in positions.items():
    print(f'  {idx}: {name}')

current_pos = device.roomperfect.get_position()
print(f'Current position: {current_pos}')

# set to focus position 1
device.roomperfect.set_position(1)

# audio mode control
print('\nAudio modes:')
modes = device.audio_mode.discover()
for idx, name in modes.items():
    print(f'  {idx}: {name}')

current_mode = device.audio_mode.get()
print(f'Current mode: {current_mode}')

# trim controls
print(f'\nCenter channel trim: {device.trim.get_center()} dB')
device.trim.set_center(0.5)  # +0.5 dB
print(f'After adjustment: {device.trim.get_center()} dB')

# lipsync control
lipsync_delay = device.lipsync.get()
print(f'\nLipsync delay: {lipsync_delay} ms')

# get range
lipsync_range = device.lipsync.get_range()
print(f'Lipsync range: {lipsync_range}')

# Zone 2 control
print('\nZone 2 power on')
device.zone_2.power.on()
time.sleep(1)

print('Setting Zone 2 volume to -40.0 dB')
device.zone_2.volume.set(-40.0)

print('Setting Zone 2 to source 2')
device.zone_2.source.set(2)

# device info
print(f'\nDevice name: {device.device.name()}')
print(f'Device interface: {device.device.get_interface()}')
print(f'Verbosity level: {device.device.get_verbosity()}')

# ping test
if device.device.ping():
    print('Device responding to ping')

# MP-60 specific features
if hasattr(device, 'dts_dialog'):
    print('\nDTS Dialog Control available')
    if device.dts_dialog.is_available():
        dts_level = device.dts_dialog.get()
        print(f'DTS Dialog level: {dts_level} dB')

print('\nPower off')
device.power.off()
