from setuptools import setup, find_packages

REQUIRES = ['stackinabox>=0.13', 'six']

setup(
    name='openstackinabox',
    version='0.1',
    description='RESTful API Testing Suite',
    license='Apache License 2.0',
    url='https://github.com/TestInABox/openstackinabox',
    author='Benjamen R. Meyer',
    author_email='ben.meyer@rackspace.com',
    install_requires=REQUIRES,
    test_suite='openstackinabox',
    packages=find_packages(exclude=['tests*', 'openstackinabox/tests']),
    zip_safe=True,
    classifiers=["Intended Audience :: Developers",
                 "License :: OSI Approved :: MIT License",
                 "Topic :: Software Development :: Testing"],
)
