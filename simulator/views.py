from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.utils import timezone
from django.db.models import Avg, Sum

from django.contrib.auth.decorators import login_required, permission_required

######  for tests  ##########

import simpy
import random
import sqlite3

from . import stat_db_run

######  _________  ##########

from .models import Building, BuildingFloors, BuildingGroup, SimulationDetails
from .models import StatSimulation, StatPassengers, StatCars, SimulationRunDetails
from .models import CarRunDetails, SimulationSteps, BuildingTypes, StatSimulationSummary
from .models import Requirements


def indexView(request):
    buildings_list = Building.objects.order_by('-id')[:15]
    simulations_list = SimulationDetails.objects.order_by('-id')[:15]



    return render(request, 'simulator/index.html',
                  {'buildings_list':buildings_list,
                   'simulations_list':simulations_list,})


def newBuilding(request):

    building_types = BuildingTypes.objects.all()

    return render(request, 'simulator/newbuilding.html',
                  {'building_types':building_types})

@login_required(login_url='simulator:signIn')
def addNewBuilding(request):
    try:
        name=request.POST['name']
        b_type=get_object_or_404(BuildingTypes, pk=request.POST['buildingtype'])
        floors=request.POST['floors']
        floor_dist=request.POST['floor_dist']
        population=request.POST['population']
        
        Building.objects.create(
            date = timezone.now(),
            name=name,
            b_type=b_type,
            floors=floors,
            floor_dist=floor_dist,
            population=population,
        )

        namelist = Building.objects.order_by('id')
        building_id = namelist[len(namelist)-1].id
        building = get_object_or_404(Building, pk=building_id)

        for i in range(1, int(floors)+1):
            BuildingFloors.objects.create(
                building=building,
                local_id=i,
                name=i,
                interfloor=floor_dist,
                population=population,
                entry=0,
            )
            
        BuildingGroup.objects.create(
            building=building,
            carsNumber=request.POST['carsNumber'],
            speed=request.POST['speed'],
            acceleration=request.POST['acceleration'],
            jerk=request.POST['jerk'],
            carCapacity=request.POST['carCapacity'],
            passengerTransferTime=request.POST['passengerTransferTime'],
            doorOpeningTime=request.POST['doorOpeningTime'],
            doorClosingTime=request.POST['doorClosingTime'],
        )

        SumsBuil = BuildingFloors.objects.filter(building=building).aggregate(Sum('population'), Sum('interfloor'))

        Building.objects.filter(pk=building_id).update(
            population=SumsBuil['population__sum'],
            floor_dist=SumsBuil['interfloor__sum'],
        )

    except ValueError:
        print('-------------', b_type )
        return HttpResponseRedirect(reverse('simulator:newBuilding'))
    else:
        return HttpResponseRedirect(reverse('simulator:newBuildingDetails'))


def newBuildingDetails(request, building_id=None):
    
    namelist = Building.objects.all().order_by('-id')

    if building_id:
        building = get_object_or_404(Building, pk=building_id)

    else:
        try:
            building_id = request.POST['building_request']
            building = get_object_or_404(Building, pk=building_id)

        except KeyError:
            return render(request, 'simulator/newbuildingdetails.html',
                          {'building_list':namelist},)
        
    return render(request, 'simulator/newbuildingdetails.html',
                  {'building':building,
                   'building_list':namelist},)

@login_required(login_url='simulator:signIn')
def addNewBuildingDetails(request):
    building_id = request.POST['building_id']
    building = get_object_or_404(Building, pk=building_id)
    floors = building.floors

    for i in range(1, floors+1):
        BuildingFloors.objects.filter(building=building).filter(local_id=i).update(
            name=request.POST['name{cd}'.format(cd=i)],
            interfloor=request.POST['floor_dist{cd}'.format(cd=i)],
            population=request.POST['population{cd}'.format(cd=i)],
            entry=request.POST['entry{cd}'.format(cd=i)],
        )

    BuildingGroup.objects.filter(building=building).update(
        carsNumber=request.POST['carsNumber'],
        speed=request.POST['speed'],
        acceleration=request.POST['acceleration'],
        jerk=request.POST['jerk'],
        carCapacity=request.POST['carCapacity'],
        passengerTransferTime=request.POST['passengerTransferTime'],
        doorOpeningTime=request.POST['doorOpeningTime'],
        doorClosingTime=request.POST['doorClosingTime'],
    )

    SumsBuil = BuildingFloors.objects.filter(building=building).aggregate(Sum('population'), Sum('interfloor'))

    Building.objects.filter(pk=building_id).update(
        population=SumsBuil['population__sum'],
        floor_dist=SumsBuil['interfloor__sum'],
    )
    
    return HttpResponseRedirect(reverse('simulator:newBuildingDetails'))


