from setuptools import setup, find_packages

# Lies die Abhängigkeiten aus der requirements.txt-Datei
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='goodog',
    version='0.9.0.0',
    packages=find_packages(),
    install_requires=requirements,
    # Weitere Metadaten hier
)