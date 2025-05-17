import importlib
import inspect
import pkgutil
import sys


def discover_tests(package_name="tests"):
    package = importlib.import_module(package_name)
    for _, modname, _ in pkgutil.iter_modules(package.__path__):
        module = importlib.import_module(f"{package_name}.{modname}")
        for name, obj in inspect.getmembers(module):
            if name.startswith("test_") and inspect.isfunction(obj):
                yield f"{modname}.{name}", obj


def main():
    failures = 0
    tests = list(discover_tests())
    for name, func in tests:
        try:
            func()
            print(f"PASS {name}")
        except AssertionError as e:
            failures += 1
            print(f"FAIL {name}: {e}")
    if failures:
        print(f"{failures} tests failed")
        sys.exit(1)
    print(f"{len(tests)} tests passed")


if __name__ == "__main__":
    main()
