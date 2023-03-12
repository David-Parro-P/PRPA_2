"""
Solution to the one-way tunnel
"""
import time
import random
from time import sleep
from multiprocessing import Lock, Condition, Process
from multiprocessing import Value, Array

SOUTH = 1
NORTH = 0

NCARS = 10
NPED = 2
TIME_CARS_NORTH = 0.5  # a new car enters each 0.5s
TIME_CARS_SOUTH = 0.5  # a new car enters each 0.5s
TIME_PED = 5 # a new pedestrian enters each 5s
TIME_IN_BRIDGE_CARS = (1, 0.5) # normal 1s, 0.5s
TIME_IN_BRIDGE_PEDESTRGIAN = (30, 10) # normal 1s, 0.5s
SIZE_BRIDGE = 3

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
        self.patata = Value('i', 0)
        self.w_carriles_c = Array('i', 2)
        self.coches = Value('i',0)
        self.n_peatones_dentro    = Value('i',0)
        self.n_peatones_waiting   = Value('i', 0)
        # Luego hay que extender a array para aumentar capacidad puente
        # North = 0 ; South = 1 ; Peaton = 2; Empty = -2
        self.dir_dentro           = Value('i',0)
        # Dos punteros para hacer que puente tenga estructura de cola
        # Usando una lista cirular
        self.posicion_dentro      = Value('i',0)
        self.toca_salir           = Value ('i',0)
        # Puente de capacidad 3 para ambos, peatones y coches
        # No puede haber coches en dos direcciones distintas
        self.puente               = Array('i', 3)
        for i in range(SIZE_BRIDGE):
            self.puente[i] = -2
        self.no_coches = Condition(self.mutex)
        self.vacio     = Condition(self.mutex)
        # Testing_condiciones
        self.vienen_north    = Condition(self.mutex)
        self.vienen_south    = Condition(self.mutex)
        self.vienen_peatones = Condition(self.mutex)
    """
    queremos algo del tipo
    
    direction 1 -> wait_for(vienen_south)
    direction 0 -> wait_for(vienen_north)
    peaton      -> waith_for_vienen(peatones)
    pero queremos un punto en el que puedan entrar de manera aleateria,
    si el anterior es -2 (no queda nadie en el puente)
    queremos garantizar que pueda entrar cualquiera de los 3 (solo 1 !)
    de forma no determinista.
    """
    def esta_vacio(self):
        return self.coches.value == 0 and \
        self.n_peatones_waiting.value == 0

    # Los dejo como dos diferentes por si tengo que hacer uso de ellos 
    # Como predicados en el futuro
    def anterior_south(self):
        return self.coches.value <= SIZE_BRIDGE and self.toca_salir.value == 1
    
    def anterior_north(self):
        return self.coches.value <= SIZE_BRIDGE and self.toca_salir.value == 0

    def wants_enter_car(self, direction: int) -> None:
        self.mutex.acquire()
        self.patata.value += 1
        #### código
        self.w_carriles_c[direction] += 1
        self.vacio.wait_for(self.esta_vacio)
        self.w_carriles_c[direction] -= 1
        self.coches.value += 1
        if direction == 1 and self.anterior_south():
            self.puente[self.posicion_dentro.value] = 1
            self.posicion_dentro.value = (self.posicion_dentro.value + 1) \
            % SIZE_BRIDGE

        elif self.anterior_north():
            self.puente[self.posicion_dentro.value] = 0
            self.posicion_dentro.value = (self.posicion_dentro.value + 1) \
            % SIZE_BRIDGE

        self.mutex.release()

    def leaves_car(self, direction: int) -> None:
        self.mutex.acquire() 
        self.patata.value += 1
        self.coches.value -=1
        self.puente[self.toca_salir.value] = -2
        self.toca_salir.value = (self.toca_salir.value + 1) \
        % SIZE_BRIDGE
        self.vacio.notify()
        self.no_coches.notify_all()
        #### código
        self.mutex.release()

    def are_no_cars(self):
        return self.coches.value == 0
    
    def wants_enter_pedestrian(self) -> None:
        self.mutex.acquire()
        self.patata.value += 1
        self.n_peatones_waiting.value += 1
        #### código
        self.no_coches.wait_for(self.are_no_cars)
        self.n_peatones_dentro.value  += 1
        self.n_peatones_waiting.value -= 1
        
        self.mutex.release()

    def anterior_pedestrian(self):
        return self.n_peatones_dentro.value <= SIZE_BRIDGE and \
        self.toca_salir.value == 0

    def leaves_pedestrian(self) -> None:
        self.mutex.acquire()
        self.patata.value += 1
        if self.anterior_pedestrian():
            self.puente[self.posicion_dentro.value] = 2
            self.posicion_dentro.value = (self.posicion_dentro.value + 1) \
            % SIZE_BRIDGE
        self.puente[self.toca_salir.value] = -2
        self.toca_salir.value = (self.toca_salir.value + 1) \
        % SIZE_BRIDGE
        #### código
        if self.n_peatones_waiting == 0:
            self.vacio.notify()
        self.mutex.release()

    def __repr__(self) -> str:
        return f'Monitor: {self.patata.value}'

def delay_car_north() -> None:
    sleep(random.random())

def delay_car_south() -> None:
    sleep(random.random())

def delay_pedestrian() -> None:
    sleep(2*random.random())

def car(cid: int, direction: int, monitor: Monitor)  -> None:
    print(f"car {cid} heading {direction} wants to enter. {monitor}")
    monitor.wants_enter_car(direction)
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

def gen_cars(direction: int, time_cars, monitor: Monitor) -> None:
    cid = 0
    plst = []
    for _ in range(NCARS):
        cid += 1
        p = Process(target=car, args=(cid, direction, monitor))
        p.start()
        plst.append(p)
        time.sleep(random.expovariate(1/time_cars))

    for p in plst:
        p.join()

def main():
    monitor = Monitor()
    gcars_north = Process(target=gen_cars, args=(NORTH, TIME_CARS_NORTH, monitor))
    gcars_south = Process(target=gen_cars, args=(SOUTH, TIME_CARS_SOUTH, monitor))
    gped = Process(target=gen_pedestrian, args=(monitor,))
    gcars_north.start()
    gcars_south.start()
    gped.start()
    gcars_north.join()
    gcars_south.join()
    gped.join()


if __name__ == '__main__':
    main()