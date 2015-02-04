from thought_lounge import app
from thought_lounge.mail import digest, reminder
import sys

if __name__ == '__main__':
    task = sys.argv[1]
    print('starting task {0}...'.format(task))

    with app.app_context():
        if task == 'digest':
            notifications = int(sys.argv[2])
            digest(notifications)
        elif task == 'reminder':
            reminder()
        else:
            print('Task {0} not found.'.format(task))

    print('...finished task {0}'.format(task))
