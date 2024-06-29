
import camera
import picoweb
import machine
import time
import uasyncio as asyncio
from config import *

led = machine.Pin(app_config['led'], machine.Pin.OUT)
app = picoweb.WebApp('app')

import ulogging as logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger('app')

async def capture():
    await asyncio.sleep(3)
    n = 0
    while True:
        buf = camera.capture()
        f = open('sd/capture'+str(n)+'.jpeg', 'wb')
        f.write(buf)
        f.close()
        n = n + 1
        await asyncio.sleep_ms(100)
        if n > 20:
            break

@app.route('/')
def index(req, resp):
    # Camera resilience - if we fail to init try to deinit and init again
    if (not camera.init(0, format=camera.JPEG, fb_location=camera.PSRAM, xclk_freq=12000000)):
        camera.deinit()
        await asyncio.sleep(1)
        # If we fail to init, return a 503
        if (not camera.init(0, format=camera.JPEG, fb_location=camera.PSRAM, xclk_freq=12000000)):  
            yield from picoweb.start_response(resp, status=503)
            yield from resp.awrite('ERROR: Failed to initialise camera\r\n\r\n')
            return
    await asyncio.sleep(2)
    # start streaming
    asyncio.create_task(capture())
    first_frame = True
    while True:
        n_try = 0
        buf = False
        while (n_try < 10 and buf == False):
            # wait for sensor to start and focus before capturing image
            buf = camera.capture()
            if (buf == False): await asyncio.sleep(2)
            n_try = n_try + 1
        if (type(buf) is bytes and len(buf) > 0):
            try:
                if (first_frame): 
                    yield from picoweb.start_response(resp, "multipart/x-mixed-replace; boundary=myboundary")
                yield from resp.awrite('--myboundary\r\n')
                yield from resp.awrite('Content-Type:   image/jpeg\r\n')
                yield from resp.awrite('Content-length: ' + str(len(buf)) + '\r\n\r\n')
                yield from resp.awrite(buf)
            except:
                print('Connection closed by client')
                led.off()
                camera.deinit()
                return
        else: 
            led.off()
            yield from picoweb.start_response(resp, status=503)
            if (not first_frame): 
                yield from resp.awrite('Content-Type:   text/html; charset=utf-8\r\n\r\n')
            yield from resp.awrite('Issues:\r\n\r\n' + str(buf))
            return
        if (first_frame): 
            first_frame = False
        await asyncio.sleep_ms(5)
    

def run():
    app.run(host='0.0.0.0', port=80, debug=False)
