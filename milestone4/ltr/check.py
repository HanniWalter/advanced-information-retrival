def count_lines_contained(file_path_a, file_path_b):
    try:
        # Open the first file (a) and read its lines
        with open(file_path_a, 'r') as file_a:
            lines_a = set(file_a.read().splitlines())

        # Open the second file (b) and read its lines
        with open(file_path_b, 'r') as file_b:
            lines_b = set(file_b.read().splitlines())

        # Count the number of lines from file_a contained in file_b
        lines_contained = lines_a.intersection(lines_b)
        num_lines_contained = len(lines_contained)

        print(f"{num_lines_contained} lines from {file_path_a} are contained in {file_path_b}")

    except FileNotFoundError:
        print("One or both of the specified files not found.")

# Example usage
# file_path_a = input("Enter the path of the first file: ")
# file_path_b = input("Enter the path of the second file: ")

count_lines_contained("output.txt", "output2.txt")