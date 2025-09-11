"""
Setup script para el Clasificador de Modelos de Nube con NLP.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Leer el README para la descripción larga
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

# Leer requirements.txt para las dependencias
requirements = []
with open("requirements.txt", "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#") and not line.startswith("="):
            # Extraer solo el nombre del paquete y la versión
            if ">=" in line:
                requirements.append(line)

setup(
    name="cloud-models-classifier",
    version="1.0.0",
    author="Tu Nombre",
    author_email="tu.email@ejemplo.com",
    description="Clasificador inteligente de modelos de nube usando NLP con DeepSeek",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tu-usuario/cloud-models-classifier",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Linguistic",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.31.0,<3.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0,<8.0.0",
            "pytest-cov>=4.1.0,<5.0.0",
            "pytest-html>=3.2.0,<4.0.0",
            "pytest-benchmark>=4.0.0,<5.0.0",
            "flake8>=6.0.0,<7.0.0",
            "black>=23.0.0,<24.0.0",
            "mypy>=1.5.0,<2.0.0",
        ],
        "doc": [
            "sphinx>=7.0.0,<8.0.0",
            "sphinx-rtd-theme>=1.3.0,<2.0.0",
        ],
        "test": [
            "pytest>=7.4.0,<8.0.0",
            "pytest-cov>=4.1.0,<5.0.0",
            "pytest-html>=3.2.0,<4.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "cloud-classifier=src.demo:ejecutar_demo",
            "run-tests=tests.ejecutar_pruebas:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.md", "*.txt", "*.ini", "*.env"],
    },
    keywords=[
        "cloud-computing",
        "iaas",
        "paas", 
        "saas",
        "faas",
        "nlp",
        "deepseek",
        "openrouter",
        "classification",
        "machine-learning",
        "artificial-intelligence",
    ],
    project_urls={
        "Bug Reports": "https://github.com/tu-usuario/cloud-models-classifier/issues",
        "Source": "https://github.com/tu-usuario/cloud-models-classifier",
        "Documentation": "https://github.com/tu-usuario/cloud-models-classifier#readme",
    },
)