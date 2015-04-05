import datetime, requests

users = [
    {
        'email': 'ludwig@uvienna.edu',
        'password': 'BeetleinaBox',
        'firstName': 'Ludwig',
        'lastName': 'Wittgenstein',
        'bio': 'I\'ve solved philosophy!',
        'notifications': 4,
    },
    {
        'email': 'luce@ubrussels.edu',
        'password': 'mimesis',
        'firstName': 'Luce',
        'lastName': 'Irigaray',
        'bio': 'E != mc^2!',
        'notifications': 2,
    },
    {
        'email': 'richard@caltech.fake.edu',
        'password': 'diagrams',
        'firstName': 'Richard',
        'lastName': 'Feynman',
        'bio': 'Surely I\'m joking!',
        'notifications': 1,
    },
    {
        'email': 'noam@mit.fake.edu',
        'password': 'structures',
        'firstName': 'Noam',
        'lastName': 'Chomsky',
        'bio': 'Colorless green ideas sleep furiously...',
        'notifications': 0,
    }
]

lounges = [
    {
        'dateTime': datetime.datetime(2015, 2, 25, 3, 00).isoformat(),
        'isReserved': False,
        'community': 'UC Berkeley',
    },
    {
        'dateTime': datetime.datetime(2015, 2, 20, 3, 00).isoformat(),
        'isReserved': False,
        'community': 'UC Berkeley',
    },
    {
        'dateTime': datetime.datetime(2015, 2, 10, 3, 00).isoformat(),
        'isReserved': True,
        'location': 'Main Stacks B2',
        'community': 'UC Berkeley',
    },
    {
        'dateTime': datetime.datetime(2015, 1, 1, 4, 00).isoformat(),
        'isReserved': True,
        'topic': 'lurk late. We',
        'summary': 'strike straight. We',
        'location': 'Main Stacks C3',
        'community': 'UC Berkeley',
    },
    {
        'dateTime': datetime.datetime(2014, 12, 25, 3, 00).isoformat(),
        'isReserved': True,
        'topic': 'sing sin. We',
        'summary': 'thin gin. We',
        'location': 'Haas 2',
        'community': 'UC Berkeley',
    },
    {
        'dateTime': datetime.datetime(2014, 12, 12, 5, 00).isoformat(),
        'isReserved': True,
        'topic': 'Jazz June. We',
        'summary': 'die soon.',
        'location': 'Haas 3',
        'community': 'UC Berkeley',
    },
    {
        'dateTime': datetime.datetime(2014, 11, 25, 6, 00).isoformat(),
        'isReserved': True,
        'topic': 'Knock-kneed, coughing like hags, we cursed through sludge',
        'summary': 'Bent double, like old beggars under sacks',
        'location': 'Haas 4',
        'community': 'UC Berkeley',
    }
]

user_lounges = [
    {
        'topic': 'Tonight I can write the saddest lines.',
        'summary': 'Write, for example, \'The night is shattered and the blue stars shiver in the distance.\'',
        'showedUp': True,
        'isHost': True
    },
    {
        'topic': 'I saw the best minds of my generation destroyed by madness.',
        'summary': 'Starving hysterical naked, dragging themselves through the negro streets at dawn looking for an angry fix.',
        'showedUp': True,
        'isHost': True
    },
    {
        'topic': 'Moloch!',
        'summary': 'Solitude! Filth! Ugliness! Ashcans and unobtainable dollars! Children screaming under the stairways! Boys sobbing in armies!  Old men weeping in the parks!',
        'showedUp': True,
        'isHost': True
    },
    {
        'topic': 'Timeless',
        'summary': 'ly this (merely and whose not numerable leaves are fall i ng)he',
        'showedUp': True,
        'isHost': True
    },
    {
        'topic': 'Time\'s winged chariot hurrying near',
        'summary': 'Let us roll all our strength and all Our sweetness up into one ball,',
        'showedUp': True,
        'isHost': False
    },
    {
        'topic': 'angelheaded hipsters burning for the ancient heavenly',
        'summary': 'connection to the starry dynamo in the machinery of night',
        'showedUp': True,
        'isHost': False
    },
    {
        'topic': 'who poverty and tatters and hollow-eyed and high sat up smoking',
        'summary': 'in the supernatural darkness of cold-water flats floating',
        'showedUp': True,
        'isHost': False
    },
    {
        'showedUp': False,
        'isHost': False
    }
]

pictures = [
    {
        'bytes': requests.get('http://api.randomuser.me/portraits/thumb/women/1.jpg').content,
        'href': 'http://api.randomuser.me/?seed=0'
    },
    {
        'bytes': requests.get('http://api.randomuser.me/portraits/thumb/men/1.jpg').content,
        'href': 'http://api.randomuser.me/?seed=1'
    },
    {
        'bytes': requests.get('http://api.randomuser.me/portraits/thumb/women/2.jpg').content,
        'href': 'http://api.randomuser.me/?seed=2'
    },
    {
        'bytes': requests.get('http://api.randomuser.me/portraits/thumb/men/2.jpg').content,
        'href': 'http://api.randomuser.me/?seed=3'
    }
]

host_applications = [
    {
        'application': 'Make me a host!',
        'dateTime': datetime.datetime(2014, 12, 25, 19, 00).isoformat(),
    },
    {
        'application': 'Please make me a host!',
        'dateTime': datetime.datetime(2015, 12, 25, 19, 00).isoformat(),
    },
]
