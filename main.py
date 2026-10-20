"""Execute com Python 3.10 ou superior: python main.py."""
import tkinter as tk
from mancala.interface import Aplicativo


def main():
    janela = tk.Tk()
    Aplicativo(janela)
    janela.mainloop()


if __name__ == '__main__':
    main()
