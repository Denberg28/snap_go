from snap_go.vision import Box, select_subject

def test_none(): assert select_subject([],640,480) is None
def test_filters_class(): assert select_subject([Box(0,0,100,100,.9,1)],640,480) is None
def test_filters_conf(): assert select_subject([Box(0,0,100,100,.2,0)],640,480) is None
def test_selects_weighted():
    d=select_subject([Box(0,0,10,10,.99,0),Box(100,100,300,300,.8,0)],400,400); assert round(d.cx,2)==.5
