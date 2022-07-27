from django.urls import path
from . import views


urlpatterns = [
    path('', views.index, name='URL index'),
    path('login',views.UserLogin,name="User login"),
    path('logout',views.UserLogout,name="User logout"),
    path('users/', views.UserFunctionDistributor, name='user-function-distributor'),
    path('users/<int:user_id>/', views.ModifyUserFunctionDistributor, name='user-modify-function-distributor'),
    path('decisions',views.DecisionList,name="Decision List"),
    #path('decisioncreate',views.DecisionCreate,name="decisioncreate"),
    path('decisions/<int:pk>',views.DecisionDelete,name="Decision Delete"),
    path('decisions/decisionfilter',views.DecisionFilter,name="Decision Filter"),
    path('rules',views.RulesCreateList,name="Rule create or List"),
    path('rules/<int:pk>',views.RulesDeleteEdit,name="Rule Delete or Edit"),
    path('rules/enable',views.RuleEnable,name="Rules enable"),
    path('statistics',views.StatisticsList,name="Statistics list"),
    path('statistics/datafilter',views.StatisticsFilter,name="Statistics Data Filter"),
    path('testconnection/', views.TestConnection, name="test-connection"),
    path('settings/', views.SettingsFunctionDistributor, name='settings'),
    path('about',views.aboutApi,name="about"),
    path('download',views.log_Download,name="Log Download"),
    path('upload-offline/', views.ImportScripts, name="import-scripts"),
    path('profile',views.UserProfile,name="user profile/edit"),
    path('ale-upgrade/', views.UpgradeFromALE, name="ale-upgrade"),
]
