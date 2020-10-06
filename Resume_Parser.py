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
    filejson = gem_parser.main(filename)
    json_object = json.dumps(filejson, indent = 4)
    print(json_object)   

main()