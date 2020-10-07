import io
import os
import re
import nltk
import pandas as pd
import subprocess
import docx2txt
from datetime import datetime
from dateutil import relativedelta
from . import constants as cs
from pdfminer.converter import TextConverter
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFSyntaxError
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
from collections import Counter
import csv
import sys
sys.path.append('../drive_cli')
sys.path.append('..')
from drive_cli import actions
from nltk.corpus import names 
import nltk 
import random

# def resume_link(filename,arguments_data):
#     ''' 
#     function for getting resume_link 
#     '''
#     filename = filename.split('/')[-1]
#     filename1 = filename.split('.')[0] + ".doc"
#     filename2 = filename.split('.')[0] + ".docx"
#     default_string = "https://drive.google.com/file/d/"
#     doc_list = os.listdir(arguments_data["Directory"])
#     actions.lists_out(arguments_data)
#     df = pd.read_csv(arguments_data["drive_tablepyresparser"])
#     id = df.loc[(df['Name'] == filename) | (df['Name'] == filename1) | (df['Name'] == filename2) ,'File ID'].values[0]
#     file_link = default_string + id
#     return file_link




def extract_text_from_pdf(pdf_path):
    '''
    Helper function to extract the plain text from .pdf files

    :param pdf_path: path to PDF file to be extracted (remote or local)
    :return: iterator of string of extracted text
    '''
    # https://www.blog.pythonlibrary.org/2018/05/03/exporting-data-from-pdfs-with-python/
    if not isinstance(pdf_path, io.BytesIO):
        # extract text from local pdf file
        with open(pdf_path, 'rb') as fh:
            try:
                for page in PDFPage.get_pages(
                        fh,
                        caching=True,
                        check_extractable=True
                ):
                    resource_manager = PDFResourceManager()
                    fake_file_handle = io.StringIO()
                    converter = TextConverter(
                        resource_manager,
                        fake_file_handle,
                        codec='utf-8',
                        laparams=LAParams()
                    )
                    page_interpreter = PDFPageInterpreter(
                        resource_manager,
                        converter
                    )
                    page_interpreter.process_page(page)

                    text = fake_file_handle.getvalue()
                    yield text

                    # close open handles
                    converter.close()
                    fake_file_handle.close()
            except PDFSyntaxError:
                return
    else:
        # extract text from remote pdf file
        try:
            for page in PDFPage.get_pages(
                    pdf_path,
                    caching=True,
                    check_extractable=True
            ):
                resource_manager = PDFResourceManager()
                fake_file_handle = io.StringIO()
                converter = TextConverter(
                    resource_manager,
                    fake_file_handle,
                    codec='utf-8',
                    laparams=LAParams()
                )
                page_interpreter = PDFPageInterpreter(
                    resource_manager,
                    converter
                )
                page_interpreter.process_page(page)

                text = fake_file_handle.getvalue()
                yield text

                # close open handles
                converter.close()
                fake_file_handle.close()
        except PDFSyntaxError:
            return


def extract_text_from_docx(doc_path):
    '''
    Helper function to extract plain text from .docx files

    :param doc_path: path to .docx file to be extracted
    :return: string of extracted text
    '''
    try:
        temp = docx2txt.process(doc_path)
        text = [line.replace('\t', ' ') for line in temp.split('\n') if line]
        return ' '.join(text)
    except KeyError:
        return ' '


def extract_text_from_doc(doc_path):
    '''
    Helper function to extract plain text from .doc files

    :param doc_path: path to .doc file to be extracted
    :return: string of extracted text
    '''
    try:
        try:
            print("Doc PATH",doc_path)
            subprocess.call(['soffice', '--headless', '--convert-to', 'docx', doc_path])     
        except ImportError:
            return ' '
        temp = docx2txt.process(doc_path)
        text = [line.replace('\t', ' ') for line in temp.split('\n') if line]
        return ' '.join(text)        
    except KeyError:
        return ' '


def extract_text(file_path, extension):
    '''
    Wrapper function to detect the file extension and call text
    extraction function accordingly

    :param file_path: path of file of which text is to be extracted
    :param extension: extension of file `file_name`
    '''
    text = ''
    if extension == '.pdf':
        for page in extract_text_from_pdf(file_path):
            text += ' ' + page
    elif extension == '.docx':
        text = extract_text_from_docx(file_path)
    elif extension == '.doc':
        text = extract_text_from_doc(file_path)
    return text


