from threading import Lock
from flask import Flask, render_template, session, request, jsonify
from flask_socketio import SocketIO, emit, disconnect
import time
import MySQLdb
import configparser as ConfigParser
import serial
import json
import os

async_mode = None

app = Flask(__name__)

config = ConfigParser.ConfigParser()
config.read('config.cfg')
myhost = config.get('mysqlDB', 'host')
myuser = config.get('mysqlDB', 'user')
mypasswd = config.get('mysqlDB', 'passwd')
mydb = config.get('mysqlDB', 'db')

app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock()

data_switch = "LedResistor" # or OutResistor

ser = serial.Serial('/dev/ttyUSB0', 9600)

data_file = 'data_archive.json'
data2_file = 'data2_archive.json'

def write_data_to_file(data_list):
    if data_switch == "LedResistor":
        if os.path.exists(data_file):
            with open(data_file, 'r') as infile:
                all_data = json.load(infile)
        else:
            all_data = []

        all_data.append(data_list)
        
        with open(data_file, 'w') as outfile:
            json.dump(all_data, outfile)
    elif data_switch == "OutResistor":
        if os.path.exists(data2_file):
            with open(data2_file, 'r') as infile:
                all_data = json.load(infile)
        else:
            all_data = []

        all_data.append(data_list)
        
        with open(data2_file, 'w') as outfile:
            json.dump(all_data, outfile)


def background_thread(args):
    count = 0  
    dataCounter = 0 
    dataList = []  
    db = MySQLdb.connect(host=myhost,user=myuser,passwd=mypasswd,db=mydb) 
    start_time = time.time()       
    while True:
        if args:
            A = dict(args).get('A')
            dbV = dict(args).get('db_value')
        else:
            A = 1
            dbV = 'try'  
        
        socketio.sleep(0.5)
        
        if ser.in_waiting > 0:
            nodemcu_data = ser.readline().decode('utf-8').strip().split()
        print(nodemcu_data)
        #if nodemcu_data[0] == data_switch:
        #    sensor_data = nodemcu_data[1]
            
        #else:
         #   continue
        sensor_data_1 = nodemcu_data[1]
        sensor_data_2 = nodemcu_data[3]
        
        if data_switch == nodemcu_data[0]:
            sensor_data = sensor_data_1
        elif data_switch == nodemcu_data[2]:
            sensor_data = sensor_data_2
            
        print(dbV)
        if dbV == 'start':
            count += 1
            dataCounter += 1
            
            dataDict = {
                "count": dataCounter,
                "data": int(sensor_data)
            }
            dataList.append(dataDict)
            
            socketio.emit('my_response',
                      {'sensor_data': str(sensor_data), 'count': count},
                      namespace='/test') 
        else:
            start_time = time.time()
            if len(dataList) > 0:
                print(str(dataList))
                same = str(dataList).replace("'", "\"")
                print(same)
                write_data_to_file(dataList)
                cursor = db.cursor()
                if data_switch == "LedResistor":
                    table_name = "data_1"
                elif data_switch == "OutResistor":
                    table_name = "data_2"
                cursor.execute("SELECT MAX(id) FROM " + table_name)
                maxid = cursor.fetchone()
                cursor.execute("INSERT INTO " + table_name + " (id,data) VALUES (%s, %s)", (maxid[0]+1,same))
                db.commit()
                dataList = []
                dataCounter = 0
                count = 0

@app.route('/get_data/<string:data_wanted>/<int:data_id>', methods=['GET'])
def get_data(data_wanted,data_id):
    if data_wanted == 'ledRes':
        data_file_name = data_file
    elif data_wanted == 'outRes':
        data_file_name = data2_file
    with open(data_file_name, 'r') as infile:
        all_data = json.load(infile)
    if data_id < len(all_data):
        return jsonify({'data': all_data[data_id]})
    else:
        return jsonify({'error': 'Invalid ID'}), 404

        
@app.route('/dbdata/<string:data_wanted>/<int:data_id>', methods=['GET'])
def dbdata(data_wanted,data_id):
    db = MySQLdb.connect(host=myhost,user=myuser,passwd=mypasswd,db=mydb)
    cursor = db.cursor()
    print(data_id)
    print(data_wanted)
    if data_wanted == 'ledRes':
        table_name = "data_1"
    elif data_wanted == 'outRes':
        table_name= "data_2"
    cursor.execute("SELECT data FROM " + table_name + " WHERE id=%s", str(data_id))
    rv = cursor.fetchone()
    return str(rv[0])
    

@app.route('/')
def index():
    return render_template('index.html', async_mode=socketio.async_mode)

@socketio.on('my_event', namespace='/test')
def test_message(message):   
    session['receive_count'] = session.get('receive_count', 0) + 1 
    session['A'] = message['value']    

@socketio.on('db_event', namespace='/test')
def db_message(message):   
    print("db event")
    session['db_value'] = message['value']   
    print("running"+ message['value'])

@socketio.on('disconnect_request', namespace='/test')
def disconnect_request():
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': 'Disconnected!', 'count': session['receive_count']})
    disconnect()

@socketio.on('initialize', namespace='/test')
def test_connect():
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(target=background_thread, args=session._get_current_object())

@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected', request.sid)

@socketio.on('switch_data', namespace='/test')
def switch_data(message):
    global data_switch
    print(data_switch)
    data_switch = message['value']
    print(data_switch)
    
if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=80, debug=True)
