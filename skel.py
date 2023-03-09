"""
Solution to the one-way tunnel
"""
import time
import random
from multiprocessing import Lock, Condition, Process
from multiprocessing import Value

SOUTH = 1
NORTH = 0

NCARS = 100
NPED = 10
TIME_CARS = 0.5  # a new car enters each 0.5s
TIME_PED = 5 # a new pedestrian enters each 5s
TIME_IN_BRIDGE_CARS = (1, 0.5) # normal 1s, 0.5s
TIME_IN_BRIDGE_PEDESTRGIAN = (30, 10) # normal 1s, 0.5s

class Monitor():
    def __init__(self):
        self.mutex = Lock()


    def wants_enter_car(self, direction):
        self.mutex.acquire()
        #### código
        self.mutex.release()

    def leaves_car(self, direction):
        self.mutex.acquire()
        #### código
        self.mutex.release()

    def wants_enter_pedestrian(self):
        self.mutex.acquire()
        #### código
        self.mutex.release()

    def leaves_pedestrian(self):
        self.mutex.acquire()
        #### código
        self.mutex.release()

def delay_car_north():
    pass

def delay_car_south():
    pass

def delay_pedestrian():
    pass

def car(cid, direction, monitor):
    print(f"car {cid} heading {direction} wants to enter")
    monitor.wants_enter_car(direction)
    print(f"car {cid} heading {direction} enters the bridge")
    if direction==NORTH :
        delay_car_north()
    else:
        delay_car_south()
    print(f"car {cid} heading {direction} leaving the bridge")
    monitor.leaves_car(direction)
    print(f"car {cid} heading {direction} out of the bridge")

def pedestrian(pid, monitor):
    print(f"pedestrian {pid} wants to enter")
    monitor.wants_enter_pedestrian()
    print(f"pedestrian {pid} enters the bridge")
    delay_pedestrian()
    print(f"pedestrian {pid} leaving the bridge")
    monitor.leaves_pedestrian()
    print(f"pedestrian {pid} out of the bridge")



def gen_pedestrian(monitor):
    pid = 0
    plst = []
    for _ in range(NPED):
        pid += 1
        p = Process(target=pedestrian, args=(pid, monitor))
        p.start()
        plst.append(p)
        time.sleep(random.expovariate(1/TIME_PED))

    for p in plst:
        p.join()

def gen_cars(monitor):
    cid = 0
    plst = []
    for _ in range(NCARS):
        direction = NORTH if random.randint(0,1)==1  else SOUTH
        cid += 1
        p = Process(target=car, args=(cid, direction, monitor))
        p.start()
        plst.append(p)
        time.sleep(random.expovariate(1/TIME_CARS))

    for p in plst:
        p.join()

def main():
    monitor = Monitor()
    gcars = Process(target=gen_cars, args=(monitor,))
    gped = Process(target=gen_pedestrian, args=(monitor,))
    gcars.start()
    gped.start()
    gcars.join()
    gped.join()


if __name__ == '__main__':
    main()
