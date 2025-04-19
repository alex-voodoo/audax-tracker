import os
import pathlib
import subprocess

# Should a new translation language be added, register it using the following command:
# pybabel init --input-file=locales/bot.pot --output-dir=locales --domain=bot --locale=<language code>

os.chdir(pathlib.Path(__file__).parent)

subprocess.run(['pybabel', 'extract', '--input-dirs=.', '--output-file=locales/bot.pot', '--ignore-dirs=venv', '--no-wrap'])

subprocess.run(['pybabel', 'update', '--input-file=locales/bot.pot', '--output-dir=locales', '--domain=bot', '--no-wrap'])
