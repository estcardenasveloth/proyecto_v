from setuptools import setup, find_packages

setup(
    name="Proyect_V",
    version="0.0.1",
    author="Julio César Cárdenas",
    author_email="julio.cardenas@est.iudigital.edu.co",
    description="Scraper histórico de cotizaciones con almacenamiento en SQLite y CSV",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "pandas>=1.0.0",
        "beautifulsoup4>=4.9.0",
        "selenium>=4.0.0",
        "scikit-learn",
        "joblib",
        "streamlit",
        "matplotlib"
    ],
    python_requires=">=3.7",
)
