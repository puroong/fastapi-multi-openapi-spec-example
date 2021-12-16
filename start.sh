echo "current python version:" $(python --version)
echo "PYTHON 3.7.2 IS RECOMMEDED"
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

uvicorn main:openapi_app --reload