def newSimulation(request):

    namelist = Building.objects.order_by('-id')

    return render(request, 'simulator/newsimulationdetails.html',
                  {'building_list':namelist,})


@login_required(login_url='simulator:signIn')
def addSimulationDetails(request):
    
    building_id = request.POST['building_id']
    building = get_object_or_404(Building, pk=building_id)

    arrivalRate=float(request.POST['arrivalRate'])
    arrivalRateStep=float(request.POST['arrivalRateStep'])
    arrivalRateEnd=float(request.POST['arrivalRateEnd'])

    SimulationDetails.objects.create(
        date=timezone.now(),
        building=building,
        passengersArrivalTime=request.POST['passengersArrivalTime'],
        arrivalRate=arrivalRate,
        arrivalRateStep=arrivalRateStep,
        arrivalRateEnd=arrivalRateEnd,
        randomSeed=request.POST['randomSeed'],
        )
    
    '''create steps table for running serial simulation:'''
    simulationslist = SimulationDetails.objects.order_by('id')
    simulation_position_on_list = len(simulationslist)-1
    simulation_id = simulationslist[simulation_position_on_list].id    
        
    simulation = get_object_or_404(SimulationDetails, pk=simulation_id)

    '''write first step:'''
    SimulationSteps.objects.create(
        simulation=simulation,
        step=arrivalRate,
    )
    '''...and rests:'''
    while arrivalRate < arrivalRateEnd:
        arrivalRate += arrivalRateStep
        SimulationSteps.objects.create(
            simulation=simulation,
            step=arrivalRate,
        )
                                       
    return HttpResponseRedirect(reverse('simulator:simulationRun'))


@login_required(login_url='simulator:signIn')
def deleteBuilding(request):

    building_id = request.POST['del']
    get_object_or_404(Building, pk=building_id).delete()

    return HttpResponseRedirect(reverse('simulator:index'))


@login_required(login_url='simulator:signIn')   
def deleteSimulation(request):

    simulation_id = request.POST['del']
    get_object_or_404(SimulationDetails, pk=simulation_id).delete()

    return HttpResponseRedirect(reverse('simulator:index'))



