import os.path
import sys
from cffi import FFI
ffibuilder = FFI()

this_dir = os.path.abspath(os.path.dirname(__file__))
saf_path = os.path.join(this_dir, "Spatial_Audio_Framework")

c_header_source = f'#include "{saf_path}/framework/include/saf.h"'
include_dirs = []
libraries = []
library_dirs = [this_dir, saf_path]
extra_link_args = []

if sys.platform == "darwin":
    extra_link_args.extend(['-Wl,-framework', '-Wl,Accelerate'])
    extra_link_args.append('-Wl,-force_load,' + os.path.join(saf_path, "build/framework/libsaf.a"))

ffibuilder.cdef("""
void* malloc(size_t size);
void free(void* ptr);
void afSTFT_create(void** const phSTFT, int nCHin, int nCHout, int hopsize, int lowDelayMode, int hybridmode, int format);
void afSTFT_destroy(void** const phSTFT);
void afSTFT_forward(void* const hSTFT, float** dataTD, int framesize, float _Complex*** dataFD);
void afSTFT_backward(void* const hSTFT, float _Complex*** dataFD, int framesize, float** dataTD);
""")

ffibuilder.set_source("_safpy", c_header_source, include_dirs=include_dirs,
                      libraries=libraries, library_dirs=library_dirs, 
                      extra_link_args=extra_link_args)

if __name__ == "__main__":
    ffibuilder.compile(verbose=True)
