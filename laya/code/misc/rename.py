import os
import shutil

def copy_and_rename_files_in_directory(src_directory, dest_directory, kanda):
    files = [f for f in os.listdir(src_directory) if f.endswith('.mp3')]
    files.sort()
    
    if not os.path.exists(dest_directory):
        os.makedirs(dest_directory)
    
    for index, file in enumerate(files):
        new_name = f"{index + 1}.mp3"
        shutil.copy(os.path.join(src_directory, file), os.path.join(dest_directory, new_name))

def main():
    base_directory = 'audio'
    new_base_directory = 'new_audio'
    for kanda in range(1, 7):
        src_directory = os.path.join(base_directory, str(kanda))
        dest_directory = os.path.join(new_base_directory, str(kanda))
        if os.path.exists(src_directory):
            copy_and_rename_files_in_directory(src_directory, dest_directory, kanda)
        else:
            print(f"Directory {src_directory} does not exist")

if __name__ == "__main__":
    main()