def simulationRun(request):


    '''
        ELEVATOR GROUP SIMULATOR
        
    Process generally run like in nature :)
    1  Building and population parameters (soon also rest) are defined in input database
    2  Random passenger generator put them into process.
    3  Simple control algorithm give elevators information where to go to serve passanger.
       In future elevator control system will be based on dispathed allocations method.
    4  During process run data are collected (e.g. passanger arrival time, actual elevator speed, passangers in lobby)  
    5  When process end, data are saved to results database and evaluated to get final results 
       which are needed to perform elevator group work general rating.
       Also charts are generated to show how process parameters ran in time.
    Under devleopment (in priority order):
    1  Web site using Django working as user interface
    2  Implement dispathed allocations method for group control
    3  Process run visualization using probably https://www.panda3d.org/
    '''

    def passengersArrival(env):
        while len(passengers_stat) <= passengerAll:
            passengerActAr = abs(int(random.gauss(passengerAvgAr, passengerAvgAr**0.5)))
            # append all new passengers to passengers database:
            for i in range(passengerActAr):
                j = len(passengers_stat)
                passengers_stat[j] = Passenger(env, j, env.now, buildingFloorNumber)
                lobbyQueue.append(j)
                history.append('%d        passangerID: %d appeared. LobbyQueueLen: %d'
                              % (env.now, j, len(lobbyQueue)))
                history.append(str(lobbyQueue))
                history.append('%s' % '\n')
            # passenger arrival time is also random:
            passengerActAt = abs(random.gauss(passengerAvgAt, passengerAvgAt**0.5))
            yield env.timeout(passengerActAt)
        history.append('\n koniec naplywu \n')
        processEnd_reactivate.succeed()

    def input_run():

        global buildingPopulation
        buildingPopulation = 0

        for i in building_floors:
            j = [i.local_id,
                 i.name,
                 i.interfloor,
                 i.population,
                 i.entry]
            floorChartList.append(j)
            buildingPopulation += i.population
        

    def carGenerator(env):
        '''create cars in cars_stat dictionary:'''
        for i in range(carsNumber):
            cars_stat[i] = Car(env, i)
        '''activate car run process:'''
        for i in range(len(cars_stat)):        
            env.process(cars_stat[i].runCar(env))
        

    def processEnd(env):
        yield processEnd_reactivate
        for i in passengers_stat:
            yield passengers_stat[i].passengerRun_proc


    def reports_generator():

        '''history_file_name = 'run_history_{rn}'.format(rn=revision_no)
        stat_db_name = 'stat_db_{rn}'.format(rn=revision_no)

        stat_db_run.create_tables(stat_db_name)  
        history_file = open('{s}.txt'.format(s=history_file_name), 'a')

        for i in history:
            history_file.write(i)
        history_file.write('')'''
        
        for i, j in passengers_stat.items():
            WT = j.depTime - j.arrTime
            TTD = j.destTime - j.arrTime
            StatPassengers.objects.create(simulation=simulation_object,
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
                CarRunDetails.objects.create(simulation=simulation_object,
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
                
                
            StatCars.objects.create(simulation=simulation_object,
                                    step=arrivalRate,
                                    
                                    local_id=j.id,
                                    AINT = round(AINT, 2),
                                    ACLF = round(ACLF, 2),)


        AVGpassengers = StatPassengers.objects.filter(simulation=simulation_object).aggregate(Avg('WT'), Avg('TTD'))            
        AVGcars = StatCars.objects.filter(simulation=simulation_object).aggregate(Avg('AINT'), Avg('ACLF'))

        
        StatSimulation.objects.create(
            simulation=simulation_object,
            step=arrivalRate,
                                      
            AINT=round(AVGcars['AINT__avg'], 2),
            AWT=round(AVGpassengers['WT__avg'], 2),
            ATTD=round(AVGpassengers['TTD__avg'], 2),
            ACLF=round(AVGcars['ACLF__avg'], 2),
        )


        '''history_file.write('\n \n')'''
        
        '''stat_db_run.add_col_wt_ttd()

        #car values:
        for i, j in cars_stat.items():
            j.avgClf()
        sClf = 0
        Tc = 0

        for i, j in cars_stat.items():
            stat_db_run.add_row_cars_stat(i, j.carCapacity, j.carCapacity, j.avgClfValue)
            stat_db_run.create_car_table(i)
            for k in range(len(j.carDepartures)):
                if k != 0:
                    INT = j.carDepartures[k][0] - j.carDepartures[k-1][0]
                else:
                    INT = j.carDepartures[k][0]
                stat_db_run.add_row_car_table(i, j.carDepartures[k][0],
                                              INT, j.carDepartures[k][1])

            sClf += j.avgClfValue
            Tc += 1

        

        AVT = sVt / Tp
        ATTD = sTtd / Tp
        ACLF = sClf / Tc

        #history.append('AINT= %d \n' % AINT)
        history_file.write('AVT= %d \n' % AVT)
        history_file.write('ATTD= %d \n' % ATTD)
        history_file.write('ACLF= %d \n' % ACLF)
        history_file.close()

        stat_db_run.summarize()

        '''



    def reports_generator_summary():
        ''' module for create StatSimulationSummary object '''
        ''' with refference to Requirements obj '''

        # take Requirements dedicated to certain building:

        building_type = simulation_object.building.b_type
        requirements_objects = Requirements.objects.filter(building_type=building_type).order_by('-rating')

        # take all steps StatSimulation for certain simulation:

        steps_summary_objects = simulation_object.statsimulation_set.all().order_by('-step')

        # compare booth and save StatSimulationSummary object:

        for step in steps_summary_objects:
            stop = False
            for reqirement in requirements_objects:

                if (step.step <= reqirement.AR
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




        
      
    class Passenger():
        # containing: ID, arr time, dep time, destTime
        def __init__(self, env, id, arrTime, buildingFloorNumber):
            self.env = env
            self.id = id
            self.arrTime = arrTime
            self.passengerUnloading_proc = env.process(self.passengerUnloading(env, self.id))
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
                yield env.timeout(0.01)
                for allocatedCar in range(carsNumber):
                    yield env.timeout(0.0001)
                    '''car have to be on floor 0 and not overfilled:'''
                    if cars_stat[allocatedCar].carPosition == 0 and cars_stat[allocatedCar].carUsage.count < cars_stat[allocatedCar].carCapacity:
                        history.append('%d    passenger %d try to entry car %d. Doors are: %s \n'
                                      % (env.now, passengerId, allocatedCar,
                                         cars_stat[allocatedCar].doorOpenedMonit.is_alive))
                        self.req = cars_stat[allocatedCar].carUsage.request(priority=self.id)
                        yield self.req | cars_stat[allocatedCar].doorOpenedMonit 
                        history.append('%d       passenger %d waited %d. Doors are: %s \n'
                                      % (env.now, passengerId, allocatedCar,
                                         cars_stat[allocatedCar].doorOpenedMonit.is_alive))
                        if not self.req.triggered:
                            history.append('%d    DoCl passenger %d not leave queue and not entry car %d \n'
                                          % (env.now, passengerId, allocatedCar))
                            cars_stat[allocatedCar].carUsage.put_queue.remove(self.req)                      
                        else:                            
                            lobbyQueue.pop(lobbyQueue.index(passengerId))
                            cars_stat[allocatedCar].passengersInCar.append(passengerId)
                            cars_stat[allocatedCar].passengersInCarDest.append(self.destFloor)
                            passengers_stat[passengerId].depTime = env.now
                            history.append('%d    passenger %d leave queue and entry car %d. LobbyQueue: %s \n'
                                          % (env.now, passengerId, allocatedCar, str(lobbyQueue)))
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
            self.carPosition = 0
            self.carPositionDist = 0
            self.carPositionDistSum = 0
            
            self.runTime = 2    # all interfloors are the same
            
            self.carUsage = simpy.PriorityResource(env, capacity = self.carCapacity)
            #self.doorOpened = env.process(doorOpened(env))
            self.doorOpened_reactivate = env.event()
            
            
            self.passengersInCar = []
            self.passengersInCarDest = []
            self.carDepartures = []
            ''''''
            self.carMovement = [[],[],[],[]]
            self.avgClfValue = 0
            

        def avgClf(self):
            sClf = 0
            T = 0
            for i in self.carDepartures:
                T += 1
                sClf += i[1]
            self.avgClfValue = sClf/T

        
            
        def putting_inside(self, env, passengersInCar1):
            history.append('%d      %s \n' % (env.now, list(self.just_inside)))
            for i in passengersInCar1:
                if i not in self.just_inside:
                    self.just_inside.append(i)
                    #history.append('powinno ')
                    yield env.timeout(self.passengerTransferTime)
                    history.append('%d       1 sec for pass transfer \n' % env.now)
                    yield env.process(self.putting_inside(env, self.passengersInCar))
                    
        def doorOpened(self, env):
            yield self.doorOpened_reactivate
            yield env.timeout(0)

        def runCar(self, env):
            history.append('%d car %d generated \n' %(env.now, self.id))
            while True:
                self.carPosition = 0
                self.carPositionDist = 0
                self.carPositionDistSum = 0
                carPositionDistSumForInterfloorRun = 0
                self.doorOpenedMonit = env.process(self.doorOpened(env))
                
                if len(lobbyQueue)>0: history.append('%d car %d at floor 0. \n' % (env.now, self.id))
                yield env.timeout(self.doorOpeningTime)
                
                if len(self.passengersInCar) > 0:
                    # after loading make additional procedures (photocell delays, door close, etc...):
                    self.just_inside = []
                       
                    yield env.process(self.putting_inside(env, self.passengersInCar))
                    
                    self.carPosition = 0.5
                    
                    history.append('%d car %d at floor 0. Doors start closing. Passengers: %d %s. PassengersInCarDest: %s \n\n'
                                  % (env.now, self.id, len(self.passengersInCar),
                                     str(self.passengersInCar), str(self.passengersInCarDest)))
                    
                    self.doorOpened_reactivate.succeed()
                    self.doorOpened_reactivate = env.event()
                    
                    yield env.timeout(self.doorClosingTime)
                    self.carDepartures.append([env.now, len(self.passengersInCar)])
                    history.append('%d car %d leave floor 0. Doors are: %s \n'
                          %(env.now, self.id, self.doorOpenedMonit.is_alive))
                    
                    yield env.timeout(0)    # additionl time for acceleration
                    ###history.append(env.now, '|' * len(lobbyQueue))
                    for i in range(1, buildingFloorNumber+1):    # 'buildingFloorNumber+1' to be sure that below if will be checked also on top floor
                        if len(self.passengersInCar) > 0:
                            self.carPosition = i-0.5             # run for next floor, but it take a time
                            self.carPositionDist += floorChartList[i][2]
                            self.carPositionDistSum += floorChartList[i][2]
                            
                            if i in self.passengersInCarDest:
                                yield env.process(self.motion(env, self.carPositionDist, carPositionDistSumForInterfloorRun, 1))
                                self.carPosition = i
                                self.carPositionDist = 0
                            else:
                                history.append('%d car %d on landing %d. Nobody leave car. \n' % (env.now, self.id, i))
                                continue
                        else:
                            history.append('%d car %d go back \n' % (env.now, self.id))
                            self.carPosition = 0.5
                            yield env.process(self.motion(env, self.carPositionDistSum, self.carPositionDistSum, -1))
                            break                                          #when car is empty, go back to floor 0
                        carPositionDistSumForInterfloorRun = self.carPositionDistSum
                        
                        # passengeer 'j' leave car but it take a time:
                        for j in reversed(self.passengersInCar):           # reversed to avoid pass and dest lists position changes.
                                                                           # thanks this, pass and dest are removed from right to left from list 
                            if i == passengers_stat[j].destFloor:
                                yield env.timeout(self.passengerTransferTime)
                                passengers_stat[j].passengerUnloading_reactivate.succeed()
                                passengers_stat[j].passengerUnloading_reactivate = env.event()
                                
                                self.wy = cars_stat[self.id].passengersInCar.index(j)
                                cars_stat[self.id].passengersInCar.pop(self.wy)
                                cars_stat[self.id].passengersInCarDest.pop(self.wy)
                                history.append('%d car %d on landing %d. passenger %d leave car. Passengers in car: %s. PassengersInCarDest: %s \n'
                                              % (env.now, self.id, i, passengers_stat[j].id,
                                                 str(cars_stat[self.id].passengersInCar),
                                                 str(self.passengersInCarDest)))
                                
               
                        # after unloading make additional procedures (photocell delays, door close, etc...):
                        yield env.timeout(1)

                                

        def motion(self, env, s_max, initial_car_distance, run_direction):

            '''all is based on actualization of below statements in next steps with 'step_size' incrementation: 
            s = s0 + v0*(t) + (1/2)*a0*(t**2) + (1/6)*j*(t**3)
            v = v0 + a0*(t) + (1/2)*j*(t**2)
            a = a0 + j*(t)
            j = j0 '''

            start_time = env.now
            
            step_size = 0.01      # movement incrementation
            t = 0                 # base time
            t2 = 0                # additional time start when deceleration start

            s0 = 0
            v0 = 0
            a0 = 0
            j0 = self.jerk            # jerk [m/s3]
            
            s = 0
            v = 0
            a = 0
            j = j0
            
            vmax = self.speed
            amax = self.acceleration
            amin = -self.acceleration

            dActS = 0            # deceleration activation distance (s) before planned stop
            sTillEnd = s_max     # distance to end of planned way
            

            while s < s_max:     # run till reached demanded distance 's_max'
                t += step_size   # update base time in each step
                
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



    '''refering to certain simulation:'''
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



    random.seed(simulation_object.randomSeed)
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
        passengers_stat = {}    # local passengers database list
        cars_stat = {}          # local passengers database list
        history = []
        lobbyQueue = []         # actual passengers at lobby

        # building population per 5 min [%]
        arrivalRate = simulation_step.step

        passengerAll = int((passengersArrivalTime/300)*(buildingPopulation*arrivalRate/100))

        passengerAvgAr = 1                                                # passenger avg quantity
        passengerAvgAt = 300 / (buildingPopulation*(arrivalRate/100))     # passenger apperance avg cadency in 5 min
            
        env = simpy.Environment()
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


def simulationStat(request, simulation_id=None):

    charts_number = 3
    charts_number_list = [i for i in range(1, charts_number+1)]

    #only buildings with any simulation just done
    buildings_list = list(set([x.building for x in SimulationDetails.objects.all()]))
    

    return render(request, 'simulator/simulationstat.html',
                  {'buildings_list':buildings_list,
                   'charts_number':charts_number_list,},)


def simulationsRequest(request):
    building = get_object_or_404(Building, pk=request.GET.get('building_id', None))
    simulation_list = [x.id for x in SimulationDetails.objects.filter(building=building).order_by('-id')]

    data = {
        'simulation_list': simulation_list
    }
    return JsonResponse(data)


def chartRequest(request):
    simulation_object = get_object_or_404(SimulationDetails, pk=request.GET.get('simulation_id', None))
    forchart=simulation_object.statsimulation_set.all()
    forchartlist = [[],[],[],[],[]]
    
    for asdfgh in forchart:
        forchartlist[0].append(asdfgh.step)
        forchartlist[1].append(asdfgh.AWT)
        forchartlist[2].append(asdfgh.ATTD)
        forchartlist[3].append(asdfgh.AINT)
        forchartlist[4].append(asdfgh.ACLF)
   
    AWT  = [{'x': i, 'y': j} for (i, j) in zip(forchartlist[0], forchartlist[1])]
    ATTD = [{'x': i, 'y': j} for (i, j) in zip(forchartlist[0], forchartlist[2])]
    AINT = [{'x': i, 'y': j} for (i, j) in zip(forchartlist[0], forchartlist[3])]
    ACLF = [{'x': i, 'y': j} for (i, j) in zip(forchartlist[0], forchartlist[4])]

    data = {
        'AWT': AWT,
        'ATTD': ATTD,
        'AINT': AINT,
        'ACLF': ACLF,
    }
    return JsonResponse(data)




from django.contrib.auth.forms import UserCreationForm
from django.views.generic.edit import CreateView
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout


class SignUpView(CreateView):
    template_name = 'simulator/signup.html'
    form_class = UserCreationForm


def validate_username(request):
    username = request.GET.get('username', None)
    data = {
        'is_taken': User.objects.filter(username__iexact=username).exists()
    }
    return JsonResponse(data)

def signIn(request):
    return render(request, 'simulator/signin.html')

def signInRun(request):
    username = request.POST['username']
    password = request.POST['password']
    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        return HttpResponseRedirect(reverse('simulator:index'))
    else:
        return render(request, 'simulator/signin.html')

def logOut(request):
    logout(request)
    return HttpResponseRedirect(reverse('simulator:index'))
    

def generateChart(request):
    simulation_id = request.GET.get('simulation_id', None)
    chart=SummaryChart()
    chart.simulation_id=simulation_id

    data = {
        'name': chart.chart_type
    }
    return JsonResponse(data)

