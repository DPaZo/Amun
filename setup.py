from pathlib import Path

from Cython.Build import cythonize
from setuptools import Extension, find_packages, setup
from setuptools.command.build_py import build_py as _build_py


def module_name_from_path(path: Path) -> str:
    return ".".join(path.with_suffix("").parts)


compiled_files = [
    Path("client/connection.py"),
    Path("client/robot.py"),
    *sorted(Path("server").rglob("*.py")),
    *sorted(Path("gui").rglob("*.py")),
]

compiled_files = [path for path in compiled_files if path.name != "__init__.py"]

hidden_module_names = {module_name_from_path(path) for path in compiled_files}

extensions = [
    Extension(
        module_name_from_path(path),
        [path.as_posix()],
    )
    for path in compiled_files
]


class BuildPy(_build_py):
    def find_package_modules(self, package, package_dir):
        modules = super().find_package_modules(package, package_dir)
        visible_modules = []

        for pkg, module, module_file in modules:
            full_name = f"{pkg}.{module}" if pkg else module
            if full_name not in hidden_module_names:
                visible_modules.append((pkg, module, module_file))

        return visible_modules


setup(
    name="amun",
    version="0.1.0",
    py_modules=["amun"],
    packages=find_packages(include=["client", "client.*", "server", "server.*", "gui", "gui.*"]),
    ext_modules=cythonize(
        extensions,
        compiler_directives={"language_level": "3"},
    ),
    cmdclass={"build_py": BuildPy},
    include_package_data=False,
    exclude_package_data={
        "client": ["*.c", "*.cpp"],
        "server": ["*.c", "*.cpp"],
        "gui": ["*.c", "*.cpp"],
    },
    zip_safe=False,
)