class Symbol:
    def __init__(self, name, dtype, offset, line):
        self.name = name
        self.dtype = dtype
        self.offset = offset
        self.lines = [line]

    def add_line(self, line):
        if line not in self.lines:
            self.lines.append(line)

class SymbolTable:
    def __init__(self):
        # List of dictionaries for scoping. Index 0 is global scope.
        self.scopes = [{}]
        self.current_offset = 0
        
        # Keep track of all symbols for final rendering (if needed)
        self.all_symbols = []

    def enter_scope(self):
        self.scopes.append({})

    def exit_scope(self):
        if len(self.scopes) > 1:
            self.scopes.pop()
            
    # =========================================================================
    # TINY EQUIVALENT: st_insert()
    # -------------------------------------------------------------------------
    # In the TINY compiler, this was typically handled by st_insert() in symtab.c.
    # It stores the variable's attributes and memory location (offset).
    # =========================================================================
    def insert(self, name, dtype, line):
        current_scope = self.scopes[-1]
        if name in current_scope:
            return False # Duplicate identifier in the same scope
        
        # Simple memory offset calculation based on data type size
        size = 4
        if dtype == "float": size = 8
        elif dtype == "bool": size = 1

        sym = Symbol(name, dtype, self.current_offset, line)
        current_scope[name] = sym
        self.all_symbols.append(sym)
        self.current_offset += size
        return True

    # =========================================================================
    # TINY EQUIVALENT: st_lookup()
    # -------------------------------------------------------------------------
    # In the TINY compiler, st_lookup() searches the hash table for a memory
    # location. Here, we search from the innermost scope (local) to the 
    # outermost scope (global) mimicking lexical scoping rules.
    # =========================================================================
    def lookup(self, name):
        # Search from innermost scope to outermost (Stack LIFO)
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None

    def add_reference(self, name, line):
        """Updates the lines list where this symbol is used (similar to LineList in TINY)."""
        sym = self.lookup(name)
        if sym:
            sym.add_line(line)
            return True
        return False
