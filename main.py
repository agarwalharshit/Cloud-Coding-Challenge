"""
Details the various flask endpoints for processing and retrieving
command details as well as a swagger spec endpoint
"""

from multiprocessing import Process, Queue
import sys

import datetime
from flask import Flask, request, jsonify
from flask_swagger import swagger
import os
from db import session, engine
from base import Base, Command
from command_parser import get_valid_commands, process_command_output, get_valid_commands_file_data
import logging
errPath=os.path.dirname(os.path.realpath(__file__))+"/"+'application.log'
logging.basicConfig(filename=errPath,level=logging.INFO)

app = Flask(__name__)


@app.route('/commands', methods=['GET'])
def get_command_output():
    """
    Returns as json the command details that have been processed
    ---
    tags: [commands]
    responses:
      200:
        description: Commands returned OK
      400:
        description: Commands not found
    """
    logging.info('Get request for Commands Called')
    res="{"
    try:
        for row in session.query(Command):
            if(res !="{"):
                res=res+","
            
            s=str(row.duration)
            res=res+"{'id':"+str(row.id)\
                +",'command_string':"+row.command_string\
                +",'length':"+str(row.length)\
                +",'duration':"+str(row.duration) \
                + ",'output':" + str(row.output) \
                +"}"
    except Exception as excep:
        logging.info("Exception in function get_command_output(): "+excep.args[0])
        return jsonify("{'error:'"+excep.args[0]+"}"), 400
    res=res+"}"
    # TODO: format the query result
    return jsonify(res),200



@app.route('/commands', methods=['POST'])
def process_commands():
    """
    Processes commmands from a command list
    ---
    tags: [commands]
    parameters:
      - name: filename
        in: formData
        description: filename of the commands text file to parse
        required: true
        type: string
    responses:
      200:
        description: Processing OK
    """
    file_data = request.data.decode("utf-8")
    if not file_data:
        fileName = request.args.get('filename')
        logging.info('Post request for Commands called. Fole_Data not present. File name from input parameters is:'+str(fileName))
        if fileName ==None:
            logging.info('File name not provided in imput parameters')
            return 'fileName not provided', 400
        
    
    queue = Queue()
    if file_data:
        countElements = get_valid_commands_file_data(queue, file_data)
    else:
        countElements = get_valid_commands(queue, fileName)
    
    if(countElements>0):
        processes = [Process(target=process_command_output, args=(queue,))
                     for num in range(countElements)]
        for process in processes:
            process.start()
        for process in processes:
            process.join()
    return 'Successfully processed commands.',200


@app.route('/database', methods=['POST'])
def make_db():
    """
    Creates database schema
    ---
    tags: [db]
    responses:
      200:
        description: DB Creation OK
    """
    Base.metadata.create_all(engine)
    logging.info('Database Schema Created')
    return 'Database creation successful.',200


@app.route('/database', methods=['DELETE'])
def drop_db():
    """
    Drops all db tables
    ---
    tags: [db]
    responses:
      200:
        description: DB table drop OK
    """
    logging.info('Database deletion called')
    try:
        Base.metadata.drop_all(engine)
        logging.info('Database deleted')
    except Exception as e:
        logging.error("Error in deletion of Database:" + str(e.errno) + ":" + e.strerror)
    
    return 'Database deletion successful.',200

@app.route('/spec')
def swagger_spec():
    """
    Display the swagger formatted JSON API specification.
    ---
    tags: [docs]
    responses:
      200:
        description: OK status
    """
    spec = swagger(app)
    spec['info']['title'] = "Nervana cloud challenge API"
    spec['info']['description'] = ("Nervana's cloud challenge " +
                                   "for interns and full-time hires")
    spec['info']['license'] = {
        "name": "Nervana Proprietary License",
        "url": "http://www.nervanasys.com",
    }
    spec['info']['contact'] = {
        "name": "Nervana Systems",
        "url": "http://www.nervanasys.com",
        "email": "info@nervanasys.com",
    }
    spec['schemes'] = ['http']
    spec['tags'] = [
        {"name": "db", "description": "database actions (create, delete)"},
        {"name": "commands", "description": "process and retrieve commands"}
    ]
    return jsonify(spec)



if __name__ == '__main__':
    """
    Starts up the flask server
    """
    port = 8080
    use_reloader = True
    
    logging.info("Application Started  on port:"+str(port))
    # provides some configurable options
    for arg in sys.argv[1:]:
        if '--port' in arg:
            port = int(arg.split('=')[1])
        elif '--use_reloader' in arg:
            use_reloader = arg.split('=')[1] == 'true'

    app.run(port=port, debug=True, use_reloader=use_reloader)

