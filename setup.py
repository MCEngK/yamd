import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="yamd-MCEngK", # Replace with your own username
    version="0.0.1",
    author="MCEngK",
    author_email="MCEngK@example.com",
    description="A Minecraft daemon tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/MCEngK/yamd",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.4',
)
