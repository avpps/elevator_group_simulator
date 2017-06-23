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
import numpy as np

######  _________  ##########

from simulator.models import Building, BuildingFloors, BuildingGroup, SimulationDetails
from simulator.models import StatSimulation, StatPassengers, StatCars, SimulationRunDetails
from simulator.models import CarRunDetails, SimulationSteps, BuildingTypes, StatSimulationSummary
from simulator.models import Requirements


from django.contrib.auth.forms import UserCreationForm
from django.views.generic.edit import CreateView
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout




def indexView(request):

    url_link = ''
    user_name = request.user.username
    user_id = request.user.id

    buildings_list = Building.objects.filter(author=user_id).order_by('-id')[:15]
    simulations_list = SimulationDetails.objects.filter(
        building__author__id=user_id).order_by('-id')[:15]
    

    return render(request, 'simulator/index.html',
                  {'buildings_list':buildings_list,
                   'simulations_list':simulations_list,
                   'user_name':user_name,
                   'url_link':url_link,})


def newBuilding(request):
    url_link = 'newbuilding/'
    user_name = request.user.username

    building_types = BuildingTypes.objects.all()

    return render(request, 'simulator/newbuilding.html',
                  {'building_types':building_types,
                   'user_name':user_name,
                   'url_link':url_link,})


@login_required(login_url='simulator:signIn')
def addNewBuilding(request):
    user_id = request.user.id
    try:
        name=request.POST['name']
        b_type=get_object_or_404(BuildingTypes, pk=request.POST['buildingtype'])
        author=get_object_or_404(User, pk=user_id)
        floors=request.POST['floors']
        floor_dist=request.POST['floor_dist']
        population=request.POST['population']

        
        Building.objects.create(
            date = timezone.now(),
            name=name,
            b_type=b_type,
            author=author,
            floors=floors,
            floor_dist=floor_dist,
            population=population,
        )

        namelist = Building.objects.order_by('id')
        building_id = namelist[len(namelist)-1].id
        building = get_object_or_404(Building, pk=building_id)

        for i in range(0, int(floors)):
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
    user_name = request.user.username
    user_id = request.user.id
    
    namelist = Building.objects.filter(author=user_id).order_by('-id')

    if building_id:
        building = get_object_or_404(Building, pk=building_id)

    else:
        try:
            building_id = request.POST['building_request']
            building = get_object_or_404(Building, pk=building_id)

        except KeyError:
            return render(request, 'simulator/newbuildingdetails.html',
                          {'building_list':namelist,
                           'user_name':user_name,},)
        
    return render(request, 'simulator/newbuildingdetails.html',
                  {'building':building,
                   'building_list':namelist,
                   'user_name':user_name,},)

@login_required(login_url='simulator:signIn')
def addNewBuildingDetails(request):
    building_id = request.POST['building_id']
    building = get_object_or_404(Building, pk=building_id)
    floors = building.floors

    for i in range(0, floors):
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
    user_name = request.user.username
    user_id = request.user.id

    namelist = Building.objects.filter(author=user_id).order_by('-id')

    return render(request, 'simulator/newsimulationdetails.html',
                  {'building_list':namelist,
                   'user_name':user_name,})


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


def simulationHistory(request, simulation_id):

    simulation = get_object_or_404(SimulationDetails, pk=simulation_id)
    steps_list = [i.step for i in simulation.simulationsteps_set.all()]

    return render(request, 'simulator/simulationhistory.html',
                  {'simulation_id': simulation_id,
                   'steps_list': steps_list,},)

def simulationHistoryRequest(request):
    a = 'sdfdsf'
    print('---asfsdafsdfsdfsd------')
    data = {
        'test': a}
    return JsonResponse(data)

    

def simulationStat(request, simulation_id=None):
    user_name = request.user.username
    user_id = request.user.id

    charts_number = 3
    charts_number_list = [i for i in range(1, charts_number+1)]

    #only buildings with any simulation just done
    buildings_list = list(set([x.building for x in SimulationDetails.objects.filter(building__author__id=user_id)]))
    

    return render(request, 'simulator/simulationstat.html',
                  {'buildings_list':buildings_list,
                   'charts_number':charts_number_list,
                   'user_name':user_name,},)


