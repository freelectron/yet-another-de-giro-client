from setuptools import setup, find_packages

setup(
    name="de_giro_client_nl",
    vversion='0.1.0',
    author="freelectron",
    author_email="only_use_ICQ",
    description="de giro client",
    url='https://github.com/freelectron/yet-another-de-giro-client',
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.6",
    install_requires=[
        "pandas",
        "pendulum",
        "selenium",
        "numpy",
        "requests",
        "pandera",
        "pendulum",
        "pyaml",
    ],
)
