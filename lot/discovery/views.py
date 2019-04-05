from django.shortcuts import render, redirect
from madrona.features.views import get_object_for_viewing

# Create your views here.
from django.http import HttpResponse

def index(request):
    return redirect('/discovery/landing/')

# landing page for non logged in users
def landing(request):
    if request.user.is_authenticated:
        return redirect('/discovery/stand_profile/')
    else:
        context = {}
        return render(request, 'discovery/landing.html', context)

# account login page
def login(request):
    context = {}
    return render(request, 'discovery/account/login.html', context)

# account register page
def register(request):
    context = {
        'register': register,
    }
    return render(request, 'discovery/account/register.html', context)

# account password reset and username recovery page
def reset(request):
    context = {}
    return render(request, 'discovery/account/reset.html', context)

# support new layout for user stand/properties profiles
def stand_profile(request):
    context = {
        'username': request.user.username,
        'title': 'stands',
        # use button_text and button_action together
        'button_text': '+ Add a new property',
        'button_action': '/discovery/map/',
    }
    return render(request, 'discovery/common/grid.html', context)

# account password reset and username recovery page
def stands(request):
    context = {
        # Todo: add username condition and value
        'username': request.user.username,
        'title': 'stands',
        # use button_text and button_action together
        'button_text': '+ Add a new property',
        'button_action': '',
    }
    return render(request, 'discovery/common/grid.html', context)

# find your forest page
def find_your_forest(request):
    context = {
        'title': 'Find Your Forest',
        'flatblock_slug': 'find-your-forest',
        # use button_text and button_action together
        'button_text': 'WATCH TUTORIAL',
        'button_action': '',
        # specific for action buttons template
        'act_btn_one_text': 'Choose an pre canned property',
        'act_btn_one_action': '/discovery/stands/',
        'act_btn_two_text': 'Map your own property',
        'act_btn_two_action': '/discovery/map/',
    }
    return render(request, 'discovery/common/action_buttons.html', context)

# collect data page
def collect_data(request):
    context = {
        'title': 'Collect data',
        'flatblock_slug': 'collect-data',
        # use button_text and button_action together
        'button_text': 'WATCH TUTORIAL',
        'button_action': '',
        # specific for action buttons template
        'act_btn_one_text': 'Download tree list spreadsheet template',
        'act_btn_one_action': '',
        'act_btn_two_text': 'Download a stand table PDF template',
        'act_btn_two_action': '',
        # cta below action buttons options
        ## should this button be displayed
        'use_step_btn': True,
        'step_btn_action': '/discovery/enter_data/',
        'step_btn_text': 'Enter data now',
    }
    return render(request, 'discovery/common/action_buttons.html', context)

# enter data page
def enter_data(request):
    context = {
        'title': 'Enter data',
        'flatblock_slug': 'enter-data',
        # use button_text and button_action together
        'button_text': 'WATCH TUTORIAL',
        'button_action': '',
        # specific for action buttons template
        'act_btn_one_text': 'Upload a new tree list',
        'act_btn_one_action': '',
        'act_btn_two_text': 'Enter a new stand table',
        'act_btn_two_action': '/discovery/enter_stand_table/',
        # cta below action buttons options
        ## should this button be displayed
        ### Todo: may change to insert a disabled parameter
        ### see comment #1 : https://xd.adobe.com/view/f5cb1927-f0b7-4642-5232-f30339f78d62-83fa/screen/e8c2b162-e3c5-450f-a39e-bb71e177f1fa/Enter-data
        'use_step_btn': True,
        'step_btn_action': '',
        'step_btn_text': 'View forest profile',
    }
    return render(request, 'discovery/common/action_buttons.html', context)

# enter new stand table page
def enter_stand_table(request):
    # manage_table = tree_table(request, 'trees_forestproperty_1')
    context = {
        'title': 'Enter stand table',
        'flatblock_slug': 'enter-stand-table',
        # use button_text and button_action together
        'button_text': 'WATCH TUTORIAL',
        'button_action': '',
        # specific for data entry template

        # cta below action buttons options
        ## should this button be displayed
        'use_step_btn': True,
        'step_btn_action': '',
        'step_btn_text': 'View forest profile',
        # TODO: Add real values for property
        # 'manage_table': manage_table,
    }
    return render(request, 'discovery/common/data_table.html', context)

def manage_strata(request, property_uid):
    '''
    Strata management view
    '''
    forestproperty = get_object_for_viewing(request, property_uid)
    if isinstance(forestproperty, HttpResponse):
        return forestproperty
    name = forestproperty.name
    is_locked = forestproperty.is_locked
    return render(
        request,
        'discovery/common/strata.html',
        {'property_id': property_uid,
         'property_name': name,
         'property_is_locked': is_locked})


# overwrite static content in lot app about.html
def map(request):
    context = {
        'title': 'Map your forest stand',
        'flatblock_slug': 'map-your-property',
        # use button_text and button_action together
        'button_text': 'WATCH TUTORIAL',
        'button_action': '',
    }
    return render(request, 'discovery/map.html', context)

# overwrite static content in lot app about.html
def about(request):
    context = {}
    return render(request, 'discovery/common/about.html', context)

# overwrite satic content in lot app documenation
def documentation(request):
    context = {}
    return render(request, 'discovery/common/documentation.html', context)
