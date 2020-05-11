FROM python:3.6

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

COPY . .

RUN rm -rf .git

EXPOSE 8000

USER www-data

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
