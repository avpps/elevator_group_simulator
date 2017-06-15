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


    def input_run(env):
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

            floors_stat[i.local_id] = Floor(
                env,
                i.local_id,
                i.name,
                i.interfloor,
                i.population,
                i.entry)


    def carGenerator(env):
        # create cars in cars_stat dictionary:
        for i in range(carsNumber):
            cars_stat[i] = Car(env, i)
        # activate car run process:
        for i in range(len(cars_stat)):        
            env.process(cars_stat[i].runCar(env))
        for i, j in floors_stat.items():
            for k, l in cars_stat.items():
                floors_stat[i].carsAtFloor[k] = floors_stat[i].carAtFloor(env)
                cars_stat[k].carAtFloors[i] = cars_stat[k].carAtFloor(env, i)
                
                
    def passengersArrival(env):
        '''continue till generated passanger quantity reach declared
        passangers quantity which should appear in building in current step
        '''
        while len(passengers_stat) <= passengerAll:
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
                    buildingFloorNumber)
                lobbyQueue.append(j)
                history.append(
                    '%d appeared passenger %d LobbyQueueLen %d %s'
                    % (
                        env.now,
                        j,
                        len(lobbyQueue),
                        str(lobbyQueue)))
            # passenger arrival time is also random:
            passengerActAt = abs(random.gauss(
                passengerAvgAt,
                passengerAvgAt**0.5))
            yield env.timeout(passengerActAt)
        history.append(
                    '%d ---all passengers appeared--- LobbyQueueLen %d'
                    % (
                        env.now,
                        len(lobbyQueue)))
        '''let know that till now simulation should wait with 
        end only for each passanger run process end
        '''
        processEnd_reactivate.succeed()


    def processEnd(env):
        yield processEnd_reactivate
        for i in passengers_stat:
            yield passengers_stat[i].passengerRun_proc


    def reports_generator():
        history_file_name = 'history_files/run_history_{sim}_{step}'.format(
            sim=simulation_object.id,
            step=simulation_step.step)
        '''stat_db_name = 'stat_db_{rn}'.format(rn=revision_no)
        stat_db_run.create_tables(stat_db_name)''' 
        history_file = open('{s}.txt'.format(s=history_file_name), 'a')
        for i in history:
            history_file.write(i)
            history_file.write('\n')
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

        
        StatSimulation.objects.create(
            simulation=simulation_object,
            step=arrivalRate,
                                      
            AINT=round(AVGcars['AINT__avg'], 2),
            AWT=round(AVGpassengers['WT__avg'], 2),
            ATTD=round(AVGpassengers['TTD__avg'], 2),
            ACLF=round(AVGcars['ACLF__avg'], 2),
        )


    def reports_generator_summary():
        ''' module for create StatSimulationSummary object
        with reference to Requirements obj '''

        # take Requirements dedicated to certain building:
        building_type = simulation_object.building.b_type
        requirements_objects = Requirements.objects.filter(
            building_type=building_type).order_by('-rating')

        # take all steps StatSimulation for certain simulation:
        steps_summary_objects = simulation_object.statsimulation_set.all(
            ).order_by('-step')
        # compare booth and save StatSimulationSummary object:
        for step in steps_summary_objects:
            stop = False
            for reqirement in requirements_objects:
                if (step.step >= reqirement.AR
                    and step.AWT <= reqirement.AWT
                    and step.ATTD <= reqirement.ATTD
                    and step.ACLF <= reqirement.ACLF):
                    StatSimulationSummary.objects.create(
                        simulation = simulation_object,
                        rating = reqirement.rating,
                        AR = step.step,
                        AWT = step.AWT,
                        AINT = step.AINT,
                        ATTD = step.ATTD,
                        ACLF = step.ACLF,
                    )
                    stop = True
                    break
                else:
                    continue
            if stop:
                break


    class Floor():
        def __init__(self, env, id, name, interfloor, population, entry):
            self.env = env
            self.id = id
            self.name = name
            self.interfloor = interfloor
            self.population = population
            self.entry = entry
            self.queue = []
            self.carsAtFloor = {}
        
        class carAtFloor(self, env):
            def carAt(self, env):
                yield self.carAt_reactivate
                yield env.timeout(0)


    class Passenger():
        # containing: ID, arr time, dep time, destTime
        def __init__(self, env, id, arrTime, buildingFloorNumber):
            self.env = env
            self.id = id
            self.arrTime = arrTime
            self.passengerUnloading_proc = env.process(
                self.passengerUnloading(env, self.id))
            self.passengerUnloading_reactivate = env.event()
            self.destFloor = random.randrange(1, buildingFloorNumber, 1)
            self.passengerRun_proc = env.process(self.passengerRun(env, id))

        def depTime(time):
            self.depTime = time

        def destTime(time):
            self.destTime = time

        def passengerUnloading(self, env, passengerId):       
            yield self.passengerUnloading_reactivate
            yield env.timeout(0)
            passengers_stat[passengerId].destTime = env.now

        def passengerRun(self, env, passengerId):
            while passengerId in lobbyQueue:
                carList = []
                for car in cars_stat:
                    carList.append(car.carAtFloors[0])
                yield simpy.AnyOf(env, carList) # probably wrong syntax: https://simpy.readthedocs.io/en/latest/topical_guides/events.html#waiting-for-multiple-events-at-once
                # below few lines for revision because of yield-based waiting for car method
                #yield env.timeout(0.01)
                for allocatedCar in range(carsNumber):
                    yield env.timeout(0.0001)
                    # car have to be on floor 0 and not overfilled:
                    if (cars_stat[allocatedCar].carPosition == 0 
                        and cars_stat[allocatedCar].carUsage.count < cars_stat[allocatedCar].carCapacity):
                        history.append(
                            '%d passenger %d try to entry car %d Doors are %s'
                            % (
                                env.now,
                                passengerId,
                                allocatedCar,
                                cars_stat[allocatedCar].doorOpenedMonit.is_alive))
                        # passengers try entry car but in order of ascending id:
                        self.req = cars_stat[allocatedCar].carUsage.request(priority=self.id)
                        # passenger wait for entry or for car doors closing:
                        yield self.req | cars_stat[allocatedCar].doorOpenedMonit
                        history.append(
                            '%d passenger %d waited to entry car %d with priority %d Doors are %s'
                            % (
                                env.now,
                                passengerId,
                                allocatedCar,
                                self.id,
                                cars_stat[allocatedCar].doorOpenedMonit.is_alive))
                        # if not entry car:
                        if not self.req.triggered:
                            history.append(
                                '%d passenger %d not leave queue and not entry car %d'
                                % (
                                    env.now,
                                    passengerId,
                                    allocatedCar))
                            cars_stat[allocatedCar].carUsage.put_queue.remove(self.req)
                        else:
                            lobbyQueue.pop(lobbyQueue.index(passengerId))
                            cars_stat[allocatedCar].passengersInCar.append(passengerId)
                            cars_stat[allocatedCar].passengersInCarDest.append(self.destFloor)
                            passengers_stat[passengerId].depTime = env.now
                            history.append(
                                '%d passenger %d leave queue and entry car %d LobbyQueue %s'
                                % (
                                    env.now,
                                    passengerId,
                                    allocatedCar,
                                    str(lobbyQueue)))
                            yield env.process(self.passengerUnloading(env, passengerId))
                            cars_stat[allocatedCar].carUsage.release(self.req)
                            break
                    else:
                        continue


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
            # absolute car position counted from floor_id=0 level
            self.carPositionDist = 0
            # 
            self.carPositionDistSum = 0
            # car have capacity limit. This is limiter:
            self.carUsage = simpy.PriorityResource(env, capacity = self.carCapacity)
            #self.doorOpened = env.process(doorOpened(env))
            self.doorOpened_reactivate = env.event()
            
            # caches for simulation run:
            self.passengersInCar = []
            self.passengersInCarDest = []
            # cache for statistics:
            self.carDepartures = []
            ''''''
            self.carMovement = [[],[],[],[]]
            self.avgClfValue = 0
            self.carAtFloors = {}
            
        class carAtFloor(self, env, floor_id):
            def isAt(env, floor_id):
                self.carAtFloor = env.process(floors_stat[floor_id].carsAtFloor)
            def isNotAt(env, floor_id):
                pass #for make up
                
                
            
        def avgClf(self):
            sClf = 0
            T = 0
            for i in self.carDepartures:
                T += 1
                sClf += i[1]
            self.avgClfValue = sClf/T

        def putting_inside(self, env, passengersInCar1):
            history.append(
                '%d car %d passengers just inside %s'
                % (
                    env.now,
                    self.id,
                    list(self.just_inside)))
            for i in passengersInCar1:
                if i not in self.just_inside:
                    self.just_inside.append(i)
                    yield env.timeout(self.passengerTransferTime)
                    history.append(
                        '%d       1 sec for pass transfer'
                        % (
                            env.now))
                    '''recursion used because after each entry to car, other
                    passanger may appear in self.passengersInCar list
                    and this passenger should also be tried to put inside:
                    '''
                    yield env.process(self.putting_inside(
                        env,
                        self.passengersInCar))
                    
        def doorOpened(self, env):
            '''if is_alive passengers are allowed to entry car.
            It is alive when
            '''
            yield self.doorOpened_reactivate
            yield env.timeout(0)

        def runCar(self, env):
            history.append(
                '%d car %d generated'
                %(
                    env.now,
                    self.id))
            while True:
                # car start at floor_id=0:
                self.carPosition = 0
                self.carPositionDist = 0
                self.carPositionDistSum = 0
                '''car movement is ralised as jumps beetween next floors
                jump distance is just this:
                '''
                carPositionDistSumForInterfloorRun = 0
                self.doorOpenedMonit = env.process(self.doorOpened(env))
                
                if len(lobbyQueue) > 0:
                    history.append(
                        '%d car %d at floor %d Doors are %s'
                        % (
                            env.now,
                            self.id,
                            self.carPosition,
                            self.doorOpenedMonit.is_alive))
                yield env.timeout(self.doorOpeningTime)
                if len(self.passengersInCar) > 0:
                    '''after loading make additional procedures 
                    (photocell delays, door close, etc...):
                    '''
                    self.just_inside = []
                    yield env.process(
                        self.putting_inside(env, self.passengersInCar))
                    '''----for verification:----'''
                    self.carPosition = 0.5
                    history.append(
                        '%d car %d at floor %d Doors start closing '
                        'Passengers in car %s Car destinations %s'
                        % (
                            env.now,
                            self.id,
                            self.carPosition,
                            str(self.passengersInCar),
                            str(self.passengersInCarDest)))
                    # activate door closing:
                    self.doorOpened_reactivate.succeed()
                    # restart doorOpened as env.event with is_alive=?
                    self.doorOpened_reactivate = env.event()
                    yield env.timeout(self.doorClosingTime)
                    self.carDepartures.append([env.now, len(self.passengersInCar)])
                    history.append(
                        '%d car %d leave floor 0 Doors are %s'
                        % (
                            env.now,
                            self.id,
                            self.doorOpenedMonit.is_alive))
                    # additional time for acceleration:
                    yield env.timeout(0)
                    ''''buildingFloorNumber+1' to be sure that below 
                    'if' statement will be checked also on top floor:
                    '''
                    for i in range(1, buildingFloorNumber+1):    
                        if len(self.passengersInCar) > 0:
                            # run for next floor, but it take a time:
                            self.carPosition = i-0.5
                            self.carPositionDist += floorChartList[i][2]
                            self.carPositionDistSum += floorChartList[i][2]
                            if i in self.passengersInCarDest:
                                yield env.process(
                                    self.motion(
                                        env,
                                        self.carPositionDist,
                                        carPositionDistSumForInterfloorRun,
                                        1))
                                self.carPosition = i
                                self.carPositionDist = 0
                            else:
                                history.append(
                                    '%d car %d at landing %d '
                                    'Nobody leave car'
                                    % (
                                        env.now,
                                        self.id, 
                                        i))
                                continue
                        else:
                            # when car is empty, go back to floor 0:
                            history.append(
                                '%d car %d go back'
                                % (
                                    env.now,
                                    self.id))
                            self.carPosition = 0.5
                            yield env.process(
                                self.motion(
                                    env,
                                    self.carPositionDistSum,
                                    self.carPositionDistSum,
                                    -1))
                            break
                        carPositionDistSumForInterfloorRun = self.carPositionDistSum
                        '''passengeer 'j' leave car but it take a time
                        (reversed to avoid pass and dest lists position 
                        changes. Thanks this, pass and dest are removed  
                        from right to left from list):
                        '''
                        for j in reversed(self.passengersInCar):                                            
                            if i == passengers_stat[j].destFloor:
                                yield env.timeout(self.passengerTransferTime)
                                passengers_stat[j].passengerUnloading_reactivate.succeed()
                                # probably not needed (above end passanger run process):
                                passengers_stat[j].passengerUnloading_reactivate = env.event()
                                self.wy = cars_stat[self.id].passengersInCar.index(j)
                                cars_stat[self.id].passengersInCar.pop(self.wy)
                                cars_stat[self.id].passengersInCarDest.pop(self.wy)
                                history.append(
                                    '%d car %d at landing %d Passenger %d leave car '
                                    'Passengers in car %s Car destinations %s'
                                    % (
                                        env.now,
                                        self.id,
                                        i,
                                        passengers_stat[j].id,
                                        str(cars_stat[self.id].passengersInCar),
                                        str(self.passengersInCarDest)))
                        '''after unloading make additional procedures 
                        (photocell delays, door close, etc...):
                        '''
                        yield env.timeout(1)

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
                    #print('przysp')
                    if a < amax and v < vmax:
                        #print('speed, accele, jerk', v, a, j, '  ', s)
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
                            #print('speed, accele', v, a, '  ', s)
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
                                #print('speed', v, '  ', s)
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
    for simulation_step in simulationstepslist:
        passengers_stat = {}    # local passengers database dict
        cars_stat = {}          # local cars database dict
        floors_stat = {}        # local floors database dict
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
        # put cars into env:
        carGenerator(env)
        env.process(passengersArrival(env))
        processEnd_proc = env.process(processEnd(env))
        processEnd_reactivate = env.event()
        env.run(until=processEnd_proc)


        reports_generator()
        
    reports_generator_summary()

    return HttpResponseRedirect(reverse('simulator:index'))

    '''
    #refering to certain simulation:
    simulationslist = SimulationDetails.objects.order_by('id')
    simulation_id = len(simulationslist)
    simulation_object = get_object_or_404(SimulationDetails, pk=simulation_id)
    simulation_arr = simulation_object.passengersArrivalTime

    #refering to certain building:
    building_id = simulation_object.building.id    
    building_object = simulation_object.building

    alist=[]

    building_floors = BuildingFloors.objects.filter(building=building_id)

    for i in building_floors:
        alist.append(i)

    #refering to certain building elevator group:
    building_group = BuildingGroup.objects.get(building=building_id)
    building_group_size = building_group.carsNumber
   
    
    return render(request, 'simulator/simulationrun.html',
                  {'building_id':building_id,
                   'simulation_id':simulation_id,
                   'simulation_arr':simulation_arr,
                   'building_group_size':building_group_size,
                   'alist':alist,})
    '''
