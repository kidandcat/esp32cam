"""
Copyright 2020 LeMaRiva|Tech (Mauro Riva) info@lemariva.com
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
    http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import gc
import machine
import json
import time
import camera

from microWebSrv import MicroWebSrv

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

class webcam():

    def __init__(self):
        self.saturation = 0
        self.quality = 10
        self.brightness = 0
        self.contrast = 0
        self.vflip = 0
        self.hflip = 0
        self.flash = 0
        self.framesize = camera.FRAME_VGA
        self.routeHandlers = [
            ("/", "GET", self._httpHandlerIndex),
            ("/logo.svg", "GET", self._httpLogo),
            ("/stream/<d>", "GET", self._httpStream),
            ("/upy/<saturation>/<brightness>/<contrast>/<quality>/<vflip>/<hflip>/<framesize>/<flash>", "GET", self._httpHandlerSetData),
            ("/upy", "GET", self._httpHandlerGetData),
            ("/memory/<query>", "GET", self._httpHandlerMemory)
        ]

    def run(self, app_config):
        self.led = machine.Pin(app_config['led'], machine.Pin.OUT)
        camera.init(0, format=camera.JPEG, framesize=self.framesize)      #ESP32-CAM
        mws = MicroWebSrv(routeHandlers=self.routeHandlers, webPath="www/")
        mws.Start(threaded=True)
        gc.collect()

    def _httpStream(self, httpClient, httpResponse, routeArgs):
        image = camera.capture()
        headers = { 'Last-Modified' : 'Fri, 1 Jan 2018 23:42:00 GMT', \
                    'Cache-Control' : 'no-cache, no-store, must-revalidate' }
        httpResponse.WriteResponse(code=200, headers=headers,
                                    contentType="image/jpeg",
                                    contentCharset="UTF-8",
                                    content=image)

    def _httpLogo(self, httpClient, httpResponse):
        f = open("www/logo.svg", "r")
        content =  f.read()
        f.close()
        httpResponse.WriteResponseOk(headers=None,
                                    contentType="image/svg+xml",
                                    contentCharset="UTF-8",
                                    content=content)

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
        self.saturation = int(routeArgs['saturation']) - 2
        self.brightness = int(routeArgs['brightness']) - 2 
        self.contrast = int(routeArgs['contrast']) - 2
        self.quality = int(routeArgs['quality'])
        self.vflip = bool(routeArgs['vflip'])
        self.hflip = bool(routeArgs['hflip'])
        self.flash = bool(routeArgs['flash'])
        self.framesize = int(routeArgs['framesize'])
        camera.saturation(self.saturation)
        camera.brightness(self.brightness)
        camera.contrast(self.contrast)
        camera.quality(self.quality)
        camera.flip(self.vflip)
        camera.mirror(self.hflip)
        camera.framesize(self.framesize)
        self.led.value(self.flash)
        data = {
            'saturation': self.saturation,
            'brightness': self.brightness,
            'contrast': self.contrast,
            'quality': self.quality,
            'vflip': self.vflip,
            'hflip': self.hflip,
            'flash': self.flash,
            'framesize': self.framesize
        }
        self._newdata = True
        httpResponse.WriteResponseOk(headers=None,
                                        contentType="text/html",
                                        contentCharset="UTF-8",
                                        content=json.dumps(data))

    def _httpHandlerGetData(self, httpClient, httpResponse):
        data = {
            'saturation': self.saturation,
            'brightness': self.brightness,
            'contrast': self.contrast,
            'quality': self.quality,
            'vflip': self.vflip,
            'hflip': self.hflip,
            'flash': self.flash,
            'framesize': self.framesize
        }
        httpResponse.WriteResponseOk(headers=None,
                                    contentType="application/json",
                                    contentCharset="UTF-8",
                                    content=json.dumps(data))

    def _httpHandlerMemory(self, httpClient, httpResponse, routeArgs):
        print("In Memory HTTP variable route :")
        query = str(routeArgs['query'])
        if 'gc' in query or 'collect' in query:
            gc.collect()
        content = """\
            {}
            """.format(gc.mem_free())
        httpResponse.WriteResponseOk(headers=None,
                                    contentType="text/html",
                                    contentCharset="UTF-8",
                                    content=content)




