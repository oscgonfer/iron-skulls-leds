# SHOW

## Sound reactivity
Uses `sounddevice` input stream, adapting latency.

You can run the volume.py to check max sound volumes before the show.

If `AUDIO_MAX_TEST_UPDATE = True` (recommended) the max volume will be updated per animation to avoid sending unvalid frames in the sACN output.

## Messages

The OSC port is in `SERVER_PORT`, in localhost. It listens to `UDP_FILTER`, discarding the rest. The message in OSC is:

`/UDP_FILTER/ANIMATION_NAME/TI.WAIT.TO.MAX.AUDIO_REACTIVE.DYNAMIC.`

The animation name has to match a file with the .fseq extension, found in the `FSEQ_DIR` directory. Additional parameters are as follows:

- `TI`: time-in. Does a fade-in on the animation. Accepts 'ms' or 's'
	+ Examples: 100ms, 10s, 10S, 100mS
- `WAIT`: animation duration, untouched (at max brightness, defined later). Same as `TI`
- `TO`: time-out. Does a fade-out on the animation. Same as `TI`
- `MAX`: Maximum brightness (0-255)
- `AUDIO_REACTIVE`: if it reacts to audio or not. Accepts anything that starts with `t` or `T`
- `DYNAMIC`: if the animation is dynamic or not (changes beyond the timing). Same as `AUDIO_REACTIVE`

## Network

For sACN to work on the network, need to setup a fixed IP Address, unless there is a router in the way. 192.168.1.1 with 255.255.255.0 would work with this repository just fine.
