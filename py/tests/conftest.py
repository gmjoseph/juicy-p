# Ensures that the modules can be imported into tests
import sys
from pathlib import Path

path = Path(__file__).parent / '../src'
path = str(path.resolve())
sys.path.append(path)
