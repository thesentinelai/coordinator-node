# coordinator-node
The Coordinator Node for The Sentinel AI

## 1. Installation
1. Python Dependencies ```pip3 install -r requirements.txt```
2. Gunicorn ```apt install gunicorn3```

## 2. Running the code
```
sudo gunicorn3 app:app --workers 3 --threads=2 --bind 0.0.0.0:5005 --log-file app.log --access-logfile access.log --log-level DEBUG
```

## 3. Code Linting
```
pylint --rcfile=pylintrc app.py
```
