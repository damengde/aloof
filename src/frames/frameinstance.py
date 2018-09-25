# -*- coding: utf-8 -*

class FrameElement:
    '''
    Class that implements a frame element
    '''
    def __init__(self):
        self.role = None
        self.entity = None

    def __str__(self):
        return '{0}: {1}'.format(self.role, self.entity)

class FrameInstance:
    '''
    Class that implements a frame
    '''
    def __init__(self, _id):
        self.id = _id
        self.frame_type = None
        self.frame_elements = []

    def __str__(self):
        return '''Frame Instance: {0}
                Frame type: {1}
                Frame elements ({2}):
                {3}'''.format(self.id,
                              self.frame_type,
                              len(self.frame_elements),
                              '\n'.join(['\t{0}'.format(str(fe)) for fe in self.frame_elements]))