from enum import Enum

class Level(Enum):
    e = 3
    w = 2
    i = 1
    v = 0

class Log:
    level = Level.v
    tag = ''

    @staticmethod
    def v(tag, msg):
        if Log.level.value <= Level.v.value:
            if Log.tag == '' or Log.tag == tag:
                print('[V][{}] {}'.format(tag, msg))    
    @staticmethod    
    def i(tag, msg):
        if Log.level.value <= Level.i.value:
            if Log.tag == '' or Log.tag == tag:
                print('[I][{}] {}'.format(tag, msg))
    @staticmethod    
    def w(tag, msg):
        if Log.level.value <= Level.w.value:
           if Log.tag == '' or Log.tag == tag:
                print('[S][{}] {}'.format(tag, msg))
    @staticmethod 
    def e(tag, msg):
        if Log.level.value <= Level.e.value:
           if Log.tag == '' or Log.tag == tag:
                print('[E][{}] {}'.format(tag, msg))