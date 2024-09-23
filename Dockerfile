FROM ubuntu:jammy

WORKDIR /app

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update
RUN apt-get install -y lsb-release software-properties-common
RUN gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys E298A3A825C0D65DFD57CBB651716619E084DAB9
RUN gpg -a --export E298A3A825C0D65DFD57CBB651716619E084DAB9 | apt-key add -
RUN apt-get update
RUN apt-get install -y software-properties-common dirmngr r-base r-base-dev r-base-core r-recommended
RUN apt-get install -y python3 python3-pip libssl-dev libcurl4-openssl-dev curl
RUN pip install python-telegram-bot==21.3
RUN R -e "install.packages('thunder',repos='https://cloud.r-project.org')"

COPY sounding_script.R .
COPY sounding_script_pay.R .
COPY telegram_bot.py .

ENTRYPOINT ["python3"]
CMD ["telegram_bot.py"]