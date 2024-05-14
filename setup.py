import os

req_file = 'requirements.txt'

with open(os.path.join(os.path.dirname(__file__), req_file)) as f:
    requires = [line.strip() for line in f.readlines()]

print(f'"{requires}"')

from setuptools import setup, find_packages

setup(name="Base",
      version='0.1.0',
      packages=find_packages(),
      author="Alignment Lab AI",
      author_email='autometa@alignmentlab.ai',
      description='Waste nothing! Store literally everything efficiently, and connect it to a local model!',
      install_requires=requires,
      entry_points={'console_scripts': ['Base=Base:main',
                                        'Baseview=Base.stats:main']})
