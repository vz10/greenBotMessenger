cd D:\home\site\wwwroot
if not exist \home\site\wwwroot\venv\Scripts\activate call D:\Python27\Scripts\virtualenv.exe venv
call .\venv\Scripts\activate
call pip install -r requirements.txt