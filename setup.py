from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="translate-projects-django",
    version="0.0.4",
    author="Neider Ruiz",
    author_email="contact@neiderruiz.com",
    description="Translate your django templates easily",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/translate-projects/translate-projects-django",
    packages=find_packages(),
    license="MIT",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Framework :: Django",
        "Framework :: Django :: 3.0",
        "Framework :: Django :: 3.1",
        "Framework :: Django :: 3.2",
    ],
    python_requires=">=3.7",
    install_requires=[
        "Django>=3.0",
        "polib>=1.2.0",
        "requests>=2.27.1,<3.0",
    ],
)