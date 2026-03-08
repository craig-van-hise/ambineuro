import os.path
import sys
from cffi import FFI
ffibuilder = FFI()

this_dir = os.path.abspath(os.path.dirname(__file__))
saf_path = os.path.join(this_dir, "Spatial_Audio_Framework")

c_header_source = f"""
#include "{saf_path}/framework/include/saf.h"
"""
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
void* calloc(size_t count, size_t size);

// afSTFT
void afSTFT_create(void** const phSTFT, int nCHin, int nCHout, int hopsize, int lowDelayMode, int hybridmode, int format);
void afSTFT_destroy(void** const phSTFT);
void afSTFT_forward(void* const hSTFT, float** dataTD, int framesize, float _Complex*** dataFD);
void afSTFT_backward(void* const hSTFT, float _Complex*** dataFD, int framesize, float** dataTD);
void afSTFT_getCentreFreqs(void* const hSTFT, float fs, int nBands, float* freqVector);
int afSTFT_getNBands(void* const hSTFT);
int afSTFT_getProcDelay(void* const hSTFT);
void afSTFT_clearBuffers(void* const hSTFT);
void afSTFT_forward_flat(void* const hSTFT, float* dataTD, int framesize, float _Complex* dataFD);
void afSTFT_backward_flat(void* const hSTFT, float _Complex* dataFD, int framesize, float* dataTD);

// HOA
typedef enum {
    BINAURAL_DECODER_DEFAULT,
    BINAURAL_DECODER_LS,
    BINAURAL_DECODER_LSDIFFEQ,
    BINAURAL_DECODER_SPR,
    BINAURAL_DECODER_TA,
    BINAURAL_DECODER_MAGLS
} BINAURAL_AMBI_DECODER_METHODS;

void getBinauralAmbiDecoderMtx(float _Complex* hrtfs, float* hrtf_dirs_deg, int N_dirs, int N_bands, 
                                BINAURAL_AMBI_DECODER_METHODS method, int order, float* freqVector, 
                                float* itd_s, float* weights, int enableDiffCM, int enableMaxrE, 
                                float _Complex* decMtx);

// Utils
void HRIRs2HRTFs_afSTFT(float* hrirs, int N_hrir_dirs, int hrir_len, int hopSize, int lowDelayMode, int hybridMode, float _Complex* hrtf_fb);
void estimateITDs(float* hrirs, int N_dirs, int hrir_len, int fs, float* itds_s);

// default HRTFs
extern const float __default_hrirs[200*2*256];
extern const float __default_hrir_dirs_deg[200*2];
extern const int __default_N_hrir_dirs;
extern const int __default_hrir_len;
extern const int __default_hrir_fs;
""")

ffibuilder.set_source("_safpy", c_header_source, include_dirs=include_dirs,
                      libraries=libraries, library_dirs=library_dirs, 
                      extra_link_args=extra_link_args)

if __name__ == "__main__":
    ffibuilder.compile(verbose=True)
