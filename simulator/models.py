import datetime

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import Group, User



class StandardUsers(Group):

    pass

class BuildingTypes(models.Model):

    name = models.CharField(max_length=200, default=0)
     
class Building(models.Model):
    date = models.DateTimeField(default=timezone.now, blank=True)
    name = models.CharField(max_length=200)
    b_type = models.ForeignKey(BuildingTypes, on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    floors = models.IntegerField(default=9)
    floor_dist = models.FloatField(default=3)
    population = models.IntegerField(default=50)

    class Meta:
        permissions = (
            ("view_building", "Can see available buildings"),
        )

class BuildingFloors(models.Model):
    building = models.ForeignKey(Building, on_delete=models.CASCADE)
    local_id = models.IntegerField(default=0)
    name = models.CharField(max_length=10)
    interfloor = models.FloatField(default=3)
    population = models.IntegerField(default=50)
    entry = models.FloatField(default=0)

class BuildingGroup(models.Model):
    
    building = models.ForeignKey(Building, on_delete=models.CASCADE)
    
    carsNumber = models.IntegerField(default=2)
    speed = models.FloatField(default=1)
    acceleration = models.FloatField(default=0.8)
    jerk = models.FloatField(default=1.2)
    carCapacity = models.IntegerField(default=13)
    passengerTransferTime = models.FloatField(default=0.9)
    doorOpeningTime = models.FloatField(default=2)
    doorClosingTime = models.FloatField(default=3)

class SimulationDetails(models.Model):
    

    building = models.ForeignKey(Building, on_delete=models.CASCADE)
    date = models.DateTimeField(default=timezone.now, blank=True)
    passengersArrivalTime = models.IntegerField(default=3600)
    arrivalRate = models.FloatField(default=1)
    arrivalRateStep = models.FloatField(default=1)
    arrivalRateEnd = models.FloatField(default=5)
    randomSeed = models.IntegerField(default=37)
    
class SimulationSteps(models.Model):
    
    simulation = models.ForeignKey(SimulationDetails, on_delete=models.CASCADE)
    
    step = models.FloatField(default=0) 

    
class StatSimulation(models.Model):

    simulation = models.ForeignKey(SimulationDetails, on_delete=models.CASCADE)
    step = models.FloatField(default=0)

    AINT = models.FloatField(default=0)
    AWT = models.FloatField(default=0)
    ATTD = models.FloatField(default=0)
    ACLF = models.FloatField(default=0)
    simulation_time = models.FloatField(default=0)


class StatSimulationSummary(models.Model):

    simulation = models.ForeignKey(SimulationDetails, on_delete=models.CASCADE)

    rating = models.CharField(max_length=200, default=0)
    AR = models.FloatField(default=0)
    AWT = models.FloatField(default=0)
    AINT = models.FloatField(default=0)
    ATTD = models.FloatField(default=0)
    ACLF = models.FloatField(default=0)
    simulation_time = models.FloatField(default=0)

class StatPassengers(models.Model):

    simulation = models.ForeignKey(SimulationDetails, on_delete=models.CASCADE)
    step = models.FloatField(default=0)
    
    local_id = models.IntegerField()
    entryFloor = models.IntegerField(default=0)
    destFloor = models.IntegerField() 
    arrTime = models.FloatField() 
    depTime = models.FloatField()
    destTime = models.FloatField()
    WT = models.FloatField()
    TTD = models.FloatField()

class StatCars(models.Model):

    simulation = models.ForeignKey(SimulationDetails, on_delete=models.CASCADE)
    step = models.FloatField(default=0)
    
    local_id = models.IntegerField()
    AINT = models.FloatField() 
    ACLF = models.FloatField()
    
class SimulationRunDetails(models.Model):

    simulation = models.ForeignKey(SimulationDetails, on_delete=models.CASCADE)
    step = models.FloatField(default=0)
    line = models.TextField(default=0)

class CarRunDetails(models.Model):

    simulation = models.ForeignKey(SimulationDetails, on_delete=models.CASCADE)
    step = models.FloatField(default=0)
    car = models.IntegerField()
    
    local_id = models.IntegerField()
    departure = models.FloatField() 
    INT = models.FloatField()
    load = models.IntegerField()


    
class Requirements(models.Model):

    building_type = models.ForeignKey(BuildingTypes, on_delete=models.CASCADE)

    rating = models.CharField(max_length=200, default=0)
    AR = models.FloatField()
    AWT = models.FloatField()
    AINT = models.FloatField()
    ATTD = models.FloatField()
    ACLF = models.FloatField()
    


    
    
    



