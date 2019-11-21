import sys
import argparse
import textwrap
import os.path
import yaml
import time
import requests

parser = argparse.ArgumentParser(

description = 'Workload generator using Locust',
    usage='"%(prog)s <command> <arg>". Use  "python %(prog)s --help" o "python %(prog)s -h" for more information',
    formatter_class=argparse.RawTextHelpFormatter)


parser.add_argument("command",
help=textwrap.dedent('''\
    start: 		Start generating the workload
    stop:		Stop Locust swarm
'''))

parser.add_argument("-f", "--file", action='store', help="File containing a trace")
parser.add_argument("--host", action='store', help="Locust web endpoint")
args = parser.parse_args()

command = args.command
CONFIG_FILE = args.file
LOCUST_HOST = args.host


def stop_load():
    url = LOCUST_HOST+'/stop'
    requests.get(url)


def file_exists(n):
    return os.path.isfile(n)


def abort(msg):
    print(msg)
    stop_load()
    sys.exit(1)


def set_user_count(count):
    url = LOCUST_HOST+'/swarm'
    requests.post(url, data={'locust_count': count, 'hatch_rate': count})


def check_params(segment_type, initial_count, end_count, duration):

    try:
        assert initial_count >= 0
        assert end_count >= 0
        assert duration >= 0
        assert initial_count == int(initial_count)
        assert end_count == int(end_count)
        assert duration == int(duration)
    except AssertionError as error:
        abort("Invalid params in config file, counts and duration need to be positive integers\n" + error)	
    
    if(segment_type == 'stable'):
        try:
            assert initial_count == end_count
        except AssertionError as error:
            abort('Invalid configuration. Stable segments need to have the same initial and end count\n' + error)

    elif(segment_type == 'rising'):		
        try:
            assert initial_count < end_count
        except AssertionError as error:
            abort('Invalid configuration. Rising segments need to have the initial count smaller than the end count\n' + error)

    elif(segment_type == 'decreasing'):		
        try:
            assert initial_count > end_count
        except AssertionError as error:
            abort('Invalid configuration. Decreasing segments need to have the initial count greater than the end count \n' + error)

    else:
        abort('Invalidad segment type. Options are: stable, rising, decreasing')


def process_segment(trace):
    segment_type = trace['segment']
    initial_count = trace['initialCount']
    end_count = trace['endCount']
    duration = trace['duration']

    check_params(segment_type, initial_count, end_count, duration)

    if(segment_type == 'stable'):
        set_user_count(initial_count)
        time.sleep(duration)

    elif(segment_type == 'rising'):
        times = end_count-initial_count
        delay = duration/times

        for t in range(times+1):
            set_user_count(t+initial_count)
            time.sleep(delay)

    elif(segment_type == 'decreasing'):
        times = initial_count-end_count
        delay = duration/times

        for t in range(times+1):
            set_user_count(initial_count-t)
            time.sleep(delay)


def generate_load():
    if(file_exists(CONFIG_FILE)):
        try:
            config_data = yaml.safe_load(open(CONFIG_FILE))
        except yaml.YAMLError as error:
            print("The file provided was not a correct file. Please try again... \n" + error)
            sys.exit(1)
    else:
        print("File does not exists. Please try again...")
        sys.exit(1)		

    traces = config_data['load']

    for trace in traces:
        for _ in range(trace['repeat']):
            for segment in trace['trace']:
                process_segment(segment)

    stop_load()			


if(command == 'start'):
    generate_load()

elif(command == 'stop'):
    stop_load()