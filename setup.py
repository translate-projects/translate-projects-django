from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="translate-projects-django",
    version="0.1.0",
    author="Neider Ruiz",
    author_email="contact@translateprojects.dev",
    description="Translate your Django projects easily",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/translate-projects/translate-projects-django",
    packages=find_packages(exclude=["tests", "tests.*"]),
    license="MIT",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Framework :: Django",
        "Framework :: Django :: 3.2",
        "Framework :: Django :: 4.2",
        "Framework :: Django :: 5.1",
        "Framework :: Django :: 5.2",
    ],
    python_requires=">=3.8",
    install_requires=[
        "Django>=3.2",
        "polib>=1.2.0",
        "requests>=2.27.1,<3.0",
        "rich>=12.4.4",
        "websockets>=10.3",
    ],
)
