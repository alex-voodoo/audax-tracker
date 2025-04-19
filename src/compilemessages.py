import os
import pathlib
import subprocess

os.chdir(pathlib.Path(__file__).parent)

subprocess.run(['pybabel', 'compile', '--directory=locales', '--domain=bot', '--use-fuzzy'])