def extract_entity_sections_grad(text):
    '''
    Helper function to extract all the raw text from sections of
    resume specifically for graduates and undergraduates

    :param text: Raw text of resume
    :return: dictionary of entities
    '''
    text_split = [i.strip() for i in text.split('\n')]
    # sections_in_resume = [i for i in text_split if i.lower() in sections]
    entities = {}
    key = False
    for phrase in text_split:
        if len(phrase) == 1:
            p_key = phrase
        else:
            p_key = set(phrase.lower().split()) & set(cs.RESUME_SECTIONS_GRAD)
        try:
            p_key = list(p_key)[0]
        except IndexError:
            pass
        if p_key in cs.RESUME_SECTIONS_GRAD:
            entities[p_key] = []
            key = p_key
        elif key and phrase.strip():
            entities[key].append(phrase)

    # entity_key = False
    # for entity in entities.keys():
    #     sub_entities = {}
    #     for entry in entities[entity]:
    #         if u'\u2022' not in entry:
    #             sub_entities[entry] = []
    #             entity_key = entry
    #         elif entity_key:
    #             sub_entities[entity_key].append(entry)
    #     entities[entity] = sub_entities

    # pprint.pprint(entities)

    # make entities that are not found None
    # for entity in cs.RESUME_SECTIONS:
    #     if entity not in entities.keys():
    #         entities[entity] = None
    return entities



def extract_entities_wih_custom_model(custom_nlp_text):
    '''
    Helper function to extract different entities with custom
    trained model using SpaCy's NER

    :param custom_nlp_text: object of `spacy.tokens.doc.Doc`
    :return: dictionary of entities
    '''
    entities = {}
    for ent in custom_nlp_text.ents:
        if ent.label_ not in entities.keys():
            entities[ent.label_] = [ent.text]
        else:
            entities[ent.label_].append(ent.text)
    for key in entities.keys():
        entities[key] = list(set(entities[key]))

    entities = {k: ",".join(v) for k,v in entities.items()}           
    entities = {k: v.rstrip("\n") for k,v in entities.items()}   
    entities =  {k: v.replace("Bachelor of Technology","B.Tech") for k,v in entities.items()}          
    entities =  {k: v.replace("B-Tech","B.Tech") for k,v in entities.items()}          
    entities =  {k: v.replace("B. Tech","B.Tech") for k,v in entities.items()}          
    entities =  {k: v.replace("BTech","B.Tech") for k,v in entities.items()}        
    entities =  {k: v.replace("btech","B.Tech") for k,v in entities.items()}         
    entities =  {k: v.replace("Btech","B.Tech") for k,v in entities.items()}         
    entities =  {k: v.replace("bTech","B.Tech") for k,v in entities.items()}         
    entities =  {k: v.replace("b.tech","B.Tech") for k,v in entities.items()}         
    entities =  {k: v.replace("b.Tech","B.Tech") for k,v in entities.items()}    
    entities =  {k: v.replace("B.tech","B.Tech") for k,v in entities.items()}     
    entities =  {k: v.lower() for k,v in entities.items()}    
    entities =  {k: v.capitalize() for k,v in entities.items()}
    
    return entities


# def get_total_experience(experience_list):
#     '''
#     Wrapper function to extract total months of experience from a resume

#     :param experience_list: list of experience text extracted
#     :return: total months of experience
#     '''
#     exp_ = []
#     for line in experience_list:
#         experience = re.search(
#             r'(?P<fmonth>\w+.\d+)\s*(\D|to)\s*(?P<smonth>\w+.\d+|present)',
#             line,
#             re.I
#         )
#         if experience:
#             exp_.append(experience.groups())
#     total_exp = sum(
#         [get_number_of_months_from_dates(i[0], i[2]) for i in exp_]
#     )
#     total_experience_in_months = total_exp
#     return total_experience_in_months


# def get_number_of_months_from_dates(date1, date2):
#     '''
#     Helper function to extract total months of experience from a resume

