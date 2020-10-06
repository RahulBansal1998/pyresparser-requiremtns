# -*- coding: utf-8 -*-
import subprocess
import time
import os
from pyresparser import ResumeParser      



def Document_to_pdf(filename):
    '''
    :param : filename to be converted to pdf 
     converting to pdf when user entered doc and docx 
    '''
    if filename.endswith('.doc') or filename.endswith('.docx'): 
        subprocess.call(['soffice', '--headless', '--convert-to', 'pdf', filename])                     #calling subprocess
        time.sleep(4)
        filename = filename.split('/')[-1]
        filename = filename.split('.')[-2]
        filename = filename + ".pdf"

    return filename
  
def dataframe_for_Directory(filename):
    '''
    :param:json parameter
     creating dataframe for writing to the google sheet 
    '''
    if filename.endswith('.pdf'):
        Resume_Data = ResumeParser(filename).get_extracted_data()                                                   #call to resume_parser file in pyresparser  
    
    return Resume_Data


def doc_to_pdf(filename):
    if filename.endswith('.doc') or filename.endswith('.docx'):
        filename = Document_to_pdf(filename)

    return filename

def main(filename): 
    ''' main function getting arguments
        from gem_resume_parser.py file 
    '''
    filename = doc_to_pdf(filename)
    Resume_Data = dataframe_for_Directory(filename)
    return Resume_Data


    

               





    




    



    
  