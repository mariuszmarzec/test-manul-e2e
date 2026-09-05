from setuptools import setup, find_packages

setup(
    name='flask-items-api',
    version='1.0.0',
    description='A simple Flask web application for managing items',
    author='Mariusz Marzec',
    author_email='mariuszmarzec@gmail.com',
    py_modules=['app', 'models'],
    install_requires=[
        'flask',
    ],
    extras_require={
        'test': [
            'pytest',
        ],
    },
    python_requires='>=3.8',
)
