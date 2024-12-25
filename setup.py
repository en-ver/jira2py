from setuptools import setup, find_packages

setup(
    name="jira2py",
    version="0.1.0",
    author="nEver1",
    author_email="7fhhwpuuo@mozmail.com",
    description="The Python library to interact with Atlassian Jira REST API",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/en-ver/jira2py",
    packages=find_packages(),
    install_requires=["python-dotenv>=1.0.0", "requests>=2.0.0"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">3.10",
)
