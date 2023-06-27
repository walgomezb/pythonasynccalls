from datetime import datetime, timedelta
import time
from tornado import ioloop, httpclient, gen
import sys,os,binascii
from tornado.gen import multi
from tornado.httpclient import AsyncHTTPClient, HTTPRequest



devices= ["device1", "device2","device3","device4","device5","device6", "device7","device8","device9","device10"]
devices= [{"name":"device1"},{"name":"device2"},{"name":"device3"},{"name":"device4"},{"name":"device5"},{"name":"device6"},
          {"name":"device7"},{"name":"device8"},{"name":"device9"},{"name":"device10"}]

#devices= [{"name":"device1"}]


processControlAsyncCalls = {}
http_client = httpclient.AsyncHTTPClient(max_clients=4)


def generateUrls(devices, procNum):

    url = "http://127.0.0.1:9051/executeNetDeviceCommands?device={device}&proceso={procNum}"
    listUrls = []
    for device in devices:
        urlAppend = url.replace("{device}", device['name'])
        urlAppend = urlAppend.replace("{procNum}",procNum)
        listUrls.append(urlAppend)

    return {"urls" : listUrls}


def handle_request_NetDeviceCommands(response):
    global processControlAsyncCalls

    print("regreso en el handle")

    urlRequested = response.effective_url
    procNum = urlRequested[urlRequested.find("proceso=") + 8:len(urlRequested)]
    device = urlRequested[urlRequested.find("device=") + 7:urlRequested.find("&")]

    processControlAsyncCalls.update({procNum: {"procNum": procNum, "numUrl": processControlAsyncCalls[procNum]['numUrl'] - 1,
                                    "ioLoopInstance": processControlAsyncCalls[procNum]["ioLoopInstance"],
                                         "respuestaComandos": processControlAsyncCalls[procNum]["respuestaComandos"],
                                    "fechaInicio": processControlAsyncCalls[procNum]["fechaInicio"],
                                    'done': False
                                    }
                          })

    print(str(response.code) + "==> " + urlRequested)

    if response.code == 200:
        #respuesta = json.loads(response.body)
        respuesta = str(response.body)
        #if 'Error' not in json.loads(response.body):
        deviceRespuestaComando = {device:respuesta}
        if response.code == 200:
            processControlAsyncCalls[procNum]["respuestaComandos"].update(deviceRespuestaComando)
            processControlAsyncCalls.update(
                {procNum: {"procNum": procNum, "numUrl": processControlAsyncCalls[procNum]['numUrl'],
                           "ioLoopInstance": processControlAsyncCalls[procNum]["ioLoopInstance"],
                           "respuestaComandos": processControlAsyncCalls[procNum]["respuestaComandos"],
                           "fechaInicio": processControlAsyncCalls[procNum]["fechaInicio"],
                           'done': False
                           }
                 })

        print ("respuesta exitosa ===> " +  respuesta) 
    else:
        print ("Error: ==>   " + str(response.code))

    if processControlAsyncCalls[procNum]['numUrl'] == 0:
        processControlAsyncCalls[procNum]["ioLoopInstance"].stop()
        fechaFin = datetime.now()

        print (str(processControlAsyncCalls[procNum]["fechaInicio"]) + "- " + str(fechaFin) + "==> " + str(
            fechaFin - processControlAsyncCalls[procNum]["fechaInicio"]))

        processControlAsyncCalls.update(
            {procNum: {"procNum": procNum, "numUrl": processControlAsyncCalls[procNum]['numUrl'],
                       "ioLoopInstance": processControlAsyncCalls[procNum]["ioLoopInstance"],
                       "respuestaComandos": processControlAsyncCalls[procNum]["respuestaComandos"],
                       "fechaInicio": processControlAsyncCalls[procNum]["fechaInicio"],
                       "fechaFin": str(fechaFin),
                       'done': True
                       }
             })

@gen.coroutine
def post(urls):
    for url in urls:
        request = HTTPRequest(url,method='GET',
                        validate_cert=False,
                        connect_timeout=240,
                        request_timeout=240)
        #Don't yield, just kkeep adding requests

        future = http_client.fetch(request)

        def done_callback(future):
            try:
                print("dentro del callback")
                #print(future.result())
                #str(future.result().body)
                #future.result().code
                #future.result().effective_url
                #future.result().error
                #future.result().request_time
                #future.result().start_time
                handle_request_NetDeviceCommands(future.result())
            except Exception as exc:
                print("error exception")
                print(exc)

        future.add_done_callback(done_callback)
    

#NUMERO DE PROCESO
#Se usa para controlar las llamadas Async De este proceso
procNum = str(binascii.b2a_hex(os.urandom(10)))
listOfUrls = generateUrls(devices,procNum)
listOfUrls = listOfUrls['urls']
numUrl = len(listOfUrls)

loop = ioloop.IOLoop.current()
newProcess = {"procNum": procNum, "numUrl": numUrl,"ioLoopInstance": loop,
              'respuestaComandos': {}, 'fechaInicio': datetime.now(),'done': False}
processControlAsyncCalls.update({procNum: newProcess})

post(listOfUrls)

#def done(future):
#    print("Done Loop")
#    loop.stop()

loop.start()
print("Done Loop...Salida de programa")