import importlib.util

spec = importlib.util.spec_from_file_location("dtessera", "Dtessera Terra.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
