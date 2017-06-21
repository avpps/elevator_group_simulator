from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.utils import timezone
from django.db.models import Avg, Sum

import simpy
import random
import sqlite3

from simulator.models import Building, BuildingFloors, BuildingGroup
from simulator.models import SimulationDetails
from simulator.models import StatSimulation, StatPassengers, StatCars
from simulator.models import SimulationRunDetails
from simulator.models import CarRunDetails, SimulationSteps, BuildingTypes
from simulator.models import StatSimulationSummary
from simulator.models import Requirements


def simulationRun(request):


    def input_run():
        global buildingPopulation
        buildingPopulation = 0
        for i in building_floors:
            j = [
                i.local_id,
                i.name,
                i.interfloor,
                i.population,
                i.entry]
            floorChartList.append(j)
            buildingPopulation += i.population


    def floorGenerator(env):
        level = 0
        for i in building_floors:
            if i.local_id == 0:
                level = 0
            else:
                level += building_floors[i.local_id-1].interfloor
            floors_stat[i.local_id] = Floor(
                env,
                i.local_id,
                i.name,
                i.interfloor,
                level,
                i.population,
                i.entry)
            floors_list.append(i.local_id)
        for i, j in floors_stat.items():
            history.append(
                '%4d %5d %5d %4d %4d'
                % (i,
                  j.interfloor,
                  j.level,
                  j.population,
                  j.entry))


    def carGenerator(env):
        # create cars in cars_stat dictionary:
        for i in range(carsNumber):
            cars_stat[i] = Car(env, i)
        # create car monitoring at floors:
        for fi, floor in floors_stat.items():
            for ci in cars_stat:
                floor.carsAtFloor[ci] = CarAtFloor(env, fi, ci)
        # create car monitoring lists at floors:
        '''for fi, floor in floors_stat.items():
            floor.carAt()'''

        # activate car run process:
        for i in range(len(cars_stat)):        
            env.process(cars_stat[i].runCar(env))
               
            
    def passengersArrival(env):
        '''continue till generated passanger quantity reach declared
        passangers quantity which should appear in building in current step
        '''
        while len(passengers_stat) <= passengerAll:
            entryFloor = 0
            # passengers quantity in also random time period passengerActAt
            passengerActAr = abs(int(random.gauss(
                passengerAvgAr, 
                passengerAvgAr**0.5)))
            # append all new passengers to passengers database:
            for i in range(passengerActAr):
                j = len(passengers_stat)
                passengers_stat[j] = Passenger(
                    env,
                    j,
                    env.now,
                    entryFloor,
                    buildingFloorNumber)
                floors_stat[entryFloor].queue.append(j)
                history.append(
                    '%6d at %d appeared passenger %d LobbyQueue %d %s'
                    % (
                        env.now,
                        entryFloor,
                        j,
                        len(floors_stat[entryFloor].queue),
                        str(floors_stat[entryFloor].queue)))
            # passenger arrival time is also random:
            passengerActAt = abs(random.gauss(
                passengerAvgAt,
                passengerAvgAt**0.5))
            yield env.timeout(passengerActAt)
        history.append(
                    '%6d ---all passengers appeared---'
                    % (
                        env.now,))
        '''let know that till now simulation should wait with 
        end only for each passanger run process end
        '''
        processEnd_reactivate.succeed()


    def processEnd(env):
        #yield env.timeout(300)
        yield processEnd_reactivate
        for i in passengers_stat:
            yield passengers_stat[i].passengerRun_proc


    def reports_generator():

        history_file_name = 'history_files/run_history_{sim}_{step}'.format(
            sim=simulation_object.id,
            step=simulation_step.step)
        history_file = open('{s}.txt'.format(s=history_file_name), 'a')
        counter = 0
        for i in history:
            counter += 1
            history_file.write(
                '{:>6} {} {}'.format(
                    str(counter),
                    i,
                    '\n',))
        history_file.write('')
        
        for i, j in passengers_stat.items():
            WT = j.depTime - j.arrTime
            TTD = j.destTime - j.arrTime
            StatPassengers.objects.create(
                simulation=simulation_object,
                step=arrivalRate,
                                                                                    
                local_id=j.id,
                destFloor=round(j.destFloor, 2),
                arrTime=round(j.arrTime, 2),
                depTime=round(j.depTime, 2),
                destTime=round(j.destTime, 2),
                WT=round(WT, 2),
                TTD=round(TTD, 2),)
            
        for i, j in cars_stat.items():
            SINT = 0
            SCLF = 0
            for k in range(len(j.carDepartures)):
                if k != 0:
                    INT = j.carDepartures[k][0] - j.carDepartures[k-1][0]
                else:
                    INT = j.carDepartures[k][0]
                SINT += INT
                SCLF += j.carDepartures[k][1]
                CarRunDetails.objects.create(
                    simulation=simulation_object,
                    step=arrivalRate,
                    car=j.id,

                    local_id=j.id,
                    departure=round(j.carDepartures[k][0], 2),
                    INT=round(INT, 2),
                    load=j.carDepartures[k][1],)
            try:
                AINT = SINT/(len(j.carDepartures))
            except ZeroDivisionError:
                AINT = 0    
            try:
                ACLF = SCLF/(len(j.carDepartures))
            except ZeroDivisionError:
                ACLF = 0  
            StatCars.objects.create(
                simulation=simulation_object,
                step=arrivalRate,
                                    
                local_id=j.id,
                AINT = round(AINT, 2),
                ACLF = round(ACLF, 2),)


        AVGpassengers = StatPassengers.objects.filter(
            simulation=simulation_object).aggregate(Avg('WT'), Avg('TTD'))            
        AVGcars = StatCars.objects.filter(
            simulation=simulation_object).aggregate(Avg('AINT'), Avg('ACLF'))
        simulation_time = step_overall_end_time - step_overall_start_time
        
        StatSimulation.objects.create(
            simulation=simulation_object,
            step=arrivalRate,
                                      
            AINT = round(AVGcars['AINT__avg'], 2),
            AWT = round(AVGpassengers['WT__avg'], 2),
            ATTD = round(AVGpassengers['TTD__avg'], 2),
            ACLF = round(AVGcars['ACLF__avg'], 2),
            simulation_time = round(simulation_time, 6),
            )


    def reports_generator_summary():
        ''' module for create StatSimulationSummary object
        with reference to Requirements obj '''

        # take Requirements dedicated to certain building:
        building_type = simulation_object.building.b_type
        requirements_objects = Requirements.objects.filter(
            building_type=building_type).order_by('rating')

        # take all steps StatSimulation for certain simulation:
        steps_summary_objects = simulation_object.statsimulation_set.all(
            ).order_by('-step')
        # compare booth and save StatSimulationSummary object:
        ratings = {}
        for step in steps_summary_objects:
            stop = False
            for reqirement in requirements_objects:
                if (step.step >= reqirement.AR
                    and step.AWT <= reqirement.AWT
                    and step.ATTD <= reqirement.ATTD
                    and step.ACLF <= reqirement.ACLF):
                    ratings[step.step] = reqirement.rating
        if len(ratings) != 0:
            max_rating = max(([j for i, j in ratings.items()]))
            max_ratings_step_list = []
            for i, j in ratings.items():
                if j == max_rating:
                    max_ratings_step_list.append(i)

            max_rating_step = max(max_ratings_step_list)
            step = simulation_object.statsimulation_set.get(step=max_rating_step)
        else:
            max_rating = '?'
            step = steps_summary_objects[0]

        StatSimulationSummary.objects.create(
            simulation = simulation_object,
            rating = max_rating,
            AR = step.step,
            AWT = step.AWT,
            AINT = step.AINT,
            ATTD = step.ATTD,
            ACLF = step.ACLF,
            simulation_time = step.simulation_time,
            )


    def tests():
        def arrTimeCheck():
            iter_range = len(passengers_stat)
            dict = []
            for i in range(iter_range):
                if i < (iter_range-1):
                    if passengers_stat[i].depTime > passengers_stat[i+1].depTime:
                        passenger =  passengers_stat[i+1]
                        dict.append([
                            passenger.id,
                            passenger.depTime,
                            passenger.depTime-passenger.arrTime])
            if len(dict)==0:
                history.append('#######################')
                history.append('## arrTimeCheck pass ##')
                history.append('#######################')    
            else:
                history.append('#######################')
                history.append('## arrTimeCheck fail ##')
                for i in dict:
                    history.append(str(i))
                history.append('#######################')
        arrTimeCheck()


    class Floor():
        def __init__(self, env, id, name, interfloor, level, population, entry):
            self.env = env
            self.id = id
            self.name = name
            self.interfloor = interfloor
            self.level = level
            self.population = population
            self.entry = entry
            self.queue = []
            self.carsAtFloor = {}
            self.carList = []
            self.carAtList = []
            self.carArrivedList = []

        def carAt(self):
            for i, car in self.carsAtFloor.items():
                self.carList.append(i)
                self.carAtList.append(car.carAt_reactivate)
                self.carArrivedList.append(car.carArrived)


    class CarAtFloor():
        def __init__(self, env, floor_id, car_id):
            self.floor_id = floor_id
            self.car_id = car_id
            self.restart_events(env)
            self.carAt = False
            env.process(self.carAt_loop(env))
        def restart_events(self, env):
            self.carAt_reactivate = ''
            self.carOut_reactivate = ''
            self.carAt_reactivate = env.event()
            self.carOut_reactivate = env.event()
            self.carDisabled = env.process(self.carDisabled_letKnow(env))
        def carArrived_letKnow(self, env):
            yield self.carOut_reactivate
            yield self.carAt_reactivate
        def carDisabled_letKnow(self, env):
            yield self.carAt_reactivate
            yield self.carOut_reactivate
        def carAt_loop(self, env):
            while True:
                yield self.carAt_reactivate
                self.carArrived = env.process(self.carArrived_letKnow(env))
                self.carAt = True
                history.append(
                    '%6d car %d wait at %d'
                    % (
                        env.now,
                        self.car_id,
                        self.floor_id,))
                yield self.carOut_reactivate
                self.carAt = False
                history.append(
                    '%6d car %d not at %d'
                    % (
                        env.now,
                        self.car_id,
                        self.floor_id,))
                self.restart_events(env)


    class Passenger():
        # containing: ID, arr time, dep time, destTime
        def __init__(self, env, id, arrTime, entryFloor, buildingFloorNumber):
            self.env = env
            self.id = id
            self.arrTime = arrTime
            self.passengerUnloading_proc = env.process(
                self.passengerUnloading(env, self.id))
            self.passengerUnloading_reactivate = env.event()
            self.entryFloor = entryFloor
            self.destFloor = random.randrange(1, buildingFloorNumber, 1)
            self.passengerRun_proc = env.process(self.passengerRun(env, id))
            self.runEnd = False

        def depTime(time):
            self.depTime = time

        def destTime(time):
            self.destTime = time

        def passengerUnloading(self, env, passengerId):       
            yield self.passengerUnloading_reactivate
            yield env.timeout(0)
            passengers_stat[passengerId].destTime = env.now

        def passengerRun(self, env, passengerId):
            entryFloorObj = floors_stat[self.entryFloor]
            carList = [i for i in entryFloorObj.carsAtFloor]

            def carAtList_generator():
                return [car.carAt_reactivate for i, car in entryFloorObj.carsAtFloor.items()]
            def carArrivedList_generator():
                return [car.carArrived for i, car in entryFloorObj.carsAtFloor.items()]

            yield simpy.AnyOf(env, carAtList_generator())
            # wait and look if nobody were here before you:
            yield env.timeout(0.0001)
            while passengerId in entryFloorObj.queue:
                for car_id in carList:
                    allocatedCar = cars_stat[car_id]
                    # car have to be at floor 0 and not overfilled:
                    if (allocatedCar.carUsage.count < allocatedCar.carCapacity
                        and entryFloorObj.carsAtFloor[car_id].carAt):
                        history.append(
                            '%6d passenger %d try to entry car %d Doors are %s'
                            % (
                                env.now,
                                passengerId,
                                car_id,
                                allocatedCar.doorOpenedMonit.is_alive))
                        # passengers try entry car but in order of ascending id:
                        self.req = allocatedCar.carUsage.request(priority=self.id)
                        # passenger wait for entry or for car doors closing:
                        yield self.req | allocatedCar.doorOpenedMonit
                        history.append(
                            '%6d passenger %d waited to entry car %d with priority %d Doors are %s'
                            % (
                                env.now,
                                passengerId,
                                car_id,
                                self.id,
                                allocatedCar.doorOpenedMonit.is_alive))
                        # if not entry car:
                        if not self.req.triggered:
                            history.append(
                                '%6d passenger %d not leave queue and not entry car %d'
                                % (
                                    env.now,
                                    passengerId,
                                    car_id))
                            allocatedCar.carUsage.put_queue.remove(self.req)
                        else:
                            entryFloorObj.queue.pop(entryFloorObj.queue.index(passengerId))
                            allocatedCar.passengersInCar.append(passengerId)
                            allocatedCar.passengersInCarDest.append(self.destFloor)
                            passengers_stat[passengerId].depTime = env.now
                            history.append(
                                '%6d passenger %d leave queue and entry car %d LobbyQueue %s'
                                % (
                                    env.now,
                                    passengerId,
                                    car_id,
                                    str(entryFloorObj.queue)))
                            yield env.process(self.passengerUnloading(env, passengerId))
                            allocatedCar.carUsage.release(self.req)
                            self.runEnd = True
                            break
                    else:
                        pass
                if not self.runEnd:
                    history.append(
                        '%6d passenger %d wait for any car'
                        % (
                            env.now,
                            passengerId,))
                    yield simpy.AnyOf(env, carArrivedList_generator())


    class Car():
        def __init__(self, env, id):
            self.id = id

            self.speed = building_group.speed
            self.acceleration = building_group.acceleration
            self.jerk = building_group.jerk
            self.carCapacity = building_group.carCapacity
            self.passengerTransferTime = building_group.passengerTransferTime
            self.doorOpeningTime = building_group.doorOpeningTime
            self.doorClosingTime = building_group.doorClosingTime
            # car start running at floor_id=0
            self.carPosition = 0
            # so first destination is floor_id=0:
            self.destination_floor_id = 0
            # car up: (run direction = 1)  car down: (run direction = -1)
            # initial runDirection is up:
            self.runDirection = 1
            # floor where car will go when is empty:
            self.returnFloor = 0
            # car have capacity limit. This is limiter:
            self.carUsage = simpy.PriorityResource(env, capacity = self.carCapacity)
            #self.doorOpened = env.process(doorOpened(env))
            self.doorOpened_reactivate = env.event()
            
            # caches for simulation run:
            self.passengersInCar = []
            self.passengersInCarDest = []
            # cache for statistics:
            self.carDepartures = []
            # cache for movement beetween floors:
            self.carMovement = [[],[],[],[]]
            # avarage car load factor for in current simulation:
            self.avgClfValue = 0
            
        def avgClf(self):
            self.avgClfValue = sum(self.carDepartures)/len(self.carDepartures)

        def putting_inside(self, env, passengersInCar1):
            history.append(
                '%6d car %d passengers just inside %s'
                % (
                    env.now,
                    self.id,
                    list(self.just_inside)))
            for i in passengersInCar1:
                if i not in self.just_inside:
                    self.just_inside.append(i)
                    yield env.timeout(self.passengerTransferTime)
                    history.append(
                        '%6d passenger %d entry car %d'
                        % (
                            env.now,
                            i,
                            self.id))
                    '''recursion used because after each entry to car, other
                    passanger may appear in self.passengersInCar list
                    and this passenger should also be tried to put inside:
                    '''
                    yield env.process(self.putting_inside(
                        env,
                        self.passengersInCar,))
                    
        def doorOpened(self, env):
            '''if is_alive passengers are allowed to entry car.
            It is alive when
            '''
            yield self.doorOpened_reactivate
            yield env.timeout(0)

        def floors_list_mod_f(self):
            high = floors_list[(self.carPosition + 1):]
            low = floors_list[:self.carPosition]
            low.reverse()
            if self.runDirection == 1:
                return (high + low)
            if self.runDirection == -1:
                return (low + high)

        def motion(self, env, s_max, initial_car_distance, run_direction):

            '''all is based on actualization of below statements 
            in next steps with 'step_size' incrementation:
            s = s0 + v0*(t) + (1/2)*a0*(t**2) + (1/6)*j*(t**3)
            v = v0 + a0*(t) + (1/2)*j*(t**2)
            a = a0 + j*(t)
            j = j0
            '''

            start_time = env.now
            
            step_size = 0.01        # movement incrementation
            t = 0                   # base time
            t2 = 0                  # additional time start when deceleration start

            s0 = 0
            v0 = 0
            a0 = 0
            j0 = self.jerk          # jerk [m/s3]
            
            s = 0
            v = 0
            a = 0
            j = j0
            
            vmax = self.speed
            amax = self.acceleration
            amin = -self.acceleration

            dActS = 0               # deceleration activation distance (s) before planned stop
            sTillEnd = s_max        # distance to end of planned way
            

            while s < s_max:        # run till reached demanded distance 's_max'
                t += step_size      # update base time in each step
                
                if s < 0.5*s_max:           # first half of demanded distance
                    #history.append('przysp')
                    if a < amax and v < vmax:
                        #history.append('speed, accele, jerk', v, a, j, '  ', s)
                        s = s0 + v0*(t) + (1/2)*a0*(t**2) + (1/6)*j*(t**3)
                        s1 = s                                  # remember actual value to use it in next step if next "if" will be used
                        v = v0 + a0*(t) + (1/2)*j*(t**2)        
                        v1 = v                                  
                        a = a0 + j*(t)
                        s1t = s0 + v0*(t) + (1/2)*a*((t)**2)    # forecasted to be in next "if" 
                        v1t = v0 + a*((t))                      # forecasted to be in next "if"
                        dActS = s
                        sTillEnd = s_max - s
                    else:
                        if a >= amax and v < vmax:
                            #history.append('speed, accele', v, a, '  ', s)
                            j = 0
                            s = -s1t + s1 + s0 + v0*(t) + (1/2)*a*(t**2)   #     subtract forecasted value in previous step
                                                                           # and subtract value form previous step
                                                                           # and add actual value
                                                                           # it is for leveling new function run with previous                                                                  
                            s2 = s
                            v = -v1t + v1 + v0 + a*(t)
                            s2t = s0 + v*(t)
                            dActS = s
                            sTillEnd = s_max - s
                        else:
                            if (a >= amax or a == 0) and v >= vmax:
                                #history.append('speed', v, '  ', s)
                                j = 0
                                a = 0
                                s = -s2t + s2 + s0 + v*(t)
                                sTillEnd = s_max - s
                    sk = s                  # it is for leveling new function run with previous     
                    vk = v
                    ak = a
         
                else:                       # second half of demanded distance
                    if sTillEnd >= dActS:
                        s = -s2t + s2 + s0 + v*(t)
                        sTillEnd = s_max - s

                        sk = s              # it is for leveling new function run with previous     
                        vk = v
                        ak = a
                    else:
                        if t2 == 0:
                            a = 0
                        else:
                            pass
                        
                        t2 += step_size
                        j = -j0             # start to decelerate
                        v0 = vk             # state initial speed
                        
                        if v <= 0:
                            s = s_max
                            continue
                                           
                        if 0 >= a and a > amin:
                            s =  sk + s0 + v0*(t2) + (1/2)*a0*(t2**2) + (1/6)*j*(t2**3)
                            s1 = s
                            v = v0 + a0*(t2) + (1/2)*j*(t2**2)
                            v1 = v
                            a = a0 + j*(t2)
                            at = a
                            s1t = s0 + v0*(t2) + (1/2)*a*(t2**2)
                            v1t = v0 + a*(t2)
                            sTillEnd = s_max - s

                        else:
                            if a <= amin and v > 0:
                                j = 0
                                a = at
                                s = -s1t + s1 + s0 + v0*(t2) + (1/2)*a*(t2**2)
                                v = -v1t + v1 + v0 + a*(t2)
                                sTillEnd = s_max - s

                yield env.timeout(step_size)

                self.carMovement[0].append(start_time + t)
                self.carMovement[1].append(initial_car_distance + (run_direction * s))
                self.carMovement[2].append(v)
                self.carMovement[3].append(a)

        def runCar(self, env):
            history.append(
                '%6d car %d generated'
                %(
                    env.now,
                    self.id))
            while True:
                self.carWaiting = False
                self.carPosition = self.destination_floor_id
                self.carPosition_level = floors_stat[self.carPosition].level

                # unload car if anybody exit at this floor:
                if self.passengersInCar:
                    '''passengeer 'j' leave car but it take a time
                    ("reversed" to avoid pass and dest lists position 
                    changes. Thanks this, pass and dest are removed  
                    from right to left from list):
                    '''
                    for j in reversed(self.passengersInCar):                                            
                        if self.carPosition == passengers_stat[j].destFloor:
                            yield env.timeout(self.passengerTransferTime)
                            passengers_stat[j].passengerUnloading_reactivate.succeed()
                            wy = cars_stat[self.id].passengersInCar.index(j)
                            cars_stat[self.id].passengersInCar.pop(wy)
                            cars_stat[self.id].passengersInCarDest.pop(wy)
                            history.append(
                                '%6d car %d at landing %d Passenger %d leave car '
                                'Passengers in car %s Car destinations %s'
                                % (
                                    env.now,
                                    self.id,
                                    self.carPosition,
                                    passengers_stat[j].id,
                                    str(cars_stat[self.id].passengersInCar),
                                    str(self.passengersInCarDest)))

                # if anybody want's to etry car at this floor:
                # ... and that doors are opened:
                self.doorOpenedMonit = env.process(self.doorOpened(env))
                # let know at floor that car appeared:
                if floors_stat[self.carPosition].carsAtFloor[self.id].carAt == False:
                    floors_stat[self.carPosition].carsAtFloor[
                        self.id].carAt_reactivate.succeed()
                # now passengers try to entry floor (proceeded at Passenger instances)

                if not self.passengersInCar:
                    # ...if nobody is at car raturn to return floor:
                    if not self.carPosition == self.returnFloor:
                        self.destination_floor_id = self.returnFloor
                        history.append(
                            '%6d car %d go back'
                            % (
                                env.now,
                                self.id))
                    else:
                        self.carWaiting = True
                        yield env.timeout(1)
                else:
                    '''put passengers inside and during this process 
                    check if anybody else wants enter car:
                    '''
                    self.just_inside = []
                    yield env.process(
                        self.putting_inside(env, self.passengersInCar))
                    # check destination floor:
                    floors_list_mod = self.floors_list_mod_f()
                    for i in (floors_list_mod):
                        if i in self.passengersInCarDest:
                            self.destination_floor_id = i
                            if self.destination_floor_id < self.carPosition:
                                self.runDirection = -1
                            if self.destination_floor_id > self.carPosition:
                                self.runDirection = 1
                            break
                if not self.carWaiting:
                    # start closing doors and leave floor:
                    floors_stat[self.carPosition].carsAtFloor[
                        self.id].carOut_reactivate.succeed()
                    floors_stat[self.carPosition].carsAtFloor[
                        self.id].restart_events(env)
                    # activate door closing:
                    self.doorOpened_reactivate.succeed()
                    # restart doorOpened as env.event with is_alive=?
                    self.doorOpened_reactivate = env.event()
                    history.append(
                        '%6d car %d at floor %d Doors start closing '
                        'Passengers in car %s Car destinations %s'
                        % (
                            env.now,
                            self.id,
                            self.carPosition,
                            str(self.passengersInCar),
                            str(self.passengersInCarDest)))
                    yield env.timeout(self.doorClosingTime)
                    self.carDepartures.append(
                        [env.now, len(self.passengersInCar)])
                    self.destination_floor_level = floors_stat[
                        self.destination_floor_id].level
                    self.runDistance = abs(
                        self.carPosition_level
                        - self.destination_floor_level)
                    history.append(
                        '%6d car %d leave floor %d next stop at %s run distance: %d'
                        % (
                            env.now,
                            self.id,
                            self.carPosition,
                            self.destination_floor_id,
                            self.runDistance,))
                    yield env.process(self.motion(
                        env,
                        self.runDistance,
                        self.carPosition_level,
                        self.runDirection))


    '''refering to certain (!last added!) simulation object:'''
    simulationslist = SimulationDetails.objects.order_by('id')
    simulation_position_on_list = len(simulationslist)-1
    simulation_id = simulationslist[simulation_position_on_list].id
    simulation_object = get_object_or_404(SimulationDetails, pk=simulation_id)

    '''refering to certain simulationsteps list:'''
    simulationstepslist = simulation_object.simulationsteps_set.all().order_by('id')

    '''refering to certain building:'''
    building_id = simulation_object.building.id
    building_object = simulation_object.building

    '''refering to certain building floors:'''
    building_floors = BuildingFloors.objects.filter(building=building_id)

    '''refering to certain building elevator group:'''
    building_group = BuildingGroup.objects.get(building=building_id)


    ''''import seed value:'''
    random.seed(simulation_object.randomSeed)

    '''create floorChartList:'''
    floorChartList = []
    input_run()

    buildingFloorNumber = len(floorChartList)
    carsNumber = building_group.carsNumber
    
    # summary passengers arrival time in simulation [sek]
    passengersArrivalTime = simulation_object.passengersArrivalTime
    # buildingPopulation defined in input_run()


    '''________________________________'''
    '''main loop for serial simulation:'''
    from time import clock
    for simulation_step in simulationstepslist:
        step_overall_start_time = clock()
        passengers_stat = {}    # local passengers database dict
        cars_stat = {}          # local cars database dict
        floors_stat = {}        # local floors database dict
        floors_list = [] 
        history = []
        lobbyQueue = []         # actual passengers at lobby
        # [%] value of building population appeared in lobbies per 5 min
        arrivalRate = simulation_step.step
        '''Declare passangers quantity which will appear in building in current step:
        previously declared passengersArrivalTime determine how much people appeard
        with assumption that they appear every 5[min] in
        quantity=(buildingPopulation*arrivalRate/100).
        Expression (passengersArrivalTime/300) determine number of 5 minutes periods
        in current step -> 5[min]=300[s]'''
        passengerAll = int((passengersArrivalTime/300)*(buildingPopulation*arrivalRate/100))
        '''It is parameter for random.gauss function.
        Declare how much passenger will in avg appeared at lobbies at the 
        same time. Naturally only one passangeer''' 
        passengerAvgAr = 1
        ''' ... the same with avg appearance cadency in 5 [min] '''
        passengerAvgAt = 300 / (buildingPopulation*(arrivalRate/100))

        # activate Simpy env:
        env = simpy.Environment()
        # put floors into env:
        floorGenerator(env)
        # put cars into env:
        carGenerator(env)
        env.process(passengersArrival(env))
        processEnd_proc = env.process(processEnd(env))
        processEnd_reactivate = env.event()
        env.run(until=processEnd_proc)
        step_overall_end_time = clock()
        step_additional_start_time = clock()    #### for tests
        tests()
        reports_generator()
        step_additional_end_time = clock()      #### for tests
        #### for tests:
        print('----------------', simulation_step.step, 'step time:', step_overall_end_time-step_overall_start_time)
        print('---', simulation_step.step, 'reports and tests time:', '-------------', step_additional_end_time-step_additional_start_time)  
        ####
        
        
    reports_generator_summary()

    return HttpResponseRedirect(reverse('simulator:index'))