from mimetypes import init


def init1():
    
    global Y1
    global Y2
    global iterate
    Y1 = []
    Y2 = [] 
    i = 0
    iterate = 4500
    no_of_states = 20
    no_of_actions = 15 
    for i in range(no_of_actions):
        a = (1 / no_of_actions) * (i+1)
        Y1.append(a)

    print("Actions1:", Y1)
    for i in reversed(Y1):
        Y2.append(i)
    print("Actions2:", Y2)

    for i in range((no_of_actions-1)):
        Y2[i]=Y2[i+1]

    Y2[(no_of_actions-1)] = 0.0
    
init1()