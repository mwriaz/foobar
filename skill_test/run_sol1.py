import os
import time
import threading
import argparse
import sys
import json
from types import ModuleType

class Alarm(threading.Thread):
    def __init__(self, timeout):
        threading.Thread.__init__(self)
        self.timeout = timeout
        self.setDaemon(True)
    def run(self):
        time.sleep(self.timeout)
        os._exit (1)


parser = argparse.ArgumentParser()
parser.add_argument('--solution', type=str)
parser.add_argument('--input', type=str)

arg = parser.parse_args()
solution = arg.solution
try:
    input_value = json.loads(json.loads(arg.input))
except:
    try:
        input_value = json.loads(arg.input)
    except:
        arg.input

mod = ModuleType('my_module', 'doc string here')
sys.modules['my_module'] = mod

try:
    exec(solution, mod.__dict__)
    sys.modules['my_module'] = mod
except Exception as e:
    valid_to_submit_flag = False
    exec("def solution():\n    return n", mod.__dict__)
    
alarm = Alarm(2)
alarm.start()
try:
    print(json.dumps(mod.solution(input_value)))
except:
    print(json.dumps("Error"))
del alarm
