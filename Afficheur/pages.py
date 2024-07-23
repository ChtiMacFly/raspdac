# Page Definitions
# See Page Format.txt for instructions and examples on how to modify your display settings

PAGES_Play = {
    'name':"Play",
    'pages':
    [
        {
        'name':"Artist",
        'duration':8,
        'hidewhenempty':'any',
        'hidewhenemptyvars': [ "artist" ],
        'lines': [
            {
            'name':"top",
            'variables': [ "artist" ],
            'format':"{0}",
            'justification':"left",
            'scroll':True
            },
            {
            'name':"bottom",
            'variables': [ "playlist_display", "position" ],
            'format':"{0} {1}",
            'justification':"left",
            'scroll':False
            }
        ]
        },
        {
        'name':"Blank",
        'duration':0.25,
        'lines': [
            {
            'name':"top",
            'format':"",
            },
            {
            'name':"bottom",
            'variables': [ "playlist_display", "position" ],
            'format':"{0} {1}",
            'justification':"left",
            'scroll':False
            }
        ]
        },
        {
        'name':"Album",
        'duration':8,
        'hidewhenempty':'any',
        'hidewhenemptyvars': [ "album" ],
        'lines': [
            {
            'name':"top",
            'variables': [ "album" ],
            'format':"{0}",
            'justification':"left",
            'scroll':True
            },
            {
            'name':"bottom",
            'variables': [ "playlist_display", "position" ],
            'format':"{0} {1}",
            'justification':"left",
            'scroll':False
            }
        ]
        },
        {
        'name':"Blank",
        'duration':0.25,
        'lines': [
            {
            'name':"top",
            'format':"",
            },
            {
            'name':"bottom",
            'variables': [ "playlist_display", "position" ],
            'format':"{0} {1}",
            'justification':"left",
            'scroll':False
            }
        ]
        },
        {
        'name':"Title",
        'duration':10,
        'hidewhenempty':'any',
        'hidewhenemptyvars': [ "title" ],
        'lines': [
            {
            'name':"top",
            'variables': [ "title" ],
            'format':"{0}",
            'justification':"left",
            'scroll':True
            },
            {
            'name':"bottom",
            'variables': [ "playlist_display", "position" ],
            'format':"{0} {1}",
            'justification':"left",
            'scroll':False
            }
        ]
        },
        {
        'name':"Blank",
        'duration':0.25,
        'lines': [
            {
            'name':"top",
            'format':"",
            },
            {
            'name':"bottom",
            'variables': [ "playlist_display", "position" ],
            'format':"{0} {1}",
            'justification':"left",
            'scroll':False
            }
        ]
        }
    ]
}

PAGES_Stop = {
    'name':"Stop",
    'pages':
    [
        {
        'name':"Ready",
        'duration':15,
        'lines': [
            {
            'name':"top",
            'variables': [ ],
            'format':"Pas envie de ZIK",
            'justification':"center",
            'scroll':False
            },
            {
            'name':"bottom",
            'variables': [ "current_time_formatted" ],
            'strftime':"%a %b %-d %H:%M",
            'format':"{0}",
            'justification':"center",
            'scroll':False
            }
        ]
        }
    ]
}
