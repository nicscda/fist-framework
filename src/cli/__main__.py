from ..utils.functions import apply_monkey_patches
from .main import cli as main

if __name__ == "__main__":
    apply_monkey_patches()
    main()  # pylint: disable=no-value-for-parameter
