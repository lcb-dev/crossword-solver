import os, sys
import logging
import re
import tkinter
import nltk
import io
import contextlib
import requests, json, time
from random import choice
from string import ascii_letters
from nltk.corpus import words
from tkinter import ttk
from datetime import datetime
from typing import List, Tuple, Optional
from pathlib import Path

###                 ###
###     GLOBALS     ###
###                 ###

logger = logging.getLogger(__name__)

ROWS: int = 10
COLS: int = 10

ENTRIES: List[tkinter.Entry] = []
VARS_GRID: List[tkinter.StringVar] = []

VALID_WORDS = set(words.words())
print(sys.getsizeof(VALID_WORDS)," bytes [set]")
print(sys.getsizeof(words.words())," bytes [raw]")

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
    tkinter.ttk.Button(frame, text="Solve Words", command=lambda: get_words_in_crossword(VARS_GRID, ENTRIES)).grid(column=0, row=3)
    
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
    for r in range(ROWS):
        for c in range(COLS):
            entries[r][c].config(bg="white")
    for row_vars in vars_grid:
        for var in row_vars:
            var.set(choice(ascii_letters).upper())

def get_words_in_crossword(vars_grid, entries_grid):
    """
    Scan a crossword grid for valid words in all four directions and highlight them.
    """
    valid_words = VALID_WORDS
    found_words = {}
    directions = {
        "right": (0, 1),
        "down": (1, 0),
        "left": (0, -1),
        "up": (-1, 0)
    }

    def get_letter(r, c):
        if 0 <= r < ROWS and 0 <= c < COLS:
            return vars_grid[r][c].get().lower()
        return None

    def scan_direction(row, col, dr, dc):
        """Scan a direction from a starting cell and return found words with positions."""
        letters = []
        positions = []
        r, c = row, col
        while 0 <= r < ROWS and 0 <= c < COLS:
            letter = get_letter(r, c)
            if not letter:
                break
            letters.append(letter)
            positions.append((r, c))
            # Generate all possible word candidates from this prefix
            for length in range(2, len(letters)+1):
                word_candidate = ''.join(letters[:length])
                if word_candidate in valid_words and len(word_candidate) > 2:
                    real_word, _ = is_real_word(word_candidate)
                    if real_word:
                        found_words[(positions[0], positions[length-1])] = word_candidate
            r += dr
            c += dc

    # Reset all cell colors
    for r in range(ROWS):
        for c in range(COLS):
            entries_grid[r][c].config(bg="white")

    # Scan every cell in every direction
    for row in range(ROWS):
        for col in range(COLS):
            if get_letter(row, col):
                for dr, dc in directions.values():
                    scan_direction(row, col, dr, dc)

    # Highlight found words
    for (start, end), word in found_words.items():
        sr, sc = start
        er, ec = end
        for r, c in positions_between(start, end):
            entries_grid[r][c].config(bg='lightgreen')

    # Print results
    for idx, (coords, word) in enumerate(found_words.items(), 1):
        real_word, definition = is_real_word(word)
        if real_word:
            print(f"[{idx}] {coords} {word:<10} - Definition: {definition}")

    found_words.clear()


def positions_between(start, end):
    """Yield all grid positions between start and end inclusive (supports straight lines)."""
    sr, sc = start
    er, ec = end
    dr = (er - sr) // max(1, abs(er - sr)) if er != sr else 0
    dc = (ec - sc) // max(1, abs(ec - sc)) if ec != sc else 0
    r, c = sr, sc
    while (r, c) != (er + dr, ec + dc):
        yield r, c
        r += dr
        c += dc

def is_real_word(word: str) -> Tuple[bool,str]:
    time.sleep(0.5)
    try:
        req = requests.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}")
        data = req.json()
        definition = data[0]["meanings"][0]["definitions"][0]["definition"]
        return True, definition
    except Exception:
        # Not a word with a known definition, return false. 
        return False, "Not a real word."

if __name__=='__main__':
    main()