#     :param date1: Starting date
#     :param date2: Ending date
#     :return: months of experience from date1 to date2
#     '''
#     if date2.lower() == 'present':
#         date2 = datetime.now().strftime('%b %Y')
#     try:
#         if len(date1.split()[0]) > 3:
#             date1 = date1.split()
#             date1 = date1[0][:3] + ' ' + date1[1]
#         if len(date2.split()[0]) > 3:
#             date2 = date2.split()
#             date2 = date2[0][:3] + ' ' + date2[1]
#     except IndexError:
#         return 0
#     try:
#         date1 = datetime.strptime(str(date1), '%b %Y')
#         date2 = datetime.strptime(str(date2), '%b %Y')
#         months_of_experience = relativedelta.relativedelta(date2, date1)
#         months_of_experience = (months_of_experience.years
#                                 * 12 + months_of_experience.months)
#     except ValueError:
#         return 0
#     return months_of_experience


def extract_entity_sections_professional(text):
    '''
    Helper function to extract all the raw text from sections of
    resume specifically for professionals

    :param text: Raw text of resume
    :return: dictionary of entities
    '''
    text_split = [i.strip() for i in text.split('\n')]
    entities = {}
    key = False
    for phrase in text_split:
        if len(phrase) == 1:
            p_key = phrase
        else:
            p_key = set(phrase.lower().split()) \
                    & set(cs.RESUME_SECTIONS_PROFESSIONAL)
        try:
            p_key = list(p_key)[0]
        except IndexError:
            pass
        if p_key in cs.RESUME_SECTIONS_PROFESSIONAL:
            entities[p_key] = []
            key = p_key
        elif key and phrase.strip():
            entities[key].append(phrase)
    return entities


def extract_email(text):
    '''
    Helper function to extract email id from text

    :param text: plain text extracted from resume file

    '''
    email = re.findall(r"([^@|\s]+@[^@]+\.[^@|\s]+)", text)
    if email:
        try:
            email = email[0].split()[0].strip(';')
            email = email.lower()
            email = email.replace("email:","")
            email = email.replace("e-mail:","")
            email = email.replace("e-mail-:","")
            email = email.replace("|mobile:","")
            email = email.replace("mobile:","")

            return email
        except IndexError:
            return None




def extract_name(nlp_text, matcher):
    
    pattern = [cs.NAME_PATTERN]

    matcher.add('NAME', None, *pattern)

    matches = matcher(nlp_text)

    for _, start, end in matches:
        span = nlp_text[start:end]
        if 'name' not in span.text.lower():
            name_string = str(span.text.lower())
            name_string = name_string.capitalize()
            return name_string


def extract_mobile_number(text, custom_regex=None):
    '''
    Helper function to extract mobile number from text

    :param text: plain text extracted from resume file
    :return: string of extracted mobile numbers
    '''
    mob_regex = r"\+?\d[\d -]{8,12}\d"
    if not custom_regex:
            mob_num_regex = r'''(\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}|\(\d{3}\)
                            [-\.\s]*\d{3}[-\.\s]??\d{4}|\d{3}[-\.\s]??\d{4})'''
            phone = re.findall(re.compile(mob_num_regex), text)
            phone = [i for i in phone if len(i)>9]

    if phone:
        number = ''.join(phone[0].split())
        number = number[1:] if number.startswith('0') else number
        if len(number) < 10:
            number = re.findall(re.compile(mob_regex),text)
            number = [i for i in number if len(i)>9]
            number = ''.join(number[0].split())
        if len(number) > 10:
            number = number.replace("+","")
            number = number.replace("+91","")
            number = number.replace("+91-","")
            number = number.replace("91-","")
            number = number.replace("-","")

        number = number.replace(",","")

        return number                                                  #change



def extract_degree(nlp_text,noun_chunks):
    '''
    Helper function to extract degree 

    :param nlp_text: object of `spacy.tokens.doc.Doc`
    :param noun_chunks: noun chunks extracted from nlp text
    :return: string of highest qualification
    '''
    tokens = [token.text for token in nlp_text if not token.is_stop]
    
    with open('pyresparser/degree.csv') as f1:
        reader = csv.reader(f1)
        data = list(reader)

    degree_list = [item for sublist in data for item in sublist]
    degree_list = [x.lower() for x in degree_list]

    
    degree_set = []
    #check for one-grams
    for token in tokens:
        if token.lower() in degree_list:
            degree_set.append(token)

    #check for bi-grams and tri-grams
    for token in noun_chunks:
        token = token.text.lower().strip()
        if token in degree_list:
            degree_set.append(token)
    if degree_set:
        degree_set = degree_set[0]

   
    degree_string = "".join(degree_set) 
    # print(degree_string)

    return degree_string

