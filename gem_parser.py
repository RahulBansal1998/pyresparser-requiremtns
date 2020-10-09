import os
import sys
from pyresparser import ResumeParser


def resume_data(filename):
    if not filename.endswith('.pdf'):
        if filename.endswith('doc') or filename.endswith('docx'):
            filename = doc_to_pdf(filename)
        else:
            print("Only 'pdf', 'doc' and 'docx' file format supported")
            sys.exit(1)
    Resume_Data = ResumeParser(filename).get_extracted_data()

    return Resume_Data


def doc_to_pdf(filename):
    os.system('soffice --headless --convert-to pdf %s'%(filename))
    filename = filename.split('.')[0]
    filename = filename + ".pdf"
    return filename

    

               





    




    



    
  