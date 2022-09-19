FROM python:3.9

ADD main.py .

RUN pip install websocket jsonpickle numpy datetime requests python-binance binance.py

RUN wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz && \
  tar -xvzf ta-lib-0.4.0-src.tar.gz && \
  cd ta-lib/ && \
  ./configure --prefix=/opt/venv && \
  make && \
  make install


CMD ["python", "./main.py"]

