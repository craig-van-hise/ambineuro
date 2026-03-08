import setuptools
setuptools.setup(
    name="safpy",
    version="0.0.1",
    packages=setuptools.find_packages(),
    setup_requires=["cffi>=1.0.0"],
    cffi_modules=["safpy_build.py:ffibuilder"],
    install_requires=["cffi>=1.0.0","numpy"],
)
