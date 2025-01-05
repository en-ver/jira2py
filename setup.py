from setuptools import setup, find_packages

setup(
    name="jira2py",
    version="0.2.0",
    author="nEver1",
    author_email="7fhhwpuuo@mozmail.com",
    license="MIT",
    description="The Python library to interact with Atlassian Jira REST API",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/en-ver/jira2py",
    packages=find_packages(),
    install_requires=[
        "email_validator==2.2.0",
        "pydantic==2.10.4",
        "pydantic_core==2.27.2",
        "python-dotenv==1.0.1",
        "requests==2.32.3",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">3.10",
)
