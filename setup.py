from setuptools import setup, find_packages

setup(
    name="omniscient",
    version="0.1.0",
    description="🔍 Omniscient - Framework modulaire de reconnaissance et de pentest automatique",
    author="Jordan Poujol",
    author_email="jordanpoujol@gmail.com",
    url="https://github.com/TonGitHub/Omniscient",
    packages=find_packages(exclude=["tests", "docs"]),
    include_package_data=True,
    install_requires=[
        "pyyaml",
        "colorama"
    ],
    entry_points={
        "console_scripts": [
            "omniscient=omniscient.main:main"
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: MIT License"
    ],
    python_requires='>=3.7',
)

