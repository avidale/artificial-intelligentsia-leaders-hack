For local testing you can run 

python app.py

and install requirements if needed

pip install -r requirements.txt

for production

sudo apt-get install gunicorn3

or if you use venv 

pip install gunicorn

and for launch server

gunicorn3 --timeout 200 --bind 0.0.0.0:3227 app:app
