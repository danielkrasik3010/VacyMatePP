from setuptools import setup, find_packages

setup(
    name="vacaymate",
    version="0.1",
    packages=find_packages(where="."),
    package_dir={"": "."},
    install_requires=[
        "fastapi>=0.68.0",
        "uvicorn>=0.15.0",
        "pydantic>=1.8.0",
        "pyowm>=3.3.0",
        "requests>=2.26.0",
        "python-dotenv>=0.19.0",
        "langchain>=0.1.0",
        "langchain-openai>=0.0.1",
        "langgraph>=0.0.1",
        "tavily-python>=0.3.0",
        "pandas>=2.0.0",
        "openai>=1.0.0",
        "tiktoken>=0.5.0",
        "tenacity>=8.2.0"
    ],
    python_requires=">=3.8",
    include_package_data=True,
    package_data={
        "": ["*.yaml", "*.json"],
    },
)
