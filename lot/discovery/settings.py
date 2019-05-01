EMAIL_HOST = 'localhost'
EMAIL_PORT = 25
DEFAULT_FROM_EMAIL = 'No Reply<noreply@forestdiscovery.ecotrust.org>'

DEFAULT_STAND_SPLASH = "/static/discovery/img/Evergreen_(PSF).png"
DEFAULT_STAND_IMAGE = "/static/discovery/img/Trees_icon_wide.png"

CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': 'Custom',
        'toolbar_Custom': [
            ['Format'],
            ['Bold', 'Italic', 'Underline','Strike','Subscript','Superscript'],
            ['NumberedList', 'BulletedList', '-', 'Outdent', 'Indent', '-', 'JustifyLeft', 'JustifyCenter', 'JustifyRight', 'JustifyBlock'],
            ['Link', 'Unlink'],
            ['Image','Table','HorizontalRule','SpecialChar'],
            [ 'TextColor','BGColor' ],
            ['Undo','Redo'],
            ['RemoveFormat', 'Source']
        ],
    }
}

IMPORT_TREELIST = False

HARD_SOFTWOOD_LOOKUP = {
    'Douglas-fir': 'softwood',
    'Nonstocked': 'unknown',
    'Bigleaf maple': 'hardwood',
    'Red alder': 'hardwood',
    'Lodgepole pine': 'softwood',
    'Tanoak': 'hardwood',
    'Western larch': 'softwood',
    'Oregon white oak': 'hardwood',
    'Western juniper': 'softwood',
    'Pacific madrone': 'hardwood',
    'Grand fir': 'softwood',
    'Western hemlock': 'softwood',
    'Unknown; access denied': 'unknown',
    'Western white pine': 'softwood',
    'Ponderosa pine': 'softwood',
    'Oregon ash': 'hardwood',
    'Western redcedar': 'softwood',
    'Sitka spruce': 'softwood',
    'Black cottonwood': 'hardwood',
    'Engelmann spruce': 'softwood',
    'White fir': 'softwood',
    'Incense cedar': 'softwood',
    'Quaking aspen': 'hardwood',
    'Curlleaf mountain-mahogany': 'hardwood',
    'Mountain hemlock': 'softwood',
    'Shasta red fir': 'softwood',
    'Subalpine fir': 'softwood',
    'Whitebark pine': 'softwood',
    'Pacific silver fir': 'softwood',
    'Noble fir': 'softwood',
    'Port-Orford-cedar': 'softwood',
    'California-laurel': 'hardwood',
    'Canyon live oak': 'hardwood',
    'Jeffrey pine': 'softwood',
    'Golden chinkapin': 'hardwood',
    'Sugar pine': 'softwood',
    'Cherry': 'hardwood',
    'Unknown type': 'unknown',
    'Alaska cedar': 'softwood',
    'Subablpine larch': 'softwood',
    'Western paper birch': 'hardwood',
    'Willow': 'hardwood',
    'California black oak': 'hardwood',
    'Pacific yew': 'softwood',
    'White alder': 'hardwood',
    'Scotch pine': 'softwood',
    'Redwood': 'softwood',
    'Apple': 'hardwood',
    'Knobcone pine': 'softwood',
}

METRICS_DICT = [
    {
        'title': 'Fundamentals',
        'metrics': [
            {
                'title': 'Basal Area (BA)',
                'id': 'funamentals-basal-area',
                'metric_key': 'ba',
                'axes': {
                    'x': {
                        'label': 'Year'
                    },
                    'y': {
                        # 'label': 'Basal Area in ft<sup>2</sup>/acre'
                        'label': 'Basal Area in ft<tspan baseline-shift="super">2</tspan>/acre'
                    }
                }
            # },{
            #     'title': 'Quadratic Mean Diameter (QMD)',
            #     'id': 'fundamentals-quadratic-mean-diameter'
            },{
                'title': 'Trees per Acre (TPA)',
                'id': 'fundamentals-trees-per-acre',
                'metric_key': 'tpa',
                'axes': {
                    'x': {
                        'label': 'Year'
                    },
                    'y': {
                        'label': 'Trees Per Acre'
                    }
                }
            # },{
            #     'title': 'Successional Stage',
            #     'id': 'fundamentals-successional-stage'
            # },{
            #     'title': 'Annual Growth',
            #     'id': 'fundamentals-annual-growth'
            # },{
            #     'title': 'Annual Mortality',
            #     'id': 'fundamentals-annual-mortality'
            },
        ]
    },{
        'title': 'Carbon',
        'metrics': [
            {
                'title': 'Carbon stored in the forest',
                'id': 'carbon-stored-in-forest',
                'metric_key': 'agl_carbon',
                'axes': {
                    'x': {
                        'label': 'Year'
                    },
                    'y': {
                        'label': 'Carbon (metric tons C)'
                    }
                }
            # },{
            #     'title': 'Carbon stored in products',
            #     'id': 'carbon-stored-in-products'
            },{
                'title': 'Total Carbon Storage',
                'id': 'carbon-total-stored',
                'metric_key': 'total_carbon',
                'axes': {
                    'x': {
                        'label': 'Year'
                    },
                    'y': {
                        'label': 'Carbon (metric tons C)'
                    }
                }
            },
        ]
    },{
        'title': 'Timber',
        'metrics': [
            {
                'title': 'Standing timber volume',
                'id': 'timber-standing-volume',
                'metric_key': 'standing_timber',
                'axes': {
                    'x': {
                        'label': 'Year'
                    },
                    'y': {
                        'label': 'Standing Timber in MBF'
                    }
                }
            },{
                'title': 'Harvested timber volume',
                'id': 'timber-harvested-volume',
                'metric_key': 'harvested_timber',
                'axes': {
                    'x': {
                        'label': 'Year'
                    },
                    'y': {
                        'label': 'Harvested Timber in MBF'
                    }
                }
            # },{
            #     'title': 'Cash flow',
            #     'id': 'timber-cash-flow'
            },
        ]
    },{
        'title': 'Wildfire',
        'metrics': [
            {
                'title': 'Fire Hazard Rating',
                'id': 'wildfire-hazard-rating',
                'metric_key': 'fire',
                'axes': {
                    'x': {
                        'label': 'Year'
                    },
                    'y': {
                        'label': 'Fire Hazard Rating'
                    }
                }
            # },{
            #     'title': 'Mortality for Moderate Wildfire',
            #     'id': 'wildfire-mortality-moderate'
            # },{
            #     'title': 'Mortality for Severe Wildfire',
            #     'id': 'wildfire-mortality-severe'
            },
        ]
    },

]
