#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 13 20:30:35 2023

@author: david
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Solution to the one-way tunnel
"""
import time
import random
from multiprocessing import Lock, Condition, Process
from multiprocessing import Value
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

#  Solucion con prioridad para los peatones

SOUTH = 1
NORTH = 0

NCARS = 100
NPED = 10
TIME_CARS_NORTH = 0.5  # a new car enters each 0.5s
TIME_CARS_SOUTH = 0.5  # a new car enters each 0.5s
TIME_PED = 5 # a new pedestrian enters each 5s
TIME_IN_BRIDGE_CARS = (1, 0.5) # normal 1s, 0.5s
TIME_IN_BRIDGE_PEDESTRIAN = (30, 10) # normal 1s, 0.5s

class Monitor():
    def __init__(self):
        self.mutex = Lock()
        self.patata = Value('i', 0)
        
        # Contador de los que esperan
        self.c_waiting_N = Value('i', 0)
        self.c_waiting_S = Value('i', 0)
        self.p_waiting   = Value('i', 0)
        
        # Contador de los que están dentro
        #  0 <= c_N <= 1
        #  0 <= c_S <= 1
        #  0 <=  p  <= K
        self.c_N         = Value('i', 0)
        self.c_S         = Value('i', 0)
        self.p           = Value('i', 0)
        
        # Condiciones
        # p >= 1 -> q = 0 para toda condicion de abajo
        self.c_dentro_N  = Condition(self.mutex)
        self.c_dentro_S  = Condition(self.mutex)
        self.p_dentro    = Condition(self.mutex)
        
        self.vacio       = Condition(self.mutex)
        self.no_peatones = Condition(self.mutex)
        self.no_coches   = Condition(self.mutex)

    #  c_waiting_N >= 1 and last_not_N -> bloquear_entrada
    #  c_waiting_S >= 1 and last_not_S -> bloquear_entrada
    #  p_waiting   >= 1 and last_not_P -> bloquear_entrada
    def last_not_N(self):
        return self.c_S.value >= 1 or self.p.value    >= 1
    
    def last_not_S(self):
        return self.c_N.value  >= 1 or self.p.value    >= 1

    def last_not_C(self):
        return self.c_S.value >= 1 or self.c_N.value >= 1

    def last_not_P(self):
        return self.c_N.value  >= 1 or self.c_S.value  >= 1 
    
    def puente_vacio_or_no_p(self):
        return self.puente_vacio or self.p == 0

    def puente_vacio_or_no_c(self):
        return self.puente_vacio or (self.c_N + self.c_S) == 0

    # nadie_dentro -> abrir_puente
    def puente_vacio(self):
        return self.c_N.value + self.c_S.value + self.p.value == 0
    
    def wants_enter_car(self, direction: int) -> None:
        self.mutex.acquire()
        self.patata.value += 1
        #### código
        if direction == 1:
            self.c_waiting_S.value += 1
        else:
            self.c_waiting_N.value += 1
        
        # aqui va la condicion de wait
        self.no_peatones.wait_for(self.puente_vacio_or_no_p)
        # aqui se ha cumplido -> estamos dentro de puente
        if direction == 1:
            self.c_waiting_S.value -= 1
            self.c_S.value         += 1
        else:
            self.c_waiting_N.value -= 1
            self.c_N.value         += 1
        self.mutex.release()

    def leaves_car(self, direction: int) -> None:
        self.mutex.acquire() 
        self.patata.value += 1
        #### código
        
        # aqui va el notify
        
        # Idea: primero avisamos a los peatones y luego a un coche.
        # Avisamos al coche para evitar situaciones en las que no quedan
        # Peatones entonces no puden entrar mas coches
        self.no_coches.notify_all()
        self.no_peatones.notify(1)
        
        # aqui termina el notify -> ha salido
        if direction == 1:
            self.c_S.value -= 1
        else:
            self.c_N.value -= 1
        
        self.mutex.release()

    def wants_enter_pedestrian(self) -> None:
        self.mutex.acquire()
        self.patata.value += 1
        #### código
        self.p_waiting.value += 1
        # aqui va la condicion de wait
        self.no_coches.wait_for(self.puente_vacio_or_no_c)
        # aqui se ha cumplido -> estamos dentro de puente
        self.p_waiting.value -= 1
        self.p.value  += 1
        self.mutex.release()

    def leaves_pedestrian(self) -> None:
        self.mutex.acquire()
        self.patata.value += 1

        # aqui va el notify

        self.no_peatones.notify(1)
        self.no_coches.notify_all()
        

        # aqui termina el notify -> ha salido
        self.p.value -= 1
        self.mutex.release()

    def __repr__(self) -> str:
        return f'Monitor: {self.patata.value}'

def delay_car_north() -> None:
    time.sleep(random.random()/6)

def delay_car_south() -> None:
    time.sleep(random.random()/6)

def delay_pedestrian() -> None:
    time.sleep(random.random()/2)

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