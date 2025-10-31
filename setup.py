import setuptools

with open("readme.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="stardog-knowledge-kits",
    version="1.0",
    author="Stardog Union",
    description="Knowledge Graph as code",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/stardog-union/knowledge-kits",
    package_dir={"": "src"},
    include_package_data=True,
    packages=setuptools.find_packages(where="src"),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    entry_points ={
            'console_scripts': [
                'kits = stardog_union.kits.cli:cli'
            ]
        },
    install_requires=[
        "pystardog==0.19",
        "rdflib==7.4.0",
        "python-dotenv >= 1.0.0",
        "PyYAML==6.0.1",
        "typer==0.9.0",
        "prettytable==3.10.0",
        "tqdm==4.67.1"
    ],
    extras_require={
        "dev": [
            "mypy == 1.10.0",
            "black == 23.12.1",
            "coverage >= 5.5",
            "coverage >=5.5.0, != 7.3.3",
            "flake8 >= 6.1.0",
            "isort >= 5.13.1",
            "pytest >= 6.2.4",
            "pytest-mock >= 3.11.1",
            "pytest-cov >= 4.1.0",
            "python-dotenv >= 1.0.0",
            "types-PyYAML == 6.0.12.12",
            "types-requests >= 2.27.16",
            "wheel >= 0.41.3",
        ],
    },
    python_requires=">=3.10",
)
