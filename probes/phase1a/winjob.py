"""Experimental Windows process-tree containment, independent of DSH cancellation."""
import ctypes as C
from ctypes import wintypes as W
import time

class IO(C.Structure):
    _fields_=[(n,C.c_ulonglong) for n in ('readOps','writeOps','otherOps','readBytes','writeBytes','otherBytes')]
class BASIC(C.Structure):
    _fields_=[('processTime',C.c_longlong),('jobTime',C.c_longlong),('flags',W.DWORD),
        ('minWS',C.c_size_t),('maxWS',C.c_size_t),('activeLimit',W.DWORD),('affinity',C.c_size_t),('priority',W.DWORD),('scheduling',W.DWORD)]
class EXTENDED(C.Structure):
    _fields_=[('basic',BASIC),('io',IO),('processMemory',C.c_size_t),('jobMemory',C.c_size_t),('peakProcess',C.c_size_t),('peakJob',C.c_size_t)]
class ACCOUNTING(C.Structure):
    _fields_=[('user',C.c_longlong),('kernel',C.c_longlong),('periodUser',C.c_longlong),('periodKernel',C.c_longlong),
        ('pageFaults',W.DWORD),('totalProcesses',W.DWORD),('activeProcesses',W.DWORD),('terminatedProcesses',W.DWORD)]

class Job:
    def __init__(self,process):
        self.k=C.WinDLL('kernel32',use_last_error=True)
        self.k.CreateJobObjectW.argtypes=[C.c_void_p,W.LPCWSTR]; self.k.CreateJobObjectW.restype=W.HANDLE
        self.k.SetInformationJobObject.argtypes=[W.HANDLE,C.c_int,C.c_void_p,W.DWORD]
        self.k.AssignProcessToJobObject.argtypes=[W.HANDLE,W.HANDLE]
        self.k.QueryInformationJobObject.argtypes=[W.HANDLE,C.c_int,C.c_void_p,W.DWORD,C.c_void_p]
        self.k.TerminateJobObject.argtypes=[W.HANDLE,W.UINT]
        self.k.CloseHandle.argtypes=[W.HANDLE]
        self.handle=self.k.CreateJobObjectW(None,None)
        limits=EXTENDED(); limits.basic.flags=0x2000 # KILL_ON_JOB_CLOSE
        if not self.handle or not self.k.SetInformationJobObject(self.handle,9,C.byref(limits),C.sizeof(limits)):
            raise C.WinError(C.get_last_error())
        if not self.k.AssignProcessToJobObject(self.handle,W.HANDLE(int(process._handle))):
            raise C.WinError(C.get_last_error())

    def snapshot(self):
        a=ACCOUNTING()
        if not self.k.QueryInformationJobObject(self.handle,1,C.byref(a),C.sizeof(a),None): raise C.WinError(C.get_last_error())
        return {'total':a.totalProcesses,'active':a.activeProcesses,'terminated':a.terminatedProcesses}

    def close(self):
        before=self.snapshot()
        if before['active']: self.k.TerminateJobObject(self.handle,90)
        until=time.monotonic()+5
        after=self.snapshot()
        while after['active'] and time.monotonic()<until:
            time.sleep(.01); after=self.snapshot()
        self.k.CloseHandle(self.handle)
        assert after['active']==0,after
        return {'before':before,'after':after,'seam':'Windows Job Object; no listeners; stdio only'}
