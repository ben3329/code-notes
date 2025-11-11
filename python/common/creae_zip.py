import os
from tempfile import TemporaryDirectory
from zipfile import ZipFile

FILENAME = "example.zip"
DIRNAME = "example_dir"
temp_dir = TemporaryDirectory(delete=False)
zip_file = ZipFile(f"{temp_dir.name}/{FILENAME}", "w")
for foldername, subfolders, filenames in os.walk(f"{temp_dir.name}/{DIRNAME}"):
    for filename in filenames:
        file_path = os.path.join(foldername, filename)
        zip_file.write(
            file_path,
            os.path.relpath(
                file_path,
                os.path.join(temp_dir.name, DIRNAME),
            ),
        )
zip_file.close()
