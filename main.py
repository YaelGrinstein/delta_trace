import numpy as np
import socketio
from delta_trace import DeltaCorrection
import threading
import logging
from time import time

delta_trace = DeltaCorrection()
fixed = 0
stop_thread = False
data = None
udpData = {}

logging.basicConfig(level=logging.WARNING,
                    format='(%(threadName)-9s) %(message)s', )

sio = socketio.Client()
# idan
# sio.connect('http://172.16.10.87:4000')
sio.connect('http://52.21.204.230:4000')


@sio.event
def connect():
    print('connection established')


@sio.event()
def disconnect():
    global stop_thread
    print('disconnected from server')
    stop_thrad = True
    t1.join()


@sio.on("new-packet-shelf")
# steady-shel
def on_message(data):
    global udpData

    # check the first time shelf data arrive
    if not data['boardId'] in udpData:
        udpData[data['boardId']] = [[], [], [True]]

    udpData[data['boardId']][0].append(np.array(data['packet']))


def delta_trace_execute():
    global udpData
    while True:
        # data received from server, handle
        for key in list(udpData):
            if len(udpData.get(key)[0]) > 1 and len(udpData.get(key)[1]) >= 1:
                print("im here")
                raw_data = udpData[key][0].pop(0)
                res = udpData[key][1].pop(0)
                print("measure_1", res)
                print("measure_2", raw_data)

                fixed = delta_trace.fit(res, raw_data)
                udpData[key][1].append(np.array(fixed['packet']))
                sio.emit("new-packet-fix", fixed)

            # The first time a data arrived from key shelf
            elif len(udpData.get(key)[0]) > 1 and udpData.get(key)[2]:
                start_time = time()
                udpData.get(key)[2] = False
                print("start")
                measure_1 = udpData[key][0].pop(0)
                print("measure_1", measure_1)
                measure_2 = udpData[key][0].pop(0)
                print("measure_2", measure_2)
                fixed = delta_trace.fit(measure_1, measure_2)
                udpData[key][1].append(np.array(fixed['packet']))
                sio.emit("new-packet-fix", fixed)
                end = time()
                print("total= ", (end - start_time))

            if stop_thread is True:
                break


if __name__ == '__main__':
    t1 = threading.Thread(name='non-blocking',
                          target=delta_trace_execute,
                          args=())
    t1.start()
