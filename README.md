# netunicorn-connector-template
This is a template repository for creating a new connector for the netunicorn platform.

## How to use this template
Use the code from `src/netunicorn/contrib/connectors/connector_name.py` as a starting point for your connector. The code is commented and should be self-explanatory.
In addition, you can read the NetunicornProtocol documentation and comments in netunicorn-base package.

## Folder structure
This project establishes a certain folder structure.

### `src` folder
All the code is located in `src` folder. You can freely create other folders for documentation, tests, etc.  
Note that if you create a Python package with setuptools, you'll need to 
specify the `src` folder as the root of the package.  
For example, for pyproject.toml you need to add the next lines:
```toml
[tool.setuptools.packages.find]
where = ["src"]
```

The `pyproject.toml` template in this repository already contains these lines.

### `netunicorn/contrib/connectors` folder
netunicorn project uses namespace packages for separate distribution of parts
of the project. Please, read about namespace packages in Python documentation:
[https://packaging.python.org/en/latest/guides/packaging-namespace-packages/](https://packaging.python.org/en/latest/guides/packaging-namespace-packages/).

Brief rules about our namespace packages:
- It's better to place your modules in `netunicorn/contrib` folder. In the particular case of connectors - in 
  `netunicorn/contrib/connectors` folder.
- You should not create `__init__.py` files in `netunicorn` and `netunicorn/contrib` folders, but you can create them
  in subfolders of `netunicorn/contrib` folder.
- After installation of your package, your modules will be available as `netunicorn.contrib.connectors.<your_module_name>`.

## GitHub Actions
This template repository contains a GitHub Actions workflow that will release your connector to PyPI
when it detects that local version in pyproject.toml is higher than the version on PyPI.  

Please, notice that you either need to add your PyPI credentials to the corresponding environment,
or use PyPI Trusted Publishing mechanism (see [https://docs.pypi.org/trusted-publishers/](https://docs.pypi.org/trusted-publishers/)).

Note, that by default push trigger is commented out. You need to uncomment it to enable automatic releases.