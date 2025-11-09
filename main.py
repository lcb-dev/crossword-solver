import os
import logging
import re
import tkinter
import nltk
import io
import contextlib
from random import choice
from string import ascii_letters
from nltk.corpus import words
from tkinter import ttk
from datetime import datetime
from typing import List, Tuple
from pathlib import Path

###                 ###
###     GLOBALS     ###
###                 ###

logger = logging.getLogger(__name__)

ROWS: int = 10
COLS: int = 10

ENTRIES: List[tkinter.Entry] = []
VARS_GRID: List[tkinter.StringVar] = []

LETTER_REGEX = re.compile(r'^[A-Za-z]$') # Regex to match single letter.

def main() -> None:
    logging_setup()
    logger.info("Starting app...")
    get_words_data()
    setup_gui()

###             ###
###     GUI     ###
###             ###

def setup_gui():

    def shutdown_app():
        logger.info("Quitting.\n")
        root.destroy()

    logger.info("Setting up GUI")
    root = tkinter.Tk()
    frame = tkinter.ttk.Frame(root, padding=10)
    frame.grid()
    ENTRIES, VARS_GRID = setup_crossword_grid(root, ROWS, COLS)
    tkinter.ttk.Label(frame, text="Crossword Solver").grid(column=0, row=0)
    tkinter.ttk.Button(frame, text="Quit", command=shutdown_app).grid(column=0, row=1)
    tkinter.ttk.Button(frame, text="Fill Letters", command=lambda: fill_random_letters(ENTRIES, VARS_GRID)).grid(column=0, row=2)
    
    root.mainloop()

def setup_crossword_grid(root: tkinter.Tk, rows: int=5, cols: int=5) -> Tuple[List[tkinter.Entry],List[tkinter.StringVar]]:
    logger.debug(f"Setting up crossword grid with cols={cols} rows={rows}.")

    entries = []
    vars_grid = []

    # For input validation.
    def make_trace_callback(strvar: tkinter.StringVar, row: int, col: int):
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
            logger.info(f"[{row},{col}] Value: {strvar.get()}.")
            
        return callback

    # Go through each row and dynamically setup the cells with entry and stringvar.
    for row in range(1, rows+1):
        row_entries: List[tkinter.Entry] = []
        row_vars: List[tkinter.StringVar] = []
        for col in range(1, cols+1):
            sv = tkinter.StringVar()
            sv.trace_add('write', make_trace_callback(sv, row, col))
            e = tkinter.Entry(
                root,
                textvariable=sv,
                width=2,
                justify='center'
            )
            e.grid(row=row, column=col, padx=2, pady=2)
            
            row_entries.append(e)
            row_vars.append(sv)
            logger.debug(f"Added [Entry: {e}] at ({row},{col}).")
        entries.append(row_entries)
        vars_grid.append(row_vars)
        logger.debug(f"Row [{row}] added.\n")

    logger.debug(f"Final row entries: {entries}")
    logger.debug(f"Final row vars: {row_vars}\n")
    return entries, vars_grid


###             ###
###     UTIL    ###
###             ###

def logging_setup() -> None:
    logfile_directory = "logs"
    if not os.path.exists(logfile_directory):
        os.makedirs(logfile_directory)

    logfile_name = f"csolver-{datetime.now().strftime("%d-%m-%Y_%H-%M-%S")}.log"
    logging.basicConfig(
        filename=logfile_directory+"/"+logfile_name, 
        format='(%(asctime)s) [%(filename)s:%(funcName)s:%(levelname)s]:: %(message)s', 
        datefmt='%d/%m/%Y %I:%M:%S %p', 
        level=logging.DEBUG)

def get_words_data():
    script_dir = Path(__file__).resolve().parent

    target_dir = script_dir / "nltk_data"
    target_dir.mkdir(parents=True, exist_ok=True)

    nltk.data.path.insert(0, str(target_dir))

    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(buffer):
        nltk.download('words', download_dir=str(target_dir), quiet=False, prefix="[NLTK]", print_error_to=buffer)
        print("Downloaded")

    captured = buffer.getvalue().strip()
    print(captured)
    if (captured):
        for line in captured.splitlines():
            line=line.strip()
            if line:
                logger.info(f"{line}")

    logger.info(f"Loaded words: {len(words.words())}\n")

###                   ###
###     BEHAVIOUR     ###
###                   ###

def fill_random_letters(entries, vars_grid, rows=ROWS,cols=COLS) -> None:
    logger.info(f"Filling random letters in grid from (0,0) to ({rows},{cols})")
    for row_vars in vars_grid:
        for var in row_vars:
            var.set(choice(ascii_letters).upper())
    pass

if __name__=='__main__':
    main()