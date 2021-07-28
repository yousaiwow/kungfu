import os
import sys

if __name__ == "__main__":
    py_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(py_dir)
    kfc_dir = os.path.join(base_dir, "dist", "kfc")
    sys.path.append(py_dir)
    sys.path.append(kfc_dir)
    os.environ["PATH"] += os.pathsep + kfc_dir
    sys.kf_sdk_home = kfc_dir
    from kungfu.__main__ import main

    main()
