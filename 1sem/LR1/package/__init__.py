from .utils import function

__version__ = "1.0.0"
__author__ = "MelnikNO"

def package_first():
    return f"Package {__name__} version {__version__}"

__all__ = ['package_first', 'function']