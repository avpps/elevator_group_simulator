from django.conf.urls import url
from django.contrib import admin

from . import views

from jchart.views import ChartView

summary_chart_parameterized = views.SummaryChartParameterized()
test_chart = views.TestChart()

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
    url(r'^signup/$', views.SignUpView.as_view(),
        name='signup'),
    url(r'^signup/ajax/validate_username/$', views.validate_username,
        name='validate_username'),
    url(r'^signin/$', views.signIn,
        name='signIn'),
    url(r'^signinrun/$', views.signInRun,
        name='signInRun'),
    url(r'^logout/$', views.logOut,
        name='logOut'),
    url(r'^summarychartparameterized/(?P<simulation_id>[0-9]+)/$',
        ChartView.from_chart(summary_chart_parameterized),
        name='summary_chart_parameterized'),
    url(r'^testchart/(?P<value>[0-9]+)/$',
        ChartView.from_chart(test_chart),
        name='test_chart'),
    url(r'^simulationstat/ajax/generateChart/$', views.generateChart,
        name='generateChart'),

]

