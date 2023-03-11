import sounddevice as sd
import numpy as np
import time

AUDIO_FRAMES = 1000
TEST_TIME = 30
a = sd.InputStream(extra_settings = sd.CoreAudioSettings(conversion_quality='min'))

a.start()

start = time.monotonic_ns()
prevt = start
runt = start
mvol= 0
while (runt-start)//1e9<TEST_TIME:
    lat = a.latency*1000
    runt = time.monotonic_ns()
    if (runt-prevt)//1e6<lat:
        indata = a.read(AUDIO_FRAMES)[0]
        volume_norm = np.linalg.norm(indata)*255
        mvol = max(volume_norm, mvol)
        print ("|" * int(volume_norm))
        prevt = time.monotonic_ns()

a.stop()
a.close()
print (mvol)
print ('ciao!')
