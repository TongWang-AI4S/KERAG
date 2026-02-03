from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="kerag",
    version="0.1.1",
    author="Tong",
    author_email="TongWang_2000@outlook.com",
    description="Knowledge Explorer Retrieval Augmented Generation - 知识探索检索增强生成系统",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/TongWang-AI4S/KERAG",
    packages=find_packages(),
    install_requires=["PyYAML"],
    entry_points={
        "console_scripts": [
            "kerag = kerag.cli:main",
        ],
    },
    python_requires=">=3.8",
)
