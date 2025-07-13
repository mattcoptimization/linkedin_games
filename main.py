"""Automated LinkedIn Queens game solver.

Set env variables LINKEDIN_USERNAME and LINKEDIN_PASSWORD to use.

Requires installing playwright browsers (Chromium) using `uv run playwright install`
"""

from pydantic import BaseModel, Field
from ortools.sat.python import cp_model
import os
import re
from playwright.sync_api import sync_playwright, Page
from time import sleep, perf_counter

class Position(BaseModel):
    row: int
    col: int
    

class QueensTable(BaseModel):
    colors: dict[int, list[tuple[int,int]]] = Field(description="For each color index (key), list the positions that color exists in", default_factory=lambda: {})
    solution: list[Position] = Field(description="Contains the positions of queens in the solution", default_factory=lambda: [])


def linkedin_login(page: Page) -> None:
    """Uses playwright to pass the login screen of linkedin.
    
    NOTE: Must set env vars of LINKEDIN_USERNAME and LINKEDIN_PASSWORD.
    """
    username_field = page.get_by_label("Email or phone")
    username_field.click()
    username_field.fill(value=os.getenv("LINKEDIN_USERNAME"))
    sleep(1)
    password_field = page.get_by_label("Password")
    password_field.click()
    password_field.fill(value=os.getenv("LINKEDIN_PASSWORD"))
    sleep(1)
    # Sign in button class has duplicate label
    sign_in_button = page.locator('.btn__primary--large.from__button--floating')
    sign_in_button.click()
    sleep(5)
    

def linkedin_navigate_to_queens(page: Page) -> None:
    """Uses playwright to navigate to queens page."""

    page.goto("https://linkedin.com/games/queens/")
    sleep(5)

def read_queens_table(page: Page) -> QueensTable:
    """Use playwright to read the table into the pydantic structure."""
    # Get the grid
    # Get by ID, grid contaisn all elements
    grid_element = page.locator("#queens-grid")

    table = QueensTable()

    # Get the number of rows
    rows_and_columns = grid_element.get_attribute("style")
    # The format is --rows: 9; --columns: 9
    # It is a square, so we just use regex to get rows
    pattern = r'--rows:\s*(\d+);'
    rows_match = re.search(pattern, rows_and_columns)
    if rows_match:
        n_rows = int(rows_match.group(1))
    
    # Get all of the cells and store
    all_cells = grid_element.locator(".queens-cell-with-border")

    # Iterate over cells
    for cell_number in range(all_cells.count()):
        element = all_cells.nth(cell_number)
        # Row major order
        row = cell_number // n_rows
        col = cell_number % n_rows
        # Get the class
        total_string = element.get_attribute("class")
        # Find the color index using regex
        color_idx = int(re.search(r"cell-color-(\d+)", total_string).group(1))

        if not color_idx in table.colors:
            table.colors[color_idx] = []
        # Store
        table.colors[color_idx].append((row, col))
        
        
    return table


def create_model_ortools(queens_table: QueensTable) -> tuple[cp_model.CpModel, dict]:
    """Use queens table to create model"""
    model = cp_model.CpModel()

    n_size = len(queens_table.colors)
    print(f"Creating model for {n_size}x{n_size} grid")

    # Create boolean variables for each cell position
    queen_vars = {(i,j): model.NewBoolVar(f"queen_{i}_{j}") for i in range(n_size) for j in range(n_size)}

    # Exactly one queen per row
    _ = {i: model.AddExactlyOne((queen_vars[i,j] for j in range(n_size))) for i in range(n_size)}

    _ = {j: model.AddExactlyOne((queen_vars[i,j] for i in range(n_size))) for j in range(n_size)}


    # Constraint: No queens on neighboring diagonals
    directions = [(1, 1), (1, -1)]

    # Solve the diagonals, we only go down and iterate one at a time.
    for i in range(n_size):
        for j in range(n_size):
            for di, dj in directions:
                ni, nj = i + di, j + dj
                if 0 <= ni < n_size and 0 <= nj < n_size:
                    model.AddAtMostOne([queen_vars[(i, j)],queen_vars[(ni, nj)]])


    for color_idx, positions in queens_table.colors.items():
        # Sum all boolean variables in this color region and set to 1
        color_queens = [queen_vars[pos] for pos in positions]
        model.AddExactlyOne(color_queens)
        print(f"Color {color_idx}: {len(positions)} positions")

    return model, queen_vars


def solve_model_ortools(model: cp_model.CpModel) -> tuple[int, cp_model.CpSolver]:
    """Simple function to solve the model"""
    solver = cp_model.CpSolver()
    status = solver.solve(model)
    print(f"Solver status: {status}")
    if status == cp_model.OPTIMAL:
        print("Solution found (OPTIMAL)!")
    elif status == cp_model.FEASIBLE:
        print("Solution found (FEASIBLE)!")
    elif status == cp_model.INFEASIBLE:
        print("Problem is INFEASIBLE")
    elif status == cp_model.UNKNOWN:
        print("Status is UNKNOWN")
    else:
        print(f"Unexpected status: {status}")
    return status, solver


def parse_model_results(queens_table: QueensTable, solver: cp_model.CpSolver, queen_vars: dict) -> QueensTable:
    """Function to take queen values and put them into the table"""
    n_size = len(queens_table.colors)

    queens_table.solution.extend([Position(row=i, col=j) for i in range(n_size) for j in range(n_size) if solver.Value(queen_vars[i,j]) == 1])
    
    
    return queens_table


def fill_out_linkedin(page: Page, queens_table: QueensTable) -> None:
    """Uses playwright to fill out the results."""
    n_size = len(queens_table.colors)

    grid_element = page.locator("#queens-grid")

    for pos in queens_table.solution:
        cell_index = pos.row * n_size + pos.col

        cell = grid_element.locator(".queens-cell-with-border").nth(cell_index)

        cell.click()

        sleep(0.2)
        
        cell.click()
    
    sleep(5)

def main():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        page = browser.new_page(viewport={'width': 1600, 'height': 900})
        sleep(1)
        page.goto("https://www.linkedin.com/login")
        sleep(1)
        # Login and go to queens
        linkedin_login(page=page)
        linkedin_navigate_to_queens(page=page)
        start_time = perf_counter()
        # Read in the table
        queens_table = read_queens_table(page=page)
        
        # Solve the puzzle
        model, queen_vars = create_model_ortools(queens_table=queens_table)
        status, solver = solve_model_ortools(model)
        
        # Parse results and interact with LinkedIn to fill out the puzzle
        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            queens_table = parse_model_results(queens_table=queens_table, solver=solver, queen_vars=queen_vars)
            fill_out_linkedin(page=page, queens_table=queens_table)
        else:
            print("Cannot proceed without a valid solution")
        end_time = perf_counter()

        total_time = end_time - start_time

        print(f"Time elapsed: {total_time:.2f}")
        
        browser.close()


if __name__ == "__main__":
    main()