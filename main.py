import tkinter
from tkinter import ttk
import logging
import re

###                 ###
###     GLOBALS     ###
###                 ###

logger = logging.getLogger(__name__)

ROWS: int = 5
COLS: int = 5

LETTER_REGEX = re.compile(r'^[A-Za-z]$') # Regex to match single letter.


def main() -> None:
    logging_setup()
    logger.info("Starting app...")
    setup_gui()


###             ###
###     GUI     ###
###             ###


def setup_gui():
    logger.info("Setting up GUI")
    root = tkinter.Tk()
    frame = tkinter.ttk.Frame(root, padding=10)
    frame.grid()
    tkinter.ttk.Label(frame, text="Crossword Solver").grid(column=0, row=0)
    tkinter.ttk.Button(frame, text="Quit", command=root.destroy).grid(column=1, row=0)
    entries, vars_grid = setup_crossword_grid(root, ROWS, COLS)

    root.mainloop()

def setup_crossword_grid(root: tkinter.Tk, rows: int=5, cols: int=5):
    logger.debug(f"Setting up crossword grid with cols={cols} rows={rows}.")

    entries = []
    vars_grid = []

    # For input validation.
    def make_trace_callback(strvar: tkinter.StringVar):
        def callback(*_):
            value = strvar.get()
            if value == "":
                return
            if(len(value)>1):
                value = value[0]
            value_upper = value.upper()
            if(LETTER_REGEX.fullmatch(value_upper)):
                if value_upper != strvar.get():
                    strvar.set(value_upper)
            else:
                strvar.set('')
            
        return callback

    # Go through each row and dynamically setup the cells with entry and stringvar.
    for row in range(1, rows+1):
        row_entries = []
        row_vars = []
        for col in range(1, cols+1):
            sv = tkinter.StringVar()
            sv.trace_add('write', make_trace_callback(sv))
            e = tkinter.Entry(
                root,
                textvariable=sv,
                width=2,
                justify='center'
            ).grid(row=row, column=col, padx=2, pady=2)
            
            row_entries.append(e)
            row_vars.append(sv)
            logger.debug(f"Added [Entry: {e}] at ({row},{col}).")
        entries.append(row_entries)
        vars_grid.append(row_vars)

    return entries, vars_grid


###             ###
###     UTIL    ###
###             ###

def logging_setup():
    logging.basicConfig(
        filename="csolver.log", 
        format='(%(asctime)s) [%(filename)s:%(funcName)s:%(levelname)s]:: %(message)s', 
        datefmt='%d/%m/%Y %I:%M:%S %p', 
        level=logging.DEBUG)

if __name__=='__main__':
    main()