def extract_location(nlp_text,noun_chunks):
    '''
    Helper function to extract location

    :param nlp_text: object of `spacy.tokens.doc.Doc`
    :param noun_chunks: noun chunks extracted from nlp text
    :return: string of highest location
    '''
    tokens = [token.text for token in nlp_text if not token.is_stop]
    
    with open('pyresparser/location.csv') as f1:
        reader = csv.reader(f1)
        data = list(reader)

    location_list = [item for sublist in data for item in sublist]
    location_list = [x.lower() for x in location_list]

    
    location_set = []
    #check for one-grams
    for token in tokens:
        if token.lower() in location_list:
            location_set.append(token)

    # check for bi-grams and tri-grams
    # for token in noun_chunks:
    #     token = token.text.lower().strip()
    #     if token in location_list:
    #         location_set.append(token)
    if location_set:
        location_set = location_set[0]

    location_string = "".join(location_set) 

    return location_string


def extract_college(nlp_text,noun_chunks):
    '''
    Helper function to extract college 

    :param nlp_text: object of `spacy.tokens.doc.Doc`
    :param noun_chunks: noun chunks extracted from nlp text
    :return: string of college Name
    '''
    tokens = [token.text for token in nlp_text if not token.is_stop]
    
    with open('pyresparser/College.csv') as f1:
        reader = csv.reader(f1)
        data = list(reader)
    
    college_list = [item for sublist in data for item in sublist]

    
    collegeset = []
    # check for one-grams
    for token in tokens:
        if token.lower() in college_list:
            collegeset.append(token)

    # print (noun_chunks)
    # check for bi-grams and tri-grams
    for token in noun_chunks:
        token = token.text.lower().strip()
        if token in college_list:
            if token not in collegeset:
                collegeset.append(token)

    lis =  [i.capitalize() for i in ([i.lower() for i in collegeset])]   

    college_string = ",".join(lis) 

    return college_string


def extracts_experience(text):
    '''
    :param text : simple plan text in string format
     uses regex to extract text
    '''
    text = text.lower()
    pattern = r"\d+\s+years?\s+(?:and\s*)?\d+\s+months?|\d+\s+(?:months?|years?)"
    experience = re.findall(pattern, text)
    if experience:
        experience = str(experience[0])    
    else:
        experience = ' '.join([str(elem) for elem in experience])

    return experience
        

def extract_skills(nlp_text, noun_chunks, skills_file=None):
    '''
    Helper function to extract skills from spacy nlp text

    :param nlp_text: object of `spacy.tokens.doc.Doc`
    :param noun_chunks: noun chunks extracted from nlp text
    :return: list of skills extracted
    '''
    tokens = [token.text for token in nlp_text if not token.is_stop]
    if not skills_file:
        data = pd.read_csv(
            os.path.join(os.path.dirname(__file__), 'skills.csv')
        )
    else:
        data = pd.read_csv(skills_file)
    skills = list(data.columns.values)
    skillset = []
    # check for one-grams
    for token in tokens:
        if token.lower() in skills:
            skillset.append(token)

    # check for bi-grams and tri-grams
    for token in noun_chunks:
        token = token.text.lower().strip()
        if token in skills:
            skillset.append(token)

    lis =  [i.capitalize() for i in ([i.lower() for i in skillset])]
    
    lis = list(set(lis))
 
    return lis
           
    


def cleanup(token, lower=True):
    if lower:
        token = token.lower()
    return token.strip()


def extract_education(nlp_text):
    '''
    Helper function to extract education from spacy nlp text

    :param nlp_text: object of `spacy.tokens.doc.Doc`
    :return: tuple of education degree and year if year if found
             else only returns education degree
    '''
    edu = {}
    # Extract education degree
    try:
        for index, text in enumerate(nlp_text):
            for tex in text.split():
                tex = re.sub(r'[?|$|.|!|,]', r'', tex)
                if tex.upper() in cs.EDUCATION and tex not in cs.STOPWORDS:
                    edu[tex] = text + nlp_text[index + 1]
    except IndexError:
        pass

    # Extract year
    education = []
    for key in edu.keys():
        year = re.search(re.compile(cs.YEAR), edu[key])
        if year:
            education.append((key, ''.join(year.group(0))))
        else:
            education.append(key)
    return education


