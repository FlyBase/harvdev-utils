# A script regenerate the __init__.py file for production or reporting.

def main(): 
    filename = 'production.py'
    model_file = open(filename, "r")
    class_counter = 0

    with open('__init__.py', 'w') as initfile:
        for row in model_file:
            if row.startswith('class'): # If we encounter a class.
                row_truncated = row[6:]
                class_name = row_truncated.split("(")[0] # Grab everything from the title of the class name before the open parenthesis.
                line_to_write = 'from .production import ' + class_name + '\n'
                initfile.write(line_to_write)
                class_counter += 1
                
    print('Added %s entries to __init__.py' % (class_counter))
    
if __name__ == "__main__":
    main()