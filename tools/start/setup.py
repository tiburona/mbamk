import setuptools

setuptools.setup(
    name="start",
    description="a small utility to run a development server, run tests, and deploy MBAM",
    packages=setuptools.find_packages(),
    install_requires=['pyyaml', 'colorama'],
    scripts=['entry.py'],
    python_requires='>=3.7',
    entry_points={
        'console_scripts': ['mbam=start.entry:main'],
    }
)