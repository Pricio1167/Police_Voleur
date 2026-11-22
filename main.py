"""Application entry point."""

import tkinter as tk

from controller.game_controller import GameController


def main():
    root = tk.Tk()
    GameController(root)
    root.mainloop()


if __name__ == "__main__":
    main()
