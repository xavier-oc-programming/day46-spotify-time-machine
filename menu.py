import os
import sys
import subprocess
from pathlib import Path

from art import LOGO


def main():
    clear = True
    while True:
        if clear:
            os.system("cls" if os.name == "nt" else "clear")
        clear = True

        print(LOGO)
        print("Select a build to run:")
        print("  1. Original  — course version (original/main.py)")
        print("  2. Advanced  — OOP refactor  (advanced/main.py)")
        print("  q. Quit")
        print()

        choice = input("Enter choice: ").strip().lower()

        if choice == "1":
            path = Path(__file__).parent / "original" / "main.py"
            subprocess.run([sys.executable, str(path)], cwd=str(path.parent))
            input("\nPress Enter to return to menu...")
        elif choice == "2":
            path = Path(__file__).parent / "advanced" / "main.py"
            subprocess.run([sys.executable, str(path)], cwd=str(path.parent))
            input("\nPress Enter to return to menu...")
        elif choice == "q":
            break
        else:
            print("Invalid choice. Try again.")
            clear = False


if __name__ == "__main__":
    main()