def simulationsRequest(request):
    building = get_object_or_404(Building, pk=request.GET.get('building_id', None))
    simulation_list = [x.id for x in SimulationDetails.objects.filter(building=building).order_by('-id')]

    data = {
        'simulation_list': simulation_list
    }
    return JsonResponse(data)


def chartRequest(request):
    simulation_object = get_object_or_404(SimulationDetails, pk=request.GET.get('simulation_id', None))
    view_data = request.GET.get('view_data', None)
    SimId = pk=request.GET.get('simulation_id', None)
    def numpy_converter(data):
        output_list = []
        for i in data:
            output_list.append(i.item())
        return output_list

    if view_data == 'stepsSummary':
        forchart=simulation_object.statsimulation_set.all()
        forchartlist = [[],[],[],[],[],[]]
        for asdfgh in forchart:
            forchartlist[0].append(asdfgh.step)
            forchartlist[1].append(asdfgh.AWT)
            forchartlist[2].append(asdfgh.ATTD)
            forchartlist[3].append(asdfgh.AINT)
            forchartlist[4].append(asdfgh.ACLF)
            forchartlist[5].append(asdfgh.simulation_time)
        AWT  = [{'x': i, 'y': j} for (i, j) in zip(forchartlist[0], forchartlist[1])]
        ATTD = [{'x': i, 'y': j} for (i, j) in zip(forchartlist[0], forchartlist[2])]
        AINT = [{'x': i, 'y': j} for (i, j) in zip(forchartlist[0], forchartlist[3])]
        ACLF = [{'x': i, 'y': j} for (i, j) in zip(forchartlist[0], forchartlist[4])]
        SimT = [{'x': i, 'y': j} for (i, j) in zip(forchartlist[0], forchartlist[5])]
        data = {
            'SimId': SimId,
            'AWT': AWT,
            'ATTD': ATTD,
            'AINT': AINT,
            'ACLF': ACLF,
            'SimT': SimT,
        }
        return JsonResponse(data)
    if view_data == 'waitingTimeHistogram':
        WT_bins = []
        WT_n = []
        WT_saturation = []
        colors = []
        counter = 0
        for i in simulation_object.simulationsteps_set.all():
            counter += 1
            WT_list_step = np.array([i.WT for i in simulation_object.statpassengers_set.only('WT').filter(step = i.step)])
            (WT_step_n, WT_step_bins) = np.histogram(WT_list_step, bins=20, range=(0,200), density=True)
            # converted to python datatypes
            # 'i*1000' to get value in [%] of all passengers
            WT_n.append([i*1000 for i in numpy_converter(WT_step_n)])
            WT_bins.append(numpy_converter(WT_step_bins))
            WT_saturation.append([sum(WT_step_n[:i]*1000) for i in range(1, len(WT_step_n)+1)])
            colors.append("hsl({val}, 100%, 50%)" .format(val=counter*20))
        data = {
            'SimId': SimId,
            'WT_bins': WT_bins,
            'WT_n': WT_n,
            'WT_saturation': WT_saturation,
            'colors': colors,
        }
        return JsonResponse(data)


class SignUpView(CreateView):
    template_name = 'simulator/signup.html'
    form_class = UserCreationForm


def validate_username(request):
    username = request.GET.get('username', None)
    data = {
        'is_taken': User.objects.filter(username__iexact=username).exists()
    }
    return JsonResponse(data)

def validatePassword(request):
    from django.contrib.auth.password_validation import validate_password
    from django.core.exceptions import ValidationError
    password = request.GET.get('password', None)
    try:
        result = validate_password(password)
        data = {'is_valid': True}
    except ValidationError:
        data = {'is_valid': False}

    return JsonResponse(data)

def validateEmail(request):
    from django.core.validators import validate_email
    from django.core.exceptions import ValidationError
    email = request.GET.get('email', None)
    try:
        validate_email(email)
        data = {'is_valid': False}
    except ValidationError:
        data = {'is_valid': True}

    return JsonResponse(data)

def signUp(request):
    name=request.POST['user_name']
    mail=request.POST['user_mail']
    password=request.POST['password1']

    user = User.objects.create_user(name, mail, password)
    return HttpResponseRedirect(reverse('simulator:index'))


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

