import asyncio
import importlib.util

spec = importlib.util.spec_from_file_location("dtessera", "Dtessera Terra.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

async def main():
    if hasattr(mod, "main"):
        await mod.main()

asyncio.run(main())
