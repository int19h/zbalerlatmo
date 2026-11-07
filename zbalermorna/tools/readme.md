# Tools

If you use Sublime Text on Windows, you can create a new build system for Livescript if you have msys2 installed:

```
{
    "cmd": ["lsc", "${file_path}/${file_name}", ">", "${file_path}/${file_base_name}"],
    "file_regex": "^(..[^:]*):([0-9]+):?([0-9]+)?:? (.*)$",
    "working_dir": "${file_path}",
    "path": "D:/msys64/mingw64/bin/",
    "shell": true
}
```

Which will automatically create `ligatures.ps` from a `ligatures.ps.ls` file when pressing Ctrl+b.