from os import walk
from os.path import join
from fseq import parse
from sacn import sACNsender
from config import *
import numpy as np

def std_out(msg, who):
    if DEBUG:
        print (f'[{who}]: {msg}')
    elif who != 'DEBUG':
        print (f'[{who}]: {msg}')

def get_fseqs(FSEQ_DIR):

    fseqs = dict()

    for root, dirs, files in walk(FSEQ_DIR):
        for _file in files:
            if _file.endswith(".fseq"):
                std_out (_file, "MAIN")
                std_out (f'Parsing: {_file}', "MAIN")

                fseq = parse(open(join(FSEQ_DIR, _file), 'rb'))
                std_out(f"Channel count: {fseq.channel_count_per_frame // 3}", "MAIN")
                std_out(f"Frames: {fseq.number_of_frames}", "MAIN")
                std_out(f"Step Time (ms): {fseq.step_time_in_ms}", "MAIN")

                fseqs[_file.replace(".fseq", "")] = fseq
                std_out ('---', "MAIN")

    std_out (f'Available sequences: {list(fseqs.keys())}', "MAIN")
    std_out ('---', "MAIN")

    return fseqs

def start_sender():
    sender = sACNsender()

    sender.fps = RECEIVER_FPS
    sender.universeDiscovery = False

    # Start sACN sender
    sender.start()
    for universe in range(RECEIVER_UNIVERSES):
        std_out (f"Activating output in universe: {universe + 1}", "ANIMATOR")
        sender.activate_output(universe+1)
        sender[universe+1].destination = RECEIVER_IP

    sender.manual_flush = True
    sender.flush()
    sender.manual_flush = False

    return sender

def parse_animation_params(animation_params):
    '''
    Parses animation parameters
    INPUT FORMAT: TI.WAIT.TO.AR
        TI: Time in
        WAIT: DURATION
        TO: Time out
        MAX: Maximum intensity (0-255)
        AR: Audio Reactive (true or false)
        DY: Dynamic animation (true or false)
    OUTPUT:
        {
            'ti': time in (ms)
            'wait': duration in (ms)
            'to': time out (ms)
            'max': maximum intensity (0-1)
            'audio': boolean
            'dynamic': boolean
        }
    '''
    params = dict()

    def get_ms(param):
        m = 1000

        if 'ms' in param or 'MS' in param:
            m = 1
            param=int(param.replace('ms', '').replace('MS', ''))
        elif 's' in param or 'S' in param:
            m = 1000
            param=int(param.replace('s', '').replace('S', ''))

        return param*m

    def get_bool(param):
        if param.lower()=='True' or param.startswith('t'):
            return True
        elif param.lower()=='False' or param.startswith('f'):
            return False
        else:
            return False

    if animation_params.count('.') != 5:
        std_out('Wrong param format', 'WARNING')
        return ANIMATION_DEFAULTS

    params['ti'] = get_ms(animation_params.split('.')[0])
    params['wait'] = get_ms(animation_params.split('.')[1])
    params['to'] = get_ms(animation_params.split('.')[2])
    params['max'] = int(animation_params.split('.')[3])
    params['audio'] = get_bool(animation_params.split('.')[4])
    params['dynamic'] = get_bool(animation_params.split('.')[5])

    return params

def frame_to_tuple(frame, channel_count):
    l = list()

    # TODO Parse this in a better way
    for i in range(channel_count // 3):
        r, g, b = frame[i * 3], frame[i * 3 + 1], frame[i * 3 + 2]
        l.append(r)
        l.append(g)
        l.append(b)

    return tuple(l)

def intensity_multiplier(ti, wait, to, current_time, max_intensity=ANIMATION_MAX):
    '''
    Inputs in ms
    '''
    # TODO: sigmoid function?
    if current_time <= ti:
        return (current_time)/ti*max_intensity/ANIMATION_RESOLUTION
    elif current_time > ti and current_time <= ti+wait:
        return max_intensity/ANIMATION_RESOLUTION
    elif current_time >ti+wait and current_time<=ti+wait+to:
        return max_intensity/ANIMATION_RESOLUTION-(current_time-wait-ti)/to
    elif current_time > ti+wait+to:
        return 0
    return max_intensity/ANIMATION_RESOLUTION

def audio_multiplier(audio_input):
    indata = audio_input.read(audio_input.read_available)[0]
    volume_norm = np.linalg.norm(indata)*AUDIO_RESOLUTION

    return int(volume_norm)
