"""
Solution to the one-way tunnel
"""
import time
import random
from multiprocessing import Lock, Condition, Process
from multiprocessing import Value, Array

SOUTH = 1
NORTH = 0

NCARS = 100
NPED = 10
TIME_CARS = 0.5  # a new car enters each 0.5s
TIME_PED = 5 # a new pedestrian enters each 5s
TIME_IN_BRIDGE_CARS = (1, 0.5) # normal 1s, 0.5s
TIME_IN_BRIDGE_PEDESTRGIAN = (30, 10) # normal 1s, 0.5s

"""
IDEAS:
basico:
    garantizar que solo puede haber un elemento en el puente a la vez
    y que funcione fluido
extension_1:
    anadir prioridad a los que estan esperando en el mismo sentido que ha 
    entrado el ultimo
extension_2:
    anadir una capacidad [c_s,c_p] para el puente de manera que no pueda 
    producirse muchas entradas simultaneas
extension_3:
    ticket para que haya un delay por los que vienen de cada sentido si van
    del mismo, de manera que evitas entrada simultanea
extension_4: 
    posibilidad de cerrar la entrada por contador
"""

# anadir ticket como delay aleatorio para el que entren varios seguidos

class Monitor():
    def __init__(self):
        self.mutex = Lock()
        self.personas = Value('i', 0)
        self.l_coches = Array('i',2)
        # self.lock_dentro = Lock()

    def wants_enter_car(self, direction: int) -> None:
        self.mutex.acquire()
        self.l_coches[direction] += 1
        #### código
        self.mutex.release()

    def leaves_car(self, direction: int) -> None:
        self.mutex.acquire() 
        self.l_coches[direction] -= 1
        #### código
        # self.lock_dentro.release()
        self.mutex.release()

    def wants_enter_pedestrian(self) -> None:
        self.mutex.acquire()
        self.personas.value += 1
        #### código
        self.mutex.release()
    
    # def is_inside(self) -> None:
    #     self.mutex.acquire()
    #     self.lock_dentro.acquire()
    #     self.mutex.release()

    def leaves_pedestrian(self) -> None:
        self.mutex.acquire()
        self.personas.value  -= 1
        #### código
        # self.lock_dentro.release()
        self.mutex.release()

    def __repr__(self) -> str:
        return f'Monitor: {self.personas.value}'

def delay_car_north() -> None:
    time.sleep(random.random())

def delay_car_south() -> None:
    time.sleep(random.random())


def delay_pedestrian() -> None:
    time.sleep(random.random())


def car(cid: int, direction: int, monitor: Monitor)  -> None:
    print(f"car {cid} heading {direction} wants to enter. {monitor}")
    monitor.wants_enter_car(direction)
    
    # Garantizar exclusion mutua de esto
    # monitor.is_inside()
    print(f"car {cid} heading {direction} enters the bridge. {monitor}")
    if direction==NORTH :
        delay_car_north()
    else:
        delay_car_south()
    print(f"car {cid} heading {direction} leaving the bridge. {monitor}")
    monitor.leaves_car(direction)

    print(f"car {cid} heading {direction} out of the bridge. {monitor}")

def pedestrian(pid: int, monitor: Monitor) -> None:
    print(f"pedestrian {pid} wants to enter. {monitor}")
    monitor.wants_enter_pedestrian()
    # Garantizar exclusion mutua de esto
    # monitor.is_inside()
    print(f"pedestrian {pid} enters the bridge. {monitor}")
    delay_pedestrian()
    print(f"pedestrian {pid} leaving the bridge. {monitor}")
    monitor.leaves_pedestrian()
    print(f"pedestrian {pid} out of the bridge. {monitor}")



def gen_pedestrian(monitor: Monitor) -> None:
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

def gen_cars(monitor: Monitor) -> None:
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
