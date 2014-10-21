# -*- coding:utf-8 -*-
#

from share import base_xls
import xlwt
from lpt.lib.share import utils


def cell_style():
    '''
    '''
    style = xlwt.XFStyle()
    style.font = base_xls.font(bold=True, colour=0x08)
    style.alignment = base_xls.alignment(horz=0x01)
    style.borders = base_xls.borders(line=0x01)
    style.pattern = base_xls.pattern(solid_pattern=0x01, fore_colour=0x2B)
    return style

def info_style():
    '''
    '''
    style = xlwt.XFStyle()
    style.font = base_xls.font(bold=True, colour=0x08)
    style.alignment = base_xls.alignment()
    style.alignment.wrap = 1
    style.borders = base_xls.borders(line=0x01)
    style.pattern = base_xls.pattern(solid_pattern=0x00, fore_colour=0x2A)
    return style

def title_style():
    '''
    '''
    style = xlwt.XFStyle()
    style.font = base_xls.font(bold=True, colour=0x0A)
    style.alignment = base_xls.alignment(horz=0x02)
    style.borders = base_xls.borders(line=0x01)
    style.pattern = base_xls.pattern(solid_pattern=0x01, fore_colour=0x1F)
    return style

def description_style():
    style = xlwt.XFStyle()
    style.font = base_xls.font(bold=True, colour=0x11)
    style.alignment = base_xls.alignment(inde=0)
    style.alignment.wrap = 1
    style.borders = base_xls.borders(line=0x01)
    style.pattern = base_xls.pattern(solid_pattern=0x00, fore_colour=0x16)
    return style

def data_title_style():
    style = xlwt.XFStyle()
    style.font = base_xls.font(bold=True, colour=0x0C)
    style.alignment = base_xls.alignment()
    style.borders = base_xls.borders(line=0x01)
    style.pattern = base_xls.pattern(solid_pattern=0x01, fore_colour=0x29)
    return style

def data_style():
    style = xlwt.XFStyle()
    style.font = base_xls.font(bold=True, colour=0x08)
    style.alignment = base_xls.alignment()
    style.borders = base_xls.borders(line=0x01)
    style.pattern = base_xls.pattern(solid_pattern=0x00, fore_colour=0x2A)
    return style

def data_seq_style(font_colour=0x08):
    style = xlwt.XFStyle()
    style.font = base_xls.font(bold=True, colour=font_colour)
    style.alignment = base_xls.alignment()
    style.borders = base_xls.borders(line=0x01)
    style.pattern = base_xls.pattern(solid_pattern=0x01, fore_colour=0x2A)
    return style

def section_title_style():
    style = xlwt.XFStyle()
    style.font = base_xls.font(bold=True, colour=0x30, height=0x00EE)
    style.alignment = base_xls.alignment()
    style.borders = base_xls.borders(line=0x01)
    style.pattern = base_xls.pattern(solid_pattern=0x00, fore_colour=0x2A)
    return style


class Wxls(base_xls.Write):
    '''
    '''
    def __init__(self):
        #super(Wxls, self).__init__()
        base_xls.Write.__init__(self)
    
    def sheet(self, tool):
        '''创建tool sheet'''
        return self.add_sheet(tool)
    
    def save(self, result_file):
        '''保存文件'''
        self.save_xls(result_file)
    
    def title(self, sheet, title, rowmin=2, rowmax=3, colmin=2, colmax=5):
        ''' 写入标题'''
        self.write_merge(sheet, rowmin, rowmax, colmin, colmax, title, title_style())
        
    def section_title(self, sheet, section_title, row, col=0):
        '''写入章节标题'''
        self.write(sheet, row, col, section_title, section_title_style())
        
    def lmbench_des(self, sheet, section_des, row, colmin, colmax):
         self.write_merge(sheet, row, row, colmin, colmax, section_des, cell_style())
        
    def write_cell(self, sheet, value, row, col):
        '''写入单个cell'''
        self.write(sheet, row, col, value, cell_style())
        if len(utils.to_unicode(value)) * 367  > sheet.col(col).width:
            sheet.col(col).width = len(utils.to_unicode(value)) * 367
        
    def description(self, sheet, description, row, colmin=1, colmax=5):
        '''
            写入描述性语句
        '''
        self.write_merge(sheet, row, row, colmin, colmax, description, description_style())
        sheet.row(row).height_mismatch=True
        
    def parameters(self, sheet, params, row, colmin, colmax):
        self.write_merge(sheet, row, row, colmin, colmax, params, data_style())
        sheet.row(row).height_mismatch=True
        
    def data_title(self, sheet, data_title_list, row, col_start_index=1):
        '''写入数据名称
        @param data_title_list: 第一行为标题，这里输入的是一个list
        '''
        if data_title_list and isinstance(data_title_list, list):
            index = col_start_index
            for data_title in data_title_list:
                self.write(sheet, row, index, data_title, data_title_style())
                if len(utils.to_unicode(data_title)) * 367  > sheet.col(index).width:
                    sheet.col(index).width = len(utils.to_unicode(data_title)) * 367
                index += 1
                
    def data_seq(self, sheet, seq, row, col=1):
        '''写入测试次数,判断seq是否等于Average,如果为整型，将以整型写入，如果为字符，将以字符写入'''
        try:
            seq = int(seq)
            font_colour = 0x08
        except Exception:
            if seq == "Average":
                font_colour = 0x0A
            else:
                font_colour = 0x08
        
        self.write(sheet, row, col, seq, data_seq_style(font_colour=font_colour))
        if len(utils.to_unicode(str(seq))) * 367  > sheet.col(col).width:
            sheet.col(col).width = len(utils.to_unicode(str(seq))) * 367
        
    def data(self, sheet, data_list, row, col_start_index=1):
        '''写入数据 '''
        if data_list and isinstance(data_list, list):
            index = col_start_index
            for data in data_list:
                self.write(sheet, row, index, data, data_style())
                index += 1
        
    def info(self, sheet, value, row, col):
        '''写入单个cell'''
        self.write(sheet, row, col, value, info_style())
        sheet.col(col).width = 16000
                
    def insert_img(self, sheet, img, row, col):
        sheet.insert_bitmap(img, row, col, 0, 2, scale_x=1, scale_y=1)
