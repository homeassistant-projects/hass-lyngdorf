"""Example usage of pylyngdorf asynchronous API."""

import asyncio

from pylyngdorf import async_get_lyngdorf


async def main():
    # connect to MP-60 via serial port
    device = await async_get_lyngdorf('mp60', '/dev/ttyUSB0', asyncio.get_event_loop())

    # or connect via IP socket
    # device = await async_get_lyngdorf(
    #     'mp60', 'socket://192.168.1.100:84', asyncio.get_event_loop()
    # )

    # power control
    print('Power on')
    await device.power.on()
    await asyncio.sleep(2)

    power_state = await device.power.get()
    print(f'Power status: {power_state}')

    # volume control (dB scale)
    print('Setting volume to -35.0 dB')
    await device.volume.set(-35.0)
    await asyncio.sleep(1)

    volume = await device.volume.get()
    print(f'Current volume: {volume} dB')

    # get max volume setting
    max_vol = await device.volume.get_max()
    print(f'Max volume setting: {max_vol} dB')

    # increase volume by 1.5 dB
    await device.volume.up(1.5)
    await asyncio.sleep(1)

    volume = await device.volume.get()
    print(f'Volume after increase: {volume} dB')

    # mute control
    print('Muting')
    await device.mute.on()
    await asyncio.sleep(1)

    mute_state = await device.mute.get()
    print(f'Mute status: {mute_state}')

    await device.mute.off()

    # source control
    print('\nDiscovering sources...')
    sources = await device.source.discover()
    for idx, name in sources.items():
        print(f'  {idx}: {name}')

    print('\nGetting current source')
    source_info = await device.source.get()
    print(f'Current source: {source_info}')

    # switch to source 1
    print('Switching to source 1')
    await device.source.set(1)
    await asyncio.sleep(1)

    # get source volume offset
    offset = await device.source.get_offset()
    print(f'Source volume offset: {offset} dB')

    # RoomPerfect control
    print('\nRoomPerfect positions:')
    positions = await device.roomperfect.discover_positions()
    for idx, name in positions.items():
        print(f'  {idx}: {name}')

    current_pos = await device.roomperfect.get_position()
    print(f'Current position: {current_pos}')

    # set to focus position 2
    await device.roomperfect.set_position(2)

    # RoomPerfect voicings
    print('\nRoomPerfect voicings:')
    voicings = await device.roomperfect.discover_voicings()
    for idx, name in voicings.items():
        print(f'  {idx}: {name}')

    current_voicing = await device.roomperfect.get_voicing()
    print(f'Current voicing: {current_voicing}')

    # audio mode control
    print('\nAudio modes:')
    modes = await device.audio_mode.discover()
    for idx, name in modes.items():
        print(f'  {idx}: {name}')

    current_mode = await device.audio_mode.get()
    print(f'Current mode: {current_mode}')

    # trim controls
    center_trim = await device.trim.get_center()
    print(f'\nCenter channel trim: {center_trim} dB')

    await device.trim.set_center(1.0)  # +1.0 dB
    center_trim = await device.trim.get_center()
    print(f'After adjustment: {center_trim} dB')

    # lipsync control
    lipsync_delay = await device.lipsync.get()
    print(f'\nLipsync delay: {lipsync_delay} ms')

    lipsync_range = await device.lipsync.get_range()
    print(f'Lipsync range: {lipsync_range}')

    # increase lipsync by 5ms
    await device.lipsync.up()

    # loudness control
    loudness = await device.loudness.get()
    print(f'\nLoudness: {loudness}')

    # Zone 2 control
    print('\nZone 2 power on')
    await device.zone_2.power.on()
    await asyncio.sleep(1)

    print('Setting Zone 2 volume to -45.0 dB')
    await device.zone_2.volume.set(-45.0)

    z2_vol = await device.zone_2.volume.get()
    print(f'Zone 2 volume: {z2_vol} dB')

    print('Discovering Zone 2 sources')
    z2_sources = await device.zone_2.source.discover()
    for idx, name in z2_sources.items():
        print(f'  {idx}: {name}')

    print('Setting Zone 2 to source 3')
    await device.zone_2.source.set(3)

    z2_source = await device.zone_2.source.get()
    print(f'Zone 2 current source: {z2_source}')

    # device info
    device_name = await device.device.name()
    print(f'\nDevice name: {device_name}')

    interface = await device.device.get_interface()
    print(f'Device interface: {interface}')

    verbosity = await device.device.get_verbosity()
    print(f'Verbosity level: {verbosity}')

    # ping test
    ping_result = await device.device.ping()
    if ping_result:
        print('Device responding to ping')

    # MP-60 specific features
    if hasattr(device, 'dts_dialog'):
        print('\nDTS Dialog Control available')
        dts_available = await device.dts_dialog.is_available()
        if dts_available:
            dts_level = await device.dts_dialog.get()
            print(f'DTS Dialog level: {dts_level} dB')

            # adjust DTS Dialog
            await device.dts_dialog.up()
            dts_level = await device.dts_dialog.get()
            print(f'DTS Dialog after increase: {dts_level} dB')

    print('\nPower off')
    await device.power.off()


if __name__ == '__main__':
    asyncio.run(main())
