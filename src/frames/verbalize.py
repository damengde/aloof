# -*- coding: utf-8 -*

from os.path import join, dirname

def verbalize_frame(frame_type, frame_elements, netlemma):
    ''' Verbalize a frame instance '''
    text_list = []
    
    for role, filler in frame_elements:
        if filler in netlemma:
            text_list.append("'%s' is the '%s'" % (netlemma[filler], role))

    return "In frame %s " % frame_type.upper() + ' and '.join(text_list)