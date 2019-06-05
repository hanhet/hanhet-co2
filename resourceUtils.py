import os
import time
import psutil
import sys
import atexit

def get_cpu_time():
	return psutil.cpu_times().idle

def get_total_memory():
    mem = psutil.virtual_memory()
    return mem.total

def get_free_memory():
	mem = psutil.virtual_memory()
	return mem.free

def get_total_disk():
    disk = psutil.disk_usage('/')
    return (disk.total)
    
def get_free_disk():
	disk = psutil.disk_usage('/')
	return disk.free
