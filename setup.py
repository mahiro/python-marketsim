import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="marketsim",
    version="0.0.1",
    author="Mahiro Ando",
    author_email="ma514y@gmail.com",
    description="Stock market simulation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mahiro/python-marketsim",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
