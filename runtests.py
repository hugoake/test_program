"""
Hugo Åkesson, Feb 2024

This is a command line tool for running test suites for other command line tools.
"""
import argparse
import subprocess
import json
import os
import multiprocessing
from itertools import starmap
from functools import partial

CPU_COUNT = multiprocessing.cpu_count()

# Parse args:
parser = argparse.ArgumentParser()
parser.add_argument("PROGRAM")
parser.add_argument("PATHS", nargs='+')
args = parser.parse_args()


# Read and parse a specifications.csv file:
def read_spec(path_and_name):
  specs = []
  with open(path_and_name, "r") as spec_file:
    spec_names = spec_file.readline().strip().split(',')
    line = spec_file.readline()
    
    while line:
      spec = dict(zip(spec_names,line.split(',')))
      flag, filename = spec["args"].split( )
      specs.append(spec)
      line = spec_file.readline()
    return specs

def unit_test_in_path(spec, path):
  with open(path + spec["output"]) as expected_output:
      expected_output = expected_output.read()
      expected_returncode = int(spec["exitcode"])
      result = subprocess.run([args.PROGRAM, *spec["args"].split(" ")], capture_output=True, text=True, cwd=path)
      # TODO: handle test errors/crashes
      output = result.stdout
      result = (output == expected_output and 
                result.returncode == expected_returncode)
      return (spec["id"], result)

# Runs a test suite and generate report dictionary. Pool is an optional multiprocessing.Pool.
def run_test_suite(specs, path):
  report = {"suite":  os.path.abspath(path),
            "passed": [],
            "failed": []}
            
  unit_test = partial(unit_test_in_path, path=path)
  #pool = multiprocessing.Pool(processes=CPU_COUNT)
  #test_results = list(pool.map(unit_test, specs))
  test_results = list(map(unit_test, specs))
  
  for (id, passed) in test_results:
    if passed:
      report["passed"].append(id)
    else:
      report["failed"].append(id)
  
  return report

def run_test_suite_in_path(path):
    return run_test_suite(read_spec(path+"runtests.csv"), path)

def main():
  pool = multiprocessing.Pool(processes = CPU_COUNT)
  reports = list(pool.map(run_test_suite_in_path,
                          args.PATHS))
  
  # Create test_reports.json if it doesn't already exists:
  name = "test_reports" + ".json"
  if not os.path.isfile(name):
    with open("test_reports.json", "w") as file:
      json.dump({}, file)
  
  with open("test_reports.json", "w") as file:
    json.dump({"reports": reports}, file)

if __name__=="__main__":
  main()