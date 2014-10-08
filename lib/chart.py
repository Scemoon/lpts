# -*- coding:utf-8 -*-

from pychart import theme
from pychart import canvas
from pychart import axis
from pychart import area
from pychart import line_plot
from pychart import line_style
from pychart import fill_style
from pychart import bar_plot
from pychart import category_coord
import sys


class Draw(object):
    def __init__(self, data, file_name, title, author=None, format="ps"):
        #定义图标格式theme.get_options()中定义众多默认值,也可以指定phonto name和 format
        #"d:co:f:", ["format=", "output=", "color=","scale=", "font-family=", "font-size=","line-width=", "debug-level=",
        #"title=", "author=", "creation_date=", "creator=", "bbox="]
        
        args = ["--title=%s" % title, "--color=yes", "--font-size=10", "--output=%s.%s" %(file_name, format), "--debug-level=0"]
        theme.get_options(argv=args)
        #canvas函数，定义canvas名称和格式， 读取theme中定义的环境变量如title
        self.can = canvas.init(fname=file_name+"."+format, format=format)
        self.data = data
                       
    def set_X(self, label, **kwargs):
        ''' set X 
        @param label: X label
        @param tic_list: 指定横纵标标签，type为list, 自定义方法，修改了pychar代码
        @tic_len:The length of tick lines. The value can be negative, 
                     in which case the tick lines are drawn right of (or above) the axis.
        @param format: The format string for tick labels
                  '''
      
        return axis.X(label=label, **kwargs)
    
    def _format(self, val):
        if val/1000 > 1:
            val = val/1000
            unit = "k"
        if val/1000>1:
            val = val/100
            unit = "m"
        return "%s%s" % (val, unit)
 
    def set_Y(self, label, **kwargs):
        ''' set Y 
        @param label: Y label
        @param label_offset: The location for drawing the axis label, 
                        relative to the middle point of the axis.
                        If the value is None, the label is displayed
                        below (or to the left of) of axis at the middle.
        @tic_len:The length of tick lines. The value can be negative, 
                     in which case the tick lines are drawn right of (or above) the axis.
        @param format: The format string for tick labels
        @param offset: The location of the axis. 
                  The value of 0 draws the
                  axis at the left (for the Y axis) or bottom (for the X axis)
                  edge of the drawing area.
        @param tic_interval: '''
        
        #return axis.Y(label=label, label_offset=label_offset, format=format,
         #              tic_len=tic_len, offset=offset, tic_interval=tic_len/6)
        return axis.Y(label=label, format="%.1e", **kwargs)

    def creat_area(self, size, xaxis, yaxis, y_range=(0, None)):
        ar = area.T(size=size, x_coord = category_coord.T(self.data, 0),
                    x_axis=xaxis, y_axis=yaxis, 
                    y_range=y_range, bg_style = fill_style.gray90,
                    x_grid_style=line_style.gray70, border_line_style = line_style.default)
        return ar
    
    def creat_line_plot(self, label, col, tick_mark):
        return line_plot.T(label=label, data=self.data, ycol=col, tick_mark=tick_mark)
    
    def creat_bar_plot(self, label, **kwargs):
        return bar_plot.T(label=label, data=self.data, **kwargs)
    
    def area_add_plot(self, ar, plot_list):
        #ar.add_plot(plot_list)
        #ar.__plot.extend(plot_list)
        ar.add_plot(*plot_list)
        
    def draws(self, ar):
        ar.draw(self.can)
        canvas._exit()




