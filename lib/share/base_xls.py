# -*- coding:utf-8 -*-
#

import xlwt

border_line_map = {
    # Text values for these borders attributes:
    # left, right, top, bottom and diag
    'no_line':  0x00,
    'thin':     0x01,
    'medium':   0x02,
    'dashed':   0x03,
    'dotted':   0x04,
    'thick':    0x05,
    'double':   0x06,
    'hair':     0x07,
    'medium_dashed':                0x08,
    'thin_dash_dotted':             0x09,
    'medium_dash_dotted':           0x0a,
    'thin_dash_dot_dotted':         0x0b,
    'medium_dash_dot_dotted':       0x0c,
    'slanted_medium_dash_dotted':   0x0d,
    }

charset_map = {
    # Text values for font.charset
    'ansi_latin':           0x00,
    'sys_default':          0x01,
    'symbol':               0x02,
    'apple_roman':          0x4d,
    'ansi_jap_shift_jis':   0x80,
    'ansi_kor_hangul':      0x81,
    'ansi_kor_johab':       0x82,
    'ansi_chinese_gbk':     0x86,
    'ansi_chinese_big5':    0x88,
    'ansi_greek':           0xa1,
    'ansi_turkish':         0xa2,
    'ansi_vietnamese':      0xa3,
    'ansi_hebrew':          0xb1,
    'ansi_arabic':          0xb2,
    'ansi_baltic':          0xba,
    'ansi_cyrillic':        0xcc,
    'ansi_thai':            0xde,
    'ansi_latin_ii':        0xee,
    'oem_latin_i':          0xff,
    }


_colour_map_text = """\
aqua 0x31
black 0x08
blue 0x0C
blue_gray 0x36
bright_green 0x0B
brown 0x3C
coral 0x1D
cyan_ega 0x0F
dark_blue 0x12
dark_blue_ega 0x12
dark_green 0x3A
dark_green_ega 0x11
dark_purple 0x1C
dark_red 0x10
dark_red_ega 0x10
dark_teal 0x38
dark_yellow 0x13
gold 0x33
gray_ega 0x17
gray25 0x16
gray40 0x37
gray50 0x17
gray80 0x3F
green 0x11
ice_blue 0x1F
indigo 0x3E
ivory 0x1A
lavender 0x2E
light_blue 0x30
light_green 0x2A
light_orange 0x34
light_turquoise 0x29
light_yellow 0x2B
lime 0x32
magenta_ega 0x0E
ocean_blue 0x1E
olive_ega 0x13
olive_green 0x3B
orange 0x35
pale_blue 0x2C
periwinkle 0x18
pink 0x0E
plum 0x3D
purple_ega 0x14
red 0x0A
rose 0x2D
sea_green 0x39
silver_ega 0x16
sky_blue 0x28
tan 0x2F
teal 0x15
teal_ega 0x15
turquoise 0x0F
violet 0x14
white 0x09
yellow 0x0D"""

pattern_map = {
    # Text values for pattern.pattern
    # xlwt/doc/pattern_examples.xls showcases all of these patterns.
    'no_fill':              0,
    'none':                 0,
    'solid':                1,
    'solid_fill':           1,
    'solid_pattern':        1,
    'fine_dots':            2,
    'alt_bars':             3,
    'sparse_dots':          4,
    'thick_horz_bands':     5,
    'thick_vert_bands':     6,
    'thick_backward_diag':  7,
    'thick_forward_diag':   8,
    'big_spots':            9,
    'bricks':               10,
    'thin_horz_bands':      11,
    'thin_vert_bands':      12,
    'thin_backward_diag':   13,
    'thin_forward_diag':    14,
    'squares':              15,
    'diamonds':             16,
    }


class Write:
    '''
    '''
    def __init__(self, encoding='utf-8'):
        self.book = xlwt.Workbook(encoding)
    
    def add_sheet(self, name, cell_overwrite_ok=True):
        '''添加sheet
        @return: 返回sheet对象
        '''
        return self.book.add_sheet(name)
    
    
    def write_merge(self, sheet, rowmin, rowmax, colmin, colmax, value, style):
        '''
        '''
        sheet.write_merge(rowmin, rowmax, colmin, colmax, value, style)
    
    def write(self, sheet, row, col, value, style):
        '''
        '''
        sheet.write(row, col, value, style)
    
    
    def row_object(self, sheet, row):
        ''' 
            row对象
        '''
        return sheet.row(row)
        
    def row_write(self, rowObject, col, value, style):
        
        rowOjbect.write(col, value, style)
    
    def save_xls(self, file):
        '''保存execl文件
        '''
        self.book.save(file)
        
    
