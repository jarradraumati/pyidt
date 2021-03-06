'''@package pyidt.py

Author: Jarrad Raumati
Date 5/11/2013

Description:
This module facilitates the manipulation of classes and objects within
GE Proficy HMI/SCADA Cimplicity v 8.1. 

'''

# Import excel modules.
from mmap import mmap,ACCESS_READ
from xlrd import open_workbook

# Regular expressions
import re

# Import system modules
import os
import sys

# Import testing module
import unittest

# Import iterator tools.
import itertools

# ------------------------------------------------------------------------------
# CONSTANTS
# ------------------------------------------------------------------------------

DEBUG_MODE = True
UNIT_TEST = False

OBJECT = 1
ATTRIB = 2
ROUTING = 3

# ------------------------------------------------------------------------------
# EXCEPTIONS
# ------------------------------------------------------------------------------

class IDTFileObjectNone(Exception):
    ''' Thrown if the idt file object could not be initialised. Commonly occurs
        when an incorrect filename is given.
    '''
    pass


# ------------------------------------------------------------------------------
# MISC FUNCTIONS
# ------------------------------------------------------------------------------

def debug(message):
    ''' Prints debugging messages if debug mode is set to true'''
    if DEBUG_MODE:
        print message


# ------------------------------------------------------------------------------
# DEPRECATED FUNCTIONS
# ------------------------------------------------------------------------------

def idt_create_object(output_file):
    csv_file_object = csv.reader(open('', 'rU'))
    output = open(output_file, 'w')
    
    csv_file_object.next()

    i = 0
    output.write("|-* IDT file generated by IDTPOP utility v1.0\n\
* RECORD: OBJECT Objects\n\
*\n\
*   0 OBJECT_ID                        Object ID\n\
*   1 view_id                          Mixed Case Object ID\n\
*   2 CLASS_ID                         Class ID\n\
*   3 description                      Description\n\
* \n")

    for row in csv_file_object:
        for cell in row[:4]:
            output.write(cell)
            i += 1
            if i < 7:
                output.write('|')
                i += 1
            if i == 7:
                output.write('\n')
                i = 0
    output.close()
            
def idt_create_object_attrib(output_file):
    csv_file_object = csv.reader(open('', 'rU'))
    output = open(output_file, 'w')
    
    header = csv_file_object.next()

    i = 4
    
    output.write("|-* IDT file generated by IDTPOP utility v1.0\n\
* RECORD: OBJECT_ATTRIB Object Attributes\n\
*\n\
*   0 OBJECT_ID                        Object ID\n\
*   1 attr_id                          Attribute ID\n\
*   2 value                            Value\n\
* \n")

    for row in csv_file_object:
        for cell in row[4:8]:
            output.write(row[0] + '|' + header[i] + '|' + cell + '\n')
            i += 1
        i = 4
    output.close()

def idt_create_object_routing (output_file):
    csv_file_object = csv.reader(open('', 'rU'))
    output = open(output_file, 'w')
    
    csv_file_object.next()

    routing = ["OPEN", "SYSMGR", "USER"]
    
    output.write("|-* IDT file generated by IDTPOP utility v1.0\n\
* RECORD: OBJECT_ROUTING Object Alarm Routing\n\
*\n\
*   0 OBJECT_ID                        Object ID\n\
*   1 role_id                          Role ID\n\
* \n")

    for row in csv_file_object:
        for item in routing:
            output.write(row[0] + '|' + item + '\n')
    output.close()


# ------------------------------------------------------------------------------
# WORKBOOK CLASSES
# ------------------------------------------------------------------------------
    
