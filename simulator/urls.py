from django.conf.urls import url
from django.contrib import admin

from . import views

app_name = 'simulator'
urlpatterns = [
    url(r'^$', views.indexView, name='index'),
    url(r'^newbuilding/$', views.newBuilding, name='newBuilding'),
    url(r'^addnewbuilding/$', views.addNewBuilding, name='addNewBuilding'),
    url(r'^newbuildingdetails/$', views.newBuildingDetails,
        name='newBuildingDetails'),
    url(r'^addnewbuildingdetails/$', views.addNewBuildingDetails,
        name='addNewBuildingDetails'),
    url(r'^newsimulation/$', views.newSimulation,
        name='newSimulation'),
    url(r'^addsimulationdetails/$', views.addSimulationDetails,
        name='addSimulationDetails'),
    url(r'^simulationrun/$', views.simulationRun,
        name='simulationRun'),
    url(r'^deletebuilding/$', views.deleteBuilding,
        name='deleteBuilding'),
    url(r'^deletesimulation/$', views.deleteSimulation,
        name='deleteSimulation'),
    url(r'^simulationstat/$', views.simulationStat,
        name='simulationStat'),
    url(r'^simulationhistory/(?P<simulation_id>[0-9]+)/$', views.simulationHistory,
        name='simulationHistory'),
    url(r'^ajax/simulationHistoryRequest/$', 
        views.simulationHistoryRequest,
        name='simulationHistoryRequest'),

    url(r'^simulationstat/ajax/simulationsRequest/$', views.simulationsRequest,
        name='simulationsRequest'),
    url(r'^simulationstat/ajax/chartRequest/$', views.chartRequest,
        name='chartRequest'),
    
    url(r'^signup/$', views.signUp,
        name='signUp'),
    url(r'^ajax/validate_username/$', views.validate_username,
        name='validate_username'),
    url(r'^ajax/validateemail/$', views.validateEmail,
        name='validateEmail'),
    url(r'^ajax/validatepassword/$', views.validatePassword,
        name='validatePassword'),
    url(r'^signin/$', views.signIn,
        name='signIn'),
    url(r'^signinrun/$', views.signInRun,
        name='signInRun'),
    url(r'^logout/$', views.logOut,
        name='logOut'),
]

