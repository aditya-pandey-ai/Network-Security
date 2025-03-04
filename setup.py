from setuptools import setup, find_packages
from typing import List

def get_requirements() -> List[str]:

    requirement_lst:List[str] = []
    try:
        with open("requirements.txt", "r") as file:
            lines = file.readlines() # Read lines
            for line in lines:
                requirement = line.strip() #Ignore empty lines
                if requirement and requirement != '-e .':
                    requirement_lst.append(requirement)
    except FileNotFoundError:
        print("requirements.txt not found")

    return requirement_lst

setup(
    name="Network Security",
    version = "0.0.1",
    author="Aditya Pandey",
    author_email="pandey.aditya2304@gmail.com",
    packages=find_packages(),
    install_requires=get_requirements(),
)