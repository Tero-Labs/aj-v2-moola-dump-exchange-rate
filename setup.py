import setuptools

setuptools.setup(
    name="celo-sdk",
    version="1.0.0",
    description="Celo Python SDK to work with smart contracts",
    include_package_data=True,
    packages=setuptools.find_packages(),
    install_requires=[
        "requests==2.24.0",
        "web3==5.12.0",
        "pycoingecko==2.0.0",
        "aiohttp==3.7.4",
        "asyncio==3.4.3",
        "pytz==2021.1",
        "APScheduler==3.0.0"   
    ],
    classifiers=[
        "License :: OSI Approved :: Apache License 2.0",
        "Operating System :: Unix",
        "Programming Language :: Python :: 3.8",
        "Blockchain :: Celo"
    ],
    python_requires='>=3.8',
)