class Workbook(object):
    ''' Class for containing the excel workbook. '''

    def __init__(self, workbook_name):
        ''' Initialises the excel workbook for use with a name. '''
        self.workbook_name = workbook_name
        self.wb = self.open_()

    def open_(self):
        ''' Creates a new excel workbook to store Cimplicity data.
        Returns the new workbook.
        '''
        wb = open_workbook(self.workbook_name)

        return wb

    def print_all(self):
    	''' Prints the contents of an excel workbook. '''
    	for s in self.wb.sheets():
    	    print 'Sheet:',s.name
    	    for row in range(s.nrows):
    	        values = []
    	        for col in range(s.ncols):
    	            values.append(s.cell(row,col).value)
    	        print ','.join(values)

    def get_column_names(self, sheet_name):
        ''' Returns a list of unicode strings of the column names. The name of
            the column is assumed to be in the first row (position 0).
        '''
        s = self.wb.sheet_by_name(sheet_name)
        column_names = []
        for col in range(s.ncols):
            column_names.append(s.cell(0,col).value)
        return column_names


# ------------------------------------------------------------------------------
# IDT CLASSES
# ------------------------------------------------------------------------------

class IDT(object):
    ''' Class for containing the IDT datafile. '''
    object_list = []

    def __init__(self, file_name, idt_type):
        ''' Initialises the IDT datafile object using a given file name. '''
        self.file_name = file_name
        self.file = self.open_file()
        self.header = self._populate_header()
        self.objects = self._populate_raw_object_list()

        # Create IDT objects with variable values and append them to the object
        # list.
        for object_raw_data in self.objects:
            if idt_type == OBJECT:
                self._get_object_list().append(IDTObject(self._obtain_variables(), object_raw_data))

            elif idt_type == ATTRIB:
                self._add_attrib(self._obtain_variables(), object_raw_data)

            elif idt_type == ROUTING:
                self._add_routing(self._obtain_variables(), object_raw_data)

        if self.file is None:
            raise IDTFileObjectNone("Could not create IDT Object due to \
missing file object reference.")

    @classmethod
    def _get_object_list(cls):
        ''' Returns the list containing idt objects. '''
        return cls.object_list

    def _populate_header(self):
        ''' Returns the header of the idt file. '''
        header = []

        for line in self.file:
            if line[0] == '|' or line[0] == '*':
                item = line.rstrip()
                header.append(item)

        # Reset file to beginning.
        self.file.seek(0)

        return header

    def _populate_raw_object_list(self):
        ''' Obtains the objects from the idt file and appends them to the 
            objects list.
        '''
        objects = []

        # Regular Expression for object.
        re1 = '/^[\w]$/'
        rg = re.compile(re1,re.IGNORECASE|re.DOTALL)

        # Step over the file header and just retrieve the object data.
        for line in self.file:
            if line[0] == '|' or line[0] == '*':
                pass
            else:
                item = line.rstrip()
                objects.append(item.split('|'))

        # Reset file to beginning.
        self.file.seek(0)

        return objects

    def _obtain_variables(self):
        ''' Returns a list of an IDT files object variables. '''
        header = self.get_header()

        # Remove additional lines not containing object variable information.
        header = header[3:-1]

        variables = []

        # Strip astrisk and create 3 element list.
        for item in header:
            item = item.replace("*", "")
            item = item.strip()
            item = item.split()
            word = ' '.join(item[2:])
            result = item[0:2]
            result.append(word)

            variable = IDTObjectVariable(result)

            variables.append(variable)

        return variables

    def _add_attrib(self, variables, object_raw_data):
        ''' Imports information from attrib idt file. '''

        # Create new variable objects to add to idt object.
        item = (object_raw_data[1], object_raw_data[2])
        variables[0].set_value(object_raw_data[0])
        variables[1].set_value(item)

        for object_ in self._get_object_list():
            if object_.get_variable_value("OBJECT_ID") == variables[0].get_value():
                object_.add_variable(variables[1])

    def _add_routing(self, variables, object_raw_data):
        ''' Imports information from the routing idt file. '''

        item = object_raw_data[1]
        variables[0].set_value(object_raw_data[0])
        variables[1].set_value(item)

        for object_ in self._get_object_list():
            if object_.get_variable_value("OBJECT_ID") == variables[0].get_value():
                object_.add_variable(variables[1])

    def open_file(self):
        ''' Opens an existing idt file. '''        
        idt_file = None

        try:
            idt_file = open(self.file_name, "rb")
        except IOError:
            print "Error: Cannot open " + self.file_name
        else:
            return idt_file

    def close_file(self):
        ''' Closes the open idt file. '''
        self.file.close()

    def get_file_name(self):
        ''' Return a string containing the idt file name. '''
        return self.file_name

    def get_header(self):
        ''' Retruns a list containing the lines of the file header. '''
        return self.header

    def get_objects(self):
        ''' Returns a list of the objects within the idt file. '''
        return self.object_list

