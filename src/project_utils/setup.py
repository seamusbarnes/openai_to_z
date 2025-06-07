from setuptools import setup, find_packages

setup(
    name="openai_to_z",          # pick any name you like
    version="0.0.1",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
)
EOF