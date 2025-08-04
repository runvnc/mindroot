from setuptools import setup, find_packages

setup(
    name="mr-mcp",
    version="1.0.0",
    description="Model Context Protocol integration for MindRoot",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    package_data={
        "mr_mcp": [
            "templates/*.jinja2",
            "inject/*.jinja2",
            "static/js/*.js",
            "static/css/*.css",
            "data/*.json"
        ],
    },
    install_requires=[
        "mcp>=1.9.0",
        "httpx>=0.24.0",
        "pydantic>=2.0.0",
        "aiofiles>=23.0.0",
        "uv>=0.7.0"
    ],
    python_requires=">=3.8",
)