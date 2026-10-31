from setuptools import setup, Extension
from Cython.Build import cythonize

extensions = [
    Extension(
        name="chronos.matching_core",
        sources=["chronos/matching_core.pyx"],
    )
]

setup(
    name="ChronosMatch",
    ext_modules=cythonize(
        extensions,
        compiler_directives={"language_level": "3"}
    ),
)