import tkinter
from tkinter import ttk
import logging

logger = logging.getLogger(__name__)

ROWS: int = 5
COLS: int = 5

def main() -> None:
    logging_setup()
    logger.info("Starting app...")
    setup_gui()

def setup_gui():
    logger.info("Setting up GUI")
    root = tkinter.Tk()
    frame = tkinter.ttk.Frame(root, padding=10)
    frame.grid()
    tkinter.ttk.Label(frame, text="Crossword Solver").grid(column=0, row=0)
    tkinter.ttk.Button(frame, text="Quit", command=root.destroy).grid(column=1, row=0)
    setup_crossword_grid(root, ROWS, COLS)
    root.mainloop()

def setup_crossword_grid(root: tkinter.Tk, rows: int=5, cols: int=5):
    logger.debug(f"Setting up crossword grid with cols={cols} rows={rows}.")

    def on_validate(txt: str) -> bool:
        return len(txt) <= 1

    valcmd = (root.register(on_validate), '%P')

    for row in range(1, rows+1):
        for col in range(1, cols+1):
            tkinter.Entry(
                root,
                width=2,
                justify='center',
                validate='key',
                validatecommand=valcmd
            ).grid(row=row, column=col, padx=2, pady=2)

def logging_setup():
    logging.basicConfig(
        filename="csolver.log", 
        format='(%(asctime)s) [%(filename)s:%(funcName)s:%(levelname)s]:: %(message)s', 
        datefmt='%d/%m/%Y %I:%M:%S %p', 
        level=logging.DEBUG)

if __name__=='__main__':
    main()