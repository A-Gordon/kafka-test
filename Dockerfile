FROM python:3.8.11
RUN groupadd -r appuser && useradd --no-log-init -r -g appuser appuser
WORKDIR /usr/src/app
COPY . .
RUN pip install -r requirements.txt
RUN chown -R appuser /usr/src/app
USER appuser
ENTRYPOINT ["python3"]
CMD ["data_stream.py"]
