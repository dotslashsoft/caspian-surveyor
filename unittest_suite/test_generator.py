import ast
import os
import sys

def generate_test_file(target_file):
    if not os.path.exists(target_file):
        print(f"Error: File '{target_file}' not found.")
        return

    with open(target_file, "r", encoding="utf-8") as f:
        node = ast.parse(f.read(), filename=target_file)

    # Extract module name for imports
    module_name = os.path.splitext(os.path.basename(target_file))[0]
    
    # Track items to test
    functions = []
    classes = {}

    # Parse top-level structures using Abstract Syntax Trees (AST)
    for body_item in node.body:
        if isinstance(body_item, ast.FunctionDef):
            # Ignore private/dunder functions
            if not body_item.name.startswith("_"):
                functions.append(body_item.name)
        elif isinstance(body_item, ast.ClassDef):
            if not body_item.name.startswith("_"):
                classes[body_item.name] = []
                for class_item in body_item.body:
                    if isinstance(class_item, ast.FunctionDef):
                        # Capture public class methods
                        if not class_item.name.startswith("_") or class_item.name == "__init__":
                            classes[body_item.name].append(class_item.name)

    # Generate the boilerplate output text
    output = []
    output.append("import unittest")
    
    # Build explicit import statements
    import_targets = functions + list(classes.keys())
    if import_targets:
        output.append(f"from {module_name} import {', '.join(import_targets)}")
    else:
        output.append(f"import {module_name}")
    output.append("\n")

    # Generate tests for top-level functions
    if functions:
        output.append(f"class Test{module_name.capitalize()}Functions(unittest.TestCase):")
        for func in functions:
            output.append(f"    def test_{func}(self):")
            output.append(f"        # TODO: Test {func}")
            output.append(f"        pass\n")
        output.append("")

    # Generate tests for classes and their methods
    for class_name, methods in classes.items():
        output.append(f"class Test{class_name}(unittest.TestCase):")
        output.append(f"    def setUp(self):")
        output.append(f"        # TODO: Initialize instance if needed")
        output.append(f"        pass\n")
        
        for method in methods:
            clean_name = "init" if method == "__init__" else method
            output.append(f"    def test_{clean_name}(self):")
            output.append(f"        # TODO: Test {class_name}.{method}")
            output.append(f"        pass\n")
        output.append("")

    # Add standard main execution wrapper
    output.append("if __name__ == '__main__':")
    output.append("    unittest.main()")

    # Write the output to a test_ file
    test_filename = f"test_{module_name}.py"
    with open(test_filename, "w", encoding="utf-8") as f:
        f.write("\n".join(output))

    print(f"Successfully generated: {test_filename}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python unittest_generator.py <path_to_python_file.py>")
    else:
        generate_test_file(sys.argv[1])