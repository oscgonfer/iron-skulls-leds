from threading import Thread, Event, Lock, current_thread
from queue import Queue
from config import *
from tools import *
import time
import sounddevice as sd
print_lock = Lock()

sender = start_sender()
fseqs = get_fseqs(FSEQ_DIR)

class FseqAnimator (Thread):
    def __init__(self, queue, parent):
        super(FseqAnimator, self).__init__()
        self.queue = queue
        self.parent = parent
        self.event = Event()
        self.daemon = True
        self.t = None
        self.audio_stream = sd.InputStream()
        self.audio_max = AUDIO_MAX_TEST
        self.audio_max_update = AUDIO_MAX_TEST_UPDATE

    def run (self):
        frame_index = 0

        while not self.event.isSet():
            if not self.queue.empty():
                animation = self.queue.get()
                std_out (f'Received animation: {animation}', 'THREAD')
                if '/' in animation:
                    std_out (f'Animation has params', 'THREAD')
                    animation_name = animation.split('/')[0]
                    animation_params = animation.split('/')[1]
                else:
                    animation_name = animation
                    animation_params = None

                self.send_sacn(animation_name, animation_params)
            else:
                # We wait to avoid loading the cpu without need...
                self.event.wait(timeout=(0.1))

    def join (self, timeout=None):
        self.event.set()
        super(FseqAnimator, self).join(timeout)

    def stop(self):
        if self.is_alive():
            self.audio_stream.stop()
            self.audio_stream.close()
            self.join()

    def send_sacn (self, animation_name, animation_params):
        # if self.receive_messages:

            t = current_thread()
            with print_lock:
                # print ('[THREAD]:', t.getName(), "Received animation {}".format(animation_name))
                # print ('[THREAD]:', t.getName(), "With parameter {}".format(animation_params))
                print ('[THREAD]:', "Received animation {}".format(animation_name))
                print ('[THREAD]:', "With parameter {}".format(animation_params))

            # Get desired fseq
            if animation_name in fseqs:
                fseq = fseqs[animation_name]
            else:
                return

            if animation_params is not None:
                ap = parse_animation_params(animation_params)
                std_out(f'Params: {ap}', 'THREAD')
            else:
                ap = ANIMATION_DEFAULTS

            start_time = time.monotonic_ns()
            # std_out(f'Animation start time (ms): {start_time//1e6}', 'THREAD')
            # prev_time = start_time
            a = 1
            if ap['audio']:
                self.audio_stream.start()
                latency = self.audio_stream.latency*1000 # Latency in ms

            if ap['dynamic']:
                # If using a dynamic animation, the animation intensity will
                # still be used, and multiplied by the intensity function from here
                # the animation itself has to run for as much time needed, as there will
                # be no looping here to avoid weird behaviour
                prevt = time.monotonic_ns() - start_time
                for frame_index in range(fseq.number_of_frames):
                    runt = time.monotonic_ns() - start_time
                    std_out(f'Animation run time (ms): {runt//1e6}', 'DEBUG')

                    frame = frame_to_tuple(fseq.get_frame(frame_index), fseq.channel_count_per_frame)
                    m = intensity_multiplier(ap['ti'], ap['wait'], ap['to'], runt//1e6, ap['max'])

                    if ap['audio']:
                        # Do this to avoid latency issues
                        if (runt-prevt)//1e6<latency:

                            araw = audio_multiplier(self.audio_stream)
                            prevt = time.monotonic_ns()

                            if self.audio_max_update:
                                if araw > self.audio_max:
                                    std_out(f'Updated AUDIO_MAX_TEST to {araw}', 'THREAD')
                                    self.audio_max = araw

                            a = araw*(AUDIO_MAX_EFFECT-AUDIO_MIN_EFFECT)/self.audio_max+AUDIO_MIN_EFFECT

                    fm = tuple(max(0,round(x*m*a)) for x in frame)

                    for universe in range(RECEIVER_UNIVERSES):
                        frame2send = fm[universe*ANIMATION_CHANNEL_COUNT:(universe+1)*ANIMATION_CHANNEL_COUNT]
                        if len(frame2send):
                            sender[universe+1].dmx_data = frame2send

                    # TODO Check issue with timing. It is not true!!
                    dt = time.monotonic_ns() - runt - start_time
                    self.event.wait(timeout=(fseq.step_time_in_ms - dt//1e6)/1000)
                    std_out(f'Elapsed time: {dt//1e6}', 'DEBUG')

            else:

                # std_out(f'Animation run time (ms): {runt//1e6}', 'THREAD')
                frame = frame_to_tuple(fseq.get_frame(0), fseq.channel_count_per_frame)
                # Do it with a for instead of a while to avoid blocking
                frames = (ap['ti']+ap['wait']+ap['to'])//fseq.step_time_in_ms
                prevt = time.monotonic_ns() - start_time
                for frame_index in range(frames):
                    runt = time.monotonic_ns() - start_time

                    m = intensity_multiplier(ap['ti'], ap['wait'], ap['to'], runt//1e6, ap['max'])

                    if ap['audio']:
                        # Do this to avoid latency issues
                        if (runt-prevt)//1e6<latency:

                            araw = audio_multiplier(self.audio_stream)
                            prevt = time.monotonic_ns()

                            if self.audio_max_update:
                                if araw > self.audio_max:
                                    std_out(f'Updated AUDIO_MAX_TEST to {araw}', 'THREAD')
                                    self.audio_max = araw

                            a = araw*(AUDIO_MAX_EFFECT-AUDIO_MIN_EFFECT)/self.audio_max+AUDIO_MIN_EFFECT

                    fm = tuple(max(0,round(x*m*a)) for x in frame)

                    for universe in range(RECEIVER_UNIVERSES):
                        frame2send = fm[universe*ANIMATION_CHANNEL_COUNT:(universe+1)*ANIMATION_CHANNEL_COUNT]
                        if len(frame2send):
                            sender[universe+1].dmx_data = frame2send

                    # TODO Check issue with timing. It is not true!!
                    dt = time.monotonic_ns() - runt - start_time
                    self.event.wait(timeout=(fseq.step_time_in_ms - dt//1e6)/1000)
