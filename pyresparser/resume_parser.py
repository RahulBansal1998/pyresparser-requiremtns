# Author: Omkar Pathak

import os
import multiprocessing as mp
import io
import spacy
import pprint
from spacy.matcher import Matcher
from . import utils


class ResumeParser(object):
    ''' Main class to define 
    all entity global variable 
    resume.py is calling this class  
    '''  
    def __init__(
        self,
        resume,
        skills_file=None,
        custom_regex=None
    ):
        nlp = spacy.load('en_core_web_sm')
        custom_nlp = spacy.load(os.path.dirname(os.path.abspath(__file__)))
        self.__skills_file = skills_file
        self.__custom_regex = custom_regex
        self.__matcher = Matcher(nlp.vocab)
        self.__details = {
            'Title':None,
            'Gender':None,
            'name': None,
            'email': None,
            'mobile_number': None,
            'url' : None,
            'skills': None,
            'college_name': None,
            'education_and_training': None,
            'designation': None,
            'company_names': None,
            'total_experience': None,
            'Current Location':None,
            'experiene':None
        }
        self.__resume = resume
        self.__file = self.__resume
        if not isinstance(self.__resume, io.BytesIO):
            ext = os.path.splitext(self.__resume)[1].split('.')[1]
        else:
            ext = self.__resume.name.split('.')[1]
        self.__text_raw = utils.extract_text(self.__resume, '.' + ext)
        self.__text = ' '.join(self.__text_raw.split())
        self.__nlp = nlp(self.__text)
        self.__custom_nlp = custom_nlp(self.__text_raw)
        self.__noun_chunks = list(self.__nlp.noun_chunks)
        self.__get_basic_details()

    def get_extracted_data(self):
        return self.__details
    
    def get_extracted_text(self):
        ext1 = self.__resume.name.split('.')[1]
        text_raw = utils.extract_text(self.__resume, '.' + ext1)
        return text_raw


    def __get_basic_details(self):
        cust_ent = utils.extract_entities_wih_custom_model(
                            self.__custom_nlp
                        )
        name = utils.extract_name(self.__nlp, matcher=self.__matcher)
        email = utils.extract_email(self.__text)
        mobile = utils.extract_mobile_number(self.__text, self.__custom_regex)
        skills = utils.extract_skills(
                    self.__nlp,
                    self.__noun_chunks,
                    self.__skills_file
                )
        try:
            self.__details['name'] = cust_ent['Name'][0]
        except (IndexError, KeyError):
            self.__details['name'] = name

        gender = utils.extract_gender_title(self.__details['name'])
        
        self.__details['Gender'] = gender[0]

        self.__details['Title'] = gender[1]

        experiences = utils.extracts_experience(self.__text)

        education_and_training = utils.extract_degree(self.__nlp,self.__noun_chunks)
        
        college = utils.extract_college(
                    self.__nlp,
                    self.__noun_chunks
                )
        Location = utils.extract_location(
                    self.__nlp,
                    self.__noun_chunks
                )

        entities = utils.extract_entity_sections_grad(self.__text_raw)

        self.__details['experience'] = entities['experience']

        # resume_link = utils.resume_link(self.__file,self.__argument)

        # self.__details['url'] = resume_link
        # edu = utils.extract_education(
        #               [sent.string.strip() for sent in self.__nlp.sents]
        #       )

        # extract name


        # extract email
        self.__details['email'] = email

        # extract mobile number
        self.__details['mobile_number'] = mobile

        # extract skills
        self.__details['skills'] = skills

        # extract college name
        try:
            self.__details['college_name'] = entities['College Name']
        except KeyError:
            self.__details['college_name'] = college


        # extract education_and_training
        try:
            self.__details['education_and_training'] = cust_ent['Degree']
        except KeyError:
            self.__details['education_and_training'] = education_and_training


        # extract designation
        try:
            self.__details['designation'] = cust_ent['Designation']
        except KeyError:
            pass

        # extract company names
        try:
            self.__details['company_names'] = cust_ent['Companies worked at']
        except KeyError:
            pass

        try:
            self.__details['total_experience'] = cust_ent['Years of Experience']                  
        except (IndexError, KeyError):
            self.__details['total_experience'] = experiences

        return


def resume_result_wrapper(resume):
    parser = ResumeParser(resume)
    return parser.get_extracted_data()


if __name__ == '__main__':
    pool = mp.Pool(mp.cpu_count())

    resumes = []
    data = []
    for root, directories, filenames in os.walk('resumes/'):
        for filename in filenames:
            file = os.path.join(root, filename)
            resumes.append(file)

    results = [
        pool.apply_async(
            resume_result_wrapper,
            args=(x,)
        ) for x in resumes
    ]

    results = [p.get() for p in results]
    pprint.pprint(results)
