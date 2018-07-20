cd D:\home\site\wwwroot
if not exist D:\home\site\wwwroot\venv\Scripts\activate call D:\Python27\Scripts\virtualenv.exe venv
call D:\home\site\wwwroot\venv\Scripts\easy_install.exe -U pip
call D:\home\site\wwwroot\venv\Scripts\pip.exe install -r D:\home\site\wwwroot\requirements.txt