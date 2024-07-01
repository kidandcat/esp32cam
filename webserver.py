import gc
import machine
import json
import camera
import time
from microWebSrv import MicroWebSrv

config = {
    "saturation": 0,
    "brightness": 0,
    "contrast": 0,
    "quality": 10,
    "vflip": 0,
    "hflip": 0,
    "flash": 0,
    "framesize": camera.FRAME_VGA
}

class webcam():
    
    def __init__(self):
        self.led = machine.Pin(4, machine.Pin.OUT)
        self.routeHandlers = [
            ("/", "GET", self._httpHandlerIndex),
            ("/stream", "GET", self._httpStream),
            ("/upy/<saturation>/<brightness>/<contrast>/<quality>/<vflip>/<hflip>/<framesize>/<flash>", "GET", self._httpHandlerSetData),
            ("/upy", "GET", self._httpHandlerGetData),
        ]

    def capture(self):
        time.sleep(3)
        n = 0
        while True:
            buf = camera.capture()
            f = open('sd/capture'+str(n)+'.jpeg', 'wb')
            f.write(buf)
            f.close()
            n = n + 1
            if n > 20:
                break

    def run(self):
        try:
            camera.init(0, format=camera.JPEG, framesize=config['framesize'])
            mws = MicroWebSrv(routeHandlers=self.routeHandlers, webPath="www/")
            mws.Start() # Blocking call
        except Exception as e:
            print('Web server exception:', e)
            machine.reset()

    def _httpStream(self, httpClient, httpResponse):
        httpResponse.WriteResponseStreamHeader()
        try:
            while True:
                image = camera.capture()
                if not httpResponse.WriteResponseStreamData(image):
                    break
        except Exception as e:
            print('Stream handler exception:', e)

    def _httpHandlerIndex(self, httpClient, httpResponse):
        f = open("www/index.html", "r")
        content =  f.read()
        f.close()
        headers = { 'Last-Modified' : 'Fri, 1 Jan 2018 23:42:00 GMT', \
                            'Cache-Control' : 'no-cache, no-store, must-revalidate' }
        httpResponse.WriteResponseOk(headers=None,
                                    contentType="text/html",
                                    contentCharset="UTF-8",
                                    content=content)

    def _httpHandlerSetData(self, httpClient, httpResponse, routeArgs):
        config['saturation'] = int(routeArgs['saturation']) - 2
        config['brightness'] = int(routeArgs['brightness']) - 2
        config['contrast'] = int(routeArgs['contrast']) - 2
        config['quality'] = int(routeArgs['quality'])
        config['vflip'] = bool(routeArgs['vflip'])
        config['hflip'] = bool(routeArgs['hflip'])
        config['flash'] = bool(routeArgs['flash'])
        config['framesize'] = int(routeArgs['framesize'])
        camera.saturation(config['saturation'])
        camera.brightness(config['brightness'])
        camera.contrast(config['contrast'])
        camera.quality(config['quality'])
        camera.flip(config['vflip'])
        camera.mirror(config['hflip'])
        camera.framesize(config['framesize'])
        self.led.value(config['flash'])
        httpResponse.WriteResponseOk(headers=None,
                                        contentType="text/html",
                                        contentCharset="UTF-8",
                                        content=json.dumps(config))

    def _httpHandlerGetData(self, httpClient, httpResponse):
        httpResponse.WriteResponseOk(headers=None,
                                    contentType="application/json",
                                    contentCharset="UTF-8",
                                    content=json.dumps(config))



