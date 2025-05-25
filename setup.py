from setuptools import setup, find_packages

setup(
    name='mus-language',
    version='1.0.0',
    packages=find_packages(),
    install_requires=[
        'colorama>=0.4.6',
    ],
    entry_points={
        'console_scripts': [
            'mus = run_mus:main',
        ],
    },
    author='Your Name',
    author_email='your.email@example.com',
    description='Mus Programming Language Interpreter',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/yourusername/mus-language',
    python_requires='>=3.7',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
) 