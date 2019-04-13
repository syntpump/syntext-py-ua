import setuptools

with open("README.md", encoding="utf-8") as fp:
    long_description = fp.read()

setuptools.setup(
    name="pysyntext",
    version="0.2",
    description="Syntext NLP project",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/syntpump/syntext-py-ua",
    license="MIT License",
    author="Syntpump",
    author_email="lynnporu@gmail.com",
    install_requires=[
        "ctx19>=1.3",
        "pymongo>=3.7.1",
    ],
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License"
    ],
    keywords="nlp",
    packages=setuptools.find_packages(),
    python_requires=">3",
    project_urls={
        "Syntpump on GitHub": "https://github.com/syntpump"
    }
)