class IDTObjectVariable(object):
    ''' Class for IDT object variable. '''

    def __init__(self, varaible_info):
        ''' Initialises the IDTObjectVariable object with an index, id and
        variable description. '''
        self.index = varaible_info[0]
        self.id = varaible_info[1]
        self.description = varaible_info[2]

        self.value = None

    def __repr__(self):
        ''' Object represntation with the form IDTObjectVariable(id). '''
        return "%s=%s" % (self.id, self.value)

    def __str__(self):
        ''' Allows for the IDTObjectVariable class information to be
            printed.
        '''
        return "%s %s %s" % (self.index, self.id, self.description)

    def set_value(self, value):
        ''' Sets the value of the variable. '''
        self.value = value

    def get_value(self):
        ''' Return the value of the variable. '''
        return self.value

    def get_index(self):
        ''' Return the variable index. '''
        return self.index

    def get_id(self):
        ''' Return the variable id. '''
        return self.id

    def get_description(self):
        ''' Return the varaible description. '''
        return self.description


class IDTObject(object):
    ''' Class for and IDT object within an IDT file. '''

    def __init__(self, variables, raw_object_data):
        self.variables = self._populate_variable_value(raw_object_data, variables)

    def __repr__(self):
        return "IDTObject(%s)" % self.get_variable_value("OBJECT_ID")

    def _populate_variable_value(self, raw_object_data, variables):
        ''' Appends the variables with their values to the object variable
        list.
        '''
        output = []

        it = iter(variables)

        for element in raw_object_data:
            item = it.next()
            item.set_value(element)
            output.append(item)

        return output

    def get_variable_value(self, variable_id):
        ''' Returns an IDTObjectVariable object value given the variable id. '''
        for variable in self.variables:
            if variable.get_id() == variable_id:
                return variable.get_value()
            else:
                return None

    def add_variable(self, variable):
        ''' Adds a new variable to the object. '''
        self.variables.append(variable)

    def get_variables(self):
        ''' Return a list of variable objects. '''
        return self.variables

    def get_object_info(self):
        ''' Return the list of variables and their values. '''
        return self.variables


# ------------------------------------------------------------------------------
# TEST ENVIRONMENT
# ------------------------------------------------------------------------------

def main():
    wb = Workbook('cimplicity_idt.xlsx')
    idt_object_file_name = 'object.idt'
    idt_attrib_file_name = 'object_attrib.idt'
    idt_routing_file_name = 'object_routing.idt'

    try:
        idt_list = []

        idt_object = IDT(idt_object_file_name, OBJECT)
        idt_list.append(idt_object)
        idt_attrib = IDT(idt_attrib_file_name, ATTRIB)
        idt_list.append(idt_attrib)
        idt_routing = IDT(idt_routing_file_name, ROUTING)
        idt_list.append(idt_routing)

    except IDTFileObjectNone:
        print "did not work..."
    
    else:
        # for idt in idt_list:
        #     print '\nPrinting imported IDT data from %s...\n' % idt.get_file_name()
        #     n = 0
        #     for object_ in idt .get_objects():
        #         print object_
        #         for variable in object_.get_object_info():
        #             print '\t' + variable.get_id() + ': ' + variable.get_value()
        #         n += 1
        #         
        for element in idt_object._get_object_list():
            print element.get_variables()

        # print '\nNumber of imported objects: %d' % n
        idt_object.close_file()
        idt_attrib.close_file()
        idt_routing.close_file()

if __name__ == '__main__':
    if UNIT_TEST:
        unittest.main()
    else:
        main()

