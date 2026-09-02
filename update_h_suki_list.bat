@echo off
echo Generating H-Suki List (this may take a while)...
python generate_h_suki_list.py
echo Building HTML...
python build_gamelist_html.py
echo Done! R:\Gamelist\index.html has been updated.
pause