class Read:
    '''
    '''
    def __init__(self):
        pass
        


def font(italic=False, bold=False, struck_out=False, outline=False, 
         shadow=False, colour=0x7FFF, escapement=0x00, underline=0x00, 
         family=0x00, height=0x00C8, weight=0x0190, charset=0x01, name='Arial'):
        
    '''设置字体
        @param italic:斜体
        @param bold: 粗体
        @param struck_out: 
        @param outline: 字体轮廓
        @param shadow: 字体阴影 
        @param colour: 颜色
                    查看_colour_map_text
        @param escapement: 上标或下标
            None: 0x00
                        上标： 0x01
                        下标： 0x02
        @param underline: 下划线 
             None：0x00
                         单线：0x01
                         单线_ACC: 0x21
                         双线：0x02
                         双线_ACC: 0x22
        @param family: 
            FAMILY_NONE     :0x00
            FAMILY_ROMAN    :0x01
            FAMILY_SWISS    :0x02
            FAMILY_MODERN   :0x03
            FAMILY_SCRIPT   :0x04
            FAMILY_DECORATIVE :0x05
        @param height:  高度
            size十六进制表示方法： size*20,然后转换成十六进制，默认0x00C8(10) 
        @param weight: 字体宽度
        @param charset: 编码集
                        参照charset_map
        @param name: 字体
                    参考：
                        宋体    SimSun
                        黑体    SimHei
                        微软雅黑    Microsoft YaHei
                        新宋体    NSimSun
                        仿宋    FangSong
                        楷体    KaiTi
                        隶书    LiSu
                        幼圆    YouYuan
            'Times New Roman'
            'Arial'
    '''
    font = xlwt.Font()
    font.italic = italic
    font.bold = bold
    font.struck_out = struck_out
    font.outline = outline
    font.shadow = shadow
    font.colour_index = colour
    font.escapement = escapement
    font.underline = underline
    font.family = family
    font.height = height
    font._weight = weight
    font.charset = charset
    font.name = name
        
    return font

def alignment(horz=0x01, vert=0x01, dire=0x01, inde=0):
    '''
        @param horz: 横向对齐
            None: 0x00
                        左对齐： 0x01
                        居中：    0x02
                        右对齐： 0x03
                        填充：    0x04
        @param vert: 纵向对齐
                        置顶:    0x00
                        居中：  0x01
                        置底：  0x02
        @param dire: 文字书写方向
            None: 0x00
                       从左向右：    0x01
                       从右向左：    0x02
        @param inde: 缩进
    '''
    aligt = xlwt.Alignment()
    aligt.horz = horz
    aligt.vert = vert
    aligt.dire = dire
    aligt.inde = inde
        
    return aligt
    

def borders(line=0x00, colour=0x40):
    '''
        @param line: cell线条格式
                    参照borders_map
        @param colour: 线条颜色
                    查看_colour_map_text
        '''
        
    bds = xlwt.Borders()
    bds.left   = line
    bds.right  = line
    bds.top    = line
    bds.bottom = line
    bds.diag   = line

    bds.left_colour   = colour
    bds.right_colour  = colour
    bds.top_colour    = colour
    bds.bottom_colour = colour
    bds.diag_colour   = colour
        
    return bds
    
def pattern(solid_pattern=0x00, fore_colour=0x40, back_colour=0x41):
    '''
        @param solid_pattern: 开启颜色背景：
            关闭：0x00
            开启:0x01
        @param fore_colour: 前景色
        @param back_colour: 后景色
        '''
    pn = xlwt.Pattern()
    pn.pattern = solid_pattern
    pn.pattern_fore_colour = fore_colour
    pn.pattern_back_colour = back_colour
        
    return pn
    

def protection(cell_locked=1, formula_hidden=0):
    '''
        @param cell_locked: 锁定
        @param formula_hidden: formula_hidden
        '''
    pron = xlwt.Protection()
    pron.cell_locked = cell_locked
    pron.formula_hidden = formula_hidden
        
    return pron