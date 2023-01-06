del dist\*
python setup.py bdist_wheel --universal
gpg --detach-sign -u FA31DF0C -a dist/*
twine upload dist/*
pause
