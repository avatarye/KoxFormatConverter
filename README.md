# KoxFormatConverter
Format converter for ePub files from kox.moe. To run it, use this command:
```bash
poetry run python src/koxformatconverter/run.py <input_file>

```
The input_file is the absolute file path to the ePub file you want to convert. The output file will be saved in the same directory as the input file with the same name but with the extension .cbz. Use "??" to replace the number in the file name, the programm will search other files with the same name within the same directory.