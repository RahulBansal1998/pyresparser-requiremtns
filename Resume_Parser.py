import argparse
import gem_parser
import json

def argument_parser():

    parser = argparse.ArgumentParser()
    parser.add_argument("-f","--filename",required=True,help='resume as an input')
    args = parser.parse_args()
    return args.filename



def main(): 
    '''
     main function getting arguments
     from gem_resume_parser.py file 
    '''
    filename = argument_parser()
    filename_dict = gem_parser.main(filename)
    filename_json = json.dumps(filename_dict, indent = 4)
    print(filename_json)   

main()