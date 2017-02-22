
from db import session, engine
from base import Command
import os
import subprocess
import datetime
import logging
errPath=os.path.dirname(os.path.realpath(__file__))+"/"+'application.log'
logging.basicConfig(filename=errPath,level=logging.INFO)
"""
Handles the work of validating and processing command input.
"""


def get_valid_commands(queue, fileName):
    # TODO: efficiently evaluate commands
    validSet=set()
    check = 0
    count = 0
    filePath=os.path.dirname(os.path.realpath(__file__))+"/"+fileName
    try:
        for line in reversed(open(filePath).readlines()):
            line=line.rstrip()
            if(line=='' or line==None):
                continue
            if(line =="[VALID COMMANDS]"):
                break;
            if (line == "[COMMAND LIST]"):
                validSet.clear()
            if (line not in validSet):
                validSet.add(line)

        #Reading commands and if they are present in Valid list, and if present in list, we will put in queue.
        file = open(filePath, "r")
        lines = file.readlines()
        for line in lines:
            line = line.lstrip()
            line = line.rstrip()
            if(bool(not line or line.isspace())):
                continue
            if (line == "[VALID COMMANDS]"):
                check = 0
            elif (line == "[COMMAND LIST]"):
                check = 1
            elif(check==1 and (line in validSet)):
                queue.put(line)
                count+=1
                validSet.remove(line) #Removing entry from valid set so that duplicate entry entering in queue should be restricted.
    except (FileNotFoundError, IOError) as e:
        logging.error("FileNotFoundError/IOError in method get_valid_commands:"+str(e.errno)+":"+e.strerror)
    except Exception as e:
        logging.error("Error in method get_valid_commands:" + str(e.errno) + ":" + e.strerror)
    return count


def get_valid_commands_file_data(queue, file_data):
    # TODO: efficiently evaluate commands
    logging.info("Inside get_valid_commands_file_data function. Reading data from Body")
    lines = file_data.split('\n')
    validSet=set()
    check = 0
    count = 0
    try:
        for line in reversed(lines):
            line=line.rstrip()
            if(line=='' or line==None):
                continue
            if(line =="[VALID COMMANDS]"):
                break;
            if (line == "[COMMAND LIST]"):
                validSet.clear()
            if (line not in validSet):
                validSet.add(line)

        #Reading commands and if they are present in Valid list, and if present in list, we will put in queue.

        for line in lines:
            line = line.rstrip().lstrip()
            if(bool(not line or line.isspace())):
                continue
            if (line == "[VALID COMMANDS]"):
                check = 0
            elif (line == "[COMMAND LIST]"):
                check = 1
            elif(check==1 and (line in validSet)):
                queue.put(line)
                count+=1
                validSet.remove(line) #Removing entry from valid set so that duplicate entry entering in queue should be restricted.
    except (FileNotFoundError, IOError) as e:
        logging.error("Inside get_valid_commands_file_data. FileNotFoundError/IOError in method get_valid_commands:"+str(e.errno)+":"+e.strerror)
    except Exception as e:
        logging.error("Inside get_valid_commands_file_data. Error in method get_valid_commands:" + str(e.errno) + ":" + e.strerror)
    return count


def process_command_output(queue):
    # TODO: run the command and put its data in the db
    command = queue.get()
    a = datetime.datetime.now()
    output=b''
    totalTime=0
    try:
        p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        try:
            p.wait(60)
            for line in p.stdout.readlines():
                output=output+line
            totalTime=(datetime.datetime.now()-a).total_seconds()
        except Exception:
            p.kill()
            logging.error("Command :"+ command+ "Not Executed Successfully due to Timeout")
            output =b''

        cmd = Command(command, len(command), totalTime, output)
        session.add(cmd)
        session.commit()
    except Exception as e:
        logging.error("Exception in process_command_output:" )

