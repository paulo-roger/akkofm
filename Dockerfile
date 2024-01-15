FROM python:slim
WORKDIR /usr/app/mastofm

RUN pip3 install pylast mastodon.py --no-cache-dir --upgrade

COPY update.py .
COPY LICENSE .
COPY init.sh .

RUN chmod +x init.sh
RUN sed -i 's/ - / • /g' update.py
RUN sed -i 's/ 🔊//g' update.py

ENTRYPOINT [ "/bin/sh", "init.sh" ]