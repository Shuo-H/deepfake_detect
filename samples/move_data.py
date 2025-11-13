import glob
import os

# Define the path and the pattern
directory_path = "/ocean/projects/cis220031p/shan1/data_ck/asvproof5/datasets/flac_E_eval/"
pattern = "*.flac"  # Example: Find all .flac files

# Join the path and pattern
search_pattern = os.path.join(directory_path, pattern)

# glob.glob() returns a list of all matching files
file_list = glob.glob(search_pattern)

# You can now loop over the list
print(f"Found {len(file_list)} files.")
for file_path in file_list[:10]:
    # move the file to the current directory
    filename = os.path.basename(file_path)
    new_path = os.path.join(os.getcwd(), filename)
    os.rename(file_path, new_path)
    print(f"Moved: {file_path} to {new_path}")