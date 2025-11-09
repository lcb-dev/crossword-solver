import os
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

VALID_WORDS = set(words.words())

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
        1. Interate over each letter in the grid. 
        2. For each letter, iterate over directions (up, down, left, right)
        3. Go to the next letter in that direction, begin building a char array. Go until edge of grid.
        4. Once full char array is built, try combinations of first letter + N consecutive letters and see if it is a word in NLTK words list.
        5. If a word is found, log for now [example: 'help' if full string is: ['h','e','l','p','f','u','l']. If still more letters, continue [example: Now 'helpful', as continued down line.]
        6. Do this for every direction, for every letter. Keep a dict of words found tied to their coordinates some how. Example: (0,0)-(0,4):'help'. 
        7. Once finished, iterate over all words found and their coordinates and print.
    """
    valid_words = VALID_WORDS
    found_words = {}

    directions = {
        "right": (0, 1),
        "down": (1, 0),
        "left": (0, -1),
        "up": (-1, 0)
    }

    # Helper - safely get letter at location.
    def get_letter(row, col):
        if((0 <= row < ROWS) and (0 <= col < COLS)):
            return vars_grid[row][col].get().lower()
        return None

    # reset all cell colours.
    for r in range(ROWS):
        for c in range(COLS):
            entries_grid[r][c].config(bg="white")

    for row in range(ROWS):
        for col in range(COLS):
            first_letter = get_letter(row, col)
            if not first_letter:
                continue

            for direction, (dir_row, dir_col) in directions.items():
                letters = [first_letter]
                positions = [(row, col)]

                next_row, next_col = row + dir_row, col + dir_col

                while ((0 <= next_row < ROWS) and (0 <= next_col < COLS)):
                    letter = get_letter(next_row, next_col)
                    if not letter:
                        break
                    letters.append(letter)
                    positions.append((next_row, next_col))
                    next_row += dir_row
                    next_col += dir_col
                
                for length in range(2, len(letters)+1):
                    word_candidate = ''.join(letters[:length])
                    if word_candidate in valid_words and len(word_candidate) > 2:
                        real_word, _ = is_real_word(word_candidate)
                        if(real_word):
                            found_words[(positions[0], positions[length-1])] = word_candidate
                            logger.debug(f"Added word: {word_candidate}")
                        else:
                            logger.debug(f"Skipping word without definition: {word_candidate}")

                        
    for (start, end), word in found_words.items():
        sr, sc = start
        er, ec = end
        if sr == er:  # horizontal
            for c in range(sc, ec+1):
                entries_grid[sr][c].config(bg='lightgreen')
        else:  # vertical
            for r in range(sr, er+1):
                entries_grid[r][sc].config(bg='lightgreen')

    counter = 0
    for coords, word in found_words.items():
        counter+=1
        real_word, definition = is_real_word(word)
        if(real_word):
            print(f"[{counter}] {coords} {word:<10} - Definition: {definition}")
        
    found_words.clear()


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
