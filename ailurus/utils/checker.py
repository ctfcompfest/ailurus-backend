from multiprocessing.pool import ThreadPool

def execute_check_function_with_timelimit(func, func_params, timelimit: int):
    pool = ThreadPool(processes=1)
    job = pool.apply_async(func, args=func_params)
    pool.close()
    
    verdict = job.get(timelimit)
    return verdict
