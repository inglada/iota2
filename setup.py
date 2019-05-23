#~ from distutils.core import setup
import setuptools
setuptools.setup(
    name='iota2',
    version='',
    py_modules = ["iota2"],
    #~ packages=['scripts', 'scripts.MPI', 'scripts.Steps', 'scripts.Tests', 'scripts.Tests.UnitTests',
              #~ 'scripts.Tests.IntegrationTests', 'scripts.Common', 'scripts.Common.Tools', 'scripts.Sensors',
              #~ 'scripts.Sensors.SAR', 'scripts.Learning', 'scripts.Sampling', 'scripts.Validation',
              #~ 'scripts.VectorTools', 'scripts.Classification', 'scripts.simplification'],
    packages=setuptools.find_packages(),
    url='',
    license='',
    author='Arthur VINCENT',
    author_email='',
    description=''
)
