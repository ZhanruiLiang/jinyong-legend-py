script=$1
kernprof.py -l $*
python -m line_profiler $script.lprof
