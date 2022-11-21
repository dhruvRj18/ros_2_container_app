FROM python:3.9

ENV VIRTUAL_ENV="/opt/venv"
RUN python -m venv ${VIRTUAL_ENV}
ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"
ENV PUTHONBUFFERED True
ENV GOOGLE_APPLICATION_CREDENTIALS "/home/key1.json"

WORKDIR /home
COPY requirements.txt .
RUN python -m pip install pip --upgrade
RUN python -m pip install -r requirements.txt
COPY pubsub_inference.py .
COPY key1.json .

CMD [ "python","/home/pubsub_inference.py" ]