from datetime import datetime, timedelta
import time
from tornado import ioloop, httpclient, gen
import sys,os,binascii


devices= ["device1", "device2","device3","device4","device5","device6", "device7","device8","device9","device10"]
devices= [{"name":"device1"}]

processControlAsyncCalls = {}


def handle_request_NetDeviceCommands(response):
    global processControlAsyncCalls

    print("regreso en el handle")

    urlRequested = response.effective_url
    procNum = urlRequested[urlRequested.find("proceso=") + 8:len(urlRequested)]

    processUpdateIntUp.update({procNum: {"procNum": procNum, "numUrl": processControlAsyncCalls[procNum]['numUrl'] - 1,
                                    "ioLoopInstance": processControlAsyncCalls[procNum]["ioLoopInstance"],
                                         "RespuestaComandos": processControlAsyncCalls[procNum]["RespuestaComandos"],
                                    "fechaInicio": processControlAsyncCalls[procNum]["fechaInicio"],
                                    'done': False
                                    }
                          })

    print(str(response.code) + "==> " + urlRequested)

    if response.code == 200:
        #servicio = json.loads(response.body)
        #if 'Error' not in json.loads(response.body):
        #    device = servicio['device']
        #    newService = {device: servicio}
        #    processControlAsyncCalls[procNum]["listaServiciosInternetUp"].update(newService)
        #    processControlAsyncCalls.update(
        #        {procNum: {"procNum": procNum, "numUrl": processControlAsyncCalls[procNum]['numUrl'],
        #                   "ioLoopBwInstance": processControlAsyncCalls[procNum]["ioLoopBwInstance"],
        #                   "listaServiciosInternetUp": processControlAsyncCalls[procNum]["listaServiciosInternetUp"],
        #                   "fechaInicio": processControlAsyncCalls[procNum]["fechaInicio"],
        #                   'done': False
        #                   }
        #         })

        print ("respuesta exitosa ===> ") +  str(response.body)
    else:
        print ("Error: ==>   ") + str(response.code)

    if processControlAsyncCalls[procNum]['numUrl'] == 0:
        processControlAsyncCalls[procNum]["ioLoopInstance"].stop()
        fechaFin = datetime.now()

        print (str(processControlAsyncCalls[procNum]["fechaInicio"]) + "- " + str(fechaFin) + "==> " + str(
            fechaFin - processControlAsyncCalls[procNum]["fechaInicio"]))

        processControlAsyncCalls.update(
            {procNum: {"procNum": procNum, "numUrl": processControlAsyncCalls[procNum]['numUrl'],
                       "ioLoopBwInstance": processControlAsyncCalls[procNum]["ioLoopBwInstance"],
                       "RespuestaComandos": processControlAsyncCalls[procNum]["RespuestaComandos"],
                       "fechaInicio": processControlAsyncCalls[procNum]["fechaInicio"],
                       "fechaFin": str(fechaFin),
                       'done': True
                       }
             })



def generateUrls(devices, procNum):

    url = "http://127.0.0.1:8051/executeNetDeviceCommands?device={device}&proceso={procNum}"
    listUrls = []
    for device in devices:
        urlAppend = url.replace("{device}", device['name'])
        urlAppend = urlAppend.replace("{procNum}",procNum)
        listUrls.append(urlAppend)

    return {"urls" : listUrls}



#NUMERO DE PROCESO
#Se usa para controlar las llamadas Async De este proceso
procNum = str(binascii.b2a_hex(os.urandom(10)))
listOfUrls = generateUrls(devices,procNum)
listOfUrls = listOfUrls['urls']
numUrl = len(listOfUrls)

newProcess = {"procNum": procNum, "numUrl": numUrl}
processControlAsyncCalls.update({procNum: newProcess})

http_client = httpclient.AsyncHTTPClient(max_clients=4)

for url in listOfUrls:
    http_client.fetch(url.strip(), handle_request_NetDeviceCommands, method='GET',
                        validate_cert=False,
                        connect_timeout=240,
                        request_timeout=240)

ioLoopInstance = ioloop.IOLoop.instance()

newProcess = {"procNum": procNum, "numUrl": numUrl, "ioLoopInstance": ioLoopInstance, 'RespuestaComandos': {},
                'fechaInicio': datetime.now(), 'done': False}
processControlAsyncCalls.update({procNum: newProcess})

ioLoopInstance.start()

print("TERMINO proceso async <=======")


print(str(processControlAsyncCalls[procNum]))

RespuestaComandos  = processControlAsyncCalls[procNum]['RespuestaComandos']
print("Remover Proceso Asyn par  Update de Interface BE by EPN <=====")
processControlAsyncCalls.pop(procNum, None)

salida = jsonify(RespuestaComandos)
