assignments = []

rows = 'ABCDEFGHI'
cols = '123456789'
digits = '123456789'

def cross(a, b):
    return [s + t for s in a for t in b]

boxes = cross(rows, cols)
row_units = [cross(r, cols) for r in rows]
column_units = [cross(rows, c) for c in cols]
square_units = [cross(rs, cs) for rs in ('ABC', 'DEF', 'GHI') for cs in ('123', '456', '789')]
unitlist = row_units + column_units + square_units
units = dict((s, [u for u in unitlist if s in u]) for s in boxes)
peers = dict((s, set(sum(units[s], [])) - set([s])) for s in boxes)
# for diagonal sudoku
diagonal_units =[[r+cols[i] for i, r in enumerate(rows)], [t[0]+t[1] for t in zip(rows, cols[::-1])]]
[[peers[s].update(set(du)- set([s])) for s in du] for du in diagonal_units]

def display(values):
    """
    Display the values as a 2-D grid.
    Input: The sudoku in dictionary form
    Output: None
    """
    width = 1 + max(len(values[s]) for s in boxes)
    line = '+'.join(['-' * (width * 3)] * 3)
    for r in rows:
        print(''.join(values[r + c].center(width) + ('|' if c in '36' else '')
                      for c in cols))
        if r in 'CF': print(line)
    return

def grid_values(grid):
    """
    Convert grid into a dict of {square: char} with '123456789' for empties.
    Input: A grid in string form.
    Output: A grid in dictionary form
            Keys: The boxes, e.g., 'A1'
            Values: The value in each box, e.g., '8'. If the box has no value, then the value will be '123456789'.
    """
    return {boxes[i] : g if g != '.' else digits for i, g in enumerate(grid)}

def assign_value(values, box, value):
    """
    Please use this function to update your values dictionary!
    Assigns a value to a given box. If it updates the board record it.
    """
    # Don't waste memory appending actions that don't actually change any values
    if values[box] == value:
        return values

    values[box] = value
    if len(value) == 1:
        assignments.append(values.copy())
    return values

def remove_twin_values(values, arr, twin_d):
    unsolved = [k for k in arr if len(values[k]) > 2]
    changed = False
    for s in unsolved:
        s_value = set(values[s])
        s_new_value = s_value - twin_d
        if s_value != s_new_value:
            changed = True
            new_value = "".join(sorted(list(s_new_value)))
            values[s] = new_value
    return values, changed

def naked_twins(values):
    """Eliminate values using the naked twins strategy.
    Args:
        values(dict): a dictionary of the form {'box_name': '123456789', ...}

    Returns:
        the values dictionary with the naked twins eliminated from peers.
    """
    stalled = False
    while not stalled:
        two_values = {k: v for k, v in values.items() if len(v) == 2}
        if two_values and len(two_values) > 1:
            twins = []
            c_changed = 0
            for k, v in two_values.items():
                if k not in twins:
                    for p in peers[k]:
                        if values[p] == v:        # we have twin
                            changed = False
                            twins.append(p)       # so do not  process it again
                            if k[0] == p[0]:      # same rows
                                values, changed = remove_twin_values(values, row_units[rows.index(k[0])], set(v))
                            elif k[1] == p[1]:    # dame column
                                values, changed = remove_twin_values(values, column_units[cols.index(k[1])], set(v))
                            else:
                                for sq in square_units:
                                    if k in sq and p in sq:
                                        values, changed = remove_twin_values(values, sq, set(v))
                                        break
                            if changed:
                                c_changed += 1
                            break                 # only one pair
            stalled = c_changed == 0
        else:
            stalled = True
    return values

def eliminate(values):
    """
    Go through all the boxes, and whenever there is a box with a value, eliminate this value from the values of all its peers.
    Input: A sudoku in dictionary form.
    Output: The resulting sudoku in dictionary form.
    """
    solved_values = [k for k, v in values.items() if len(v) == 1]
    for box in solved_values:
        digit = values[box]
        for peer in peers[box]:
            values[peer] = values[peer].replace(digit, '')
    return values

def only_choice(values):
    """
    Go through all the units, and whenever there is a unit with a value that only fits in one box, assign the value to this box.
    Input: A sudoku in dictionary form.
    Output: The resulting sudoku in dictionary form.
    """
    changed = 0
    for unit in unitlist:
        for digit in '123456789':
            dplaces = [box for box in unit if digit in values[box]]
            if len(dplaces) == 1 and len(values[dplaces[0]]) > 1:
                values[dplaces[0]] = digit
                changed += 1
    return values, changed == 0

def reduce_puzzle(values):
    """
    Iterate eliminate() and only_choice(). If at some point, there is a box with no available values, return False.
    If the sudoku is solved, return the sudoku.
    If after an iteration of both functions, the sudoku remains the same, return the sudoku.
    Input: A sudoku in dictionary form.
    Output: The resulting sudoku in dictionary form.
    """
    stalled = False
    while not stalled:
        values = naked_twins(values)
        values = eliminate(values)
        values, stalled = only_choice(values)
        if '' in values.values():
            return False
    return values

def search(values):
    values = reduce_puzzle(values)
    if not values:
        return False
    if all(len(v) == 1 for v in values.values()):
        return values
    unsolved = {k: v for k, v in values.items() if len(v) > 1}
    if unsolved:
        sorted_unsolved = sorted(unsolved.items(), key=lambda x: len(x[1]))
        for s, v in sorted_unsolved:
            for d in v:
                copy_of_values = values.copy()
                copy_of_values[s] = d
                attempt = search(copy_of_values)
                if attempt:
                    return attempt

def solve(grid):
    """
    Find the solution to a Sudoku grid.
    Args:
        grid(string): a string representing a sudoku grid.
            Example: '2.............62....1....7...6..8...3...9...7...6..4...4....8....52.............3'
    Returns:
        The dictionary representation of the final sudoku grid. False if no solution exists.
    """
    assert len(grid) == 81
    values = grid_values(grid)
    values = search(values)
    return values

if __name__ == '__main__':
    diag_sudoku_grid = '2.............62....1....7...6..8...3...9...7...6..4...4....8....52.............3'
    values = solve(diag_sudoku_grid)
    if values:
        display(values)
    else:
        print("Cannot find solution for %s" % diag_sudoku_grid)
    try:
        from visualize import visualize_assignments
        visualize_assignments(assignments)

    except SystemExit:
        pass
    except:
        print('We could not visualize your board due to a pygame issue. Not a problem! It is not a requirement.')
