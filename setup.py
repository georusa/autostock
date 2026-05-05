from setuptools import setup
setup(
    name="autostock",
    version="0.1.0",
    py_modules=["autostock"],
    install_requires=["pandas", "numpy", "matplotlib", "httpx"],
    entry_points={"console_scripts": ["autostock=autostock:main"]},
)
