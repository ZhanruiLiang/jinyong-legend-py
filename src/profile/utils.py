import time

def timeit(run_times=1000):
    def deco(func):
        def new_func(*args, **kwargs):
            records = [0] * run_times
            for t in range(run_times):
                startTime = time.clock()
                func(*args, **kwargs)
                elapsedTime = time.clock() - startTime
                records[t] = elapsedTime
            avg = sum(records) / len(records)
            print('run {} {} loops, avg: {:.2f}ms min: {:.2}ms max: {:.2}ms'.format(
                func.__name__, run_times, 
                avg * 1000, min(records) * 1000, max(records) * 1000,
            ))
        return new_func
    return deco
