#! /usr/bin/env python3
import sys
sys.path.append('..')

import record

cases = {}

def testcase(case):
    cases[case.__name__] = case
    return case

def run_all():
    for case in cases.values():
        case()


@testcase
def save_load():
    r = record.Record.load('1')
    r.save('9')
    r1 = record.Record.load('9')
    # print(r, r1)
    assert r == r1

if __name__ == '__main__':
    if len(sys.argv) == 1:
        run_all()
    else:
        cases[sys.argv[1]]()
