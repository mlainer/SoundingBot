FROM ubuntu:jammy

WORKDIR /app

ENV PYTHONUNBUFFERED=1

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update
RUN apt-get install -y lsb-release software-properties-common
RUN gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys E298A3A825C0D65DFD57CBB651716619E084DAB9
RUN gpg -a --export E298A3A825C0D65DFD57CBB651716619E084DAB9 | apt-key add -
RUN apt-get update
RUN apt-get install -y software-properties-common dirmngr r-base r-base-dev r-base-core r-recommended
RUN apt-get install -y python3 python3-pip libarchive-dev libssl-dev libcurl4-openssl-dev libicu-dev curl
RUN pip install python-telegram-bot==21.3
RUN R -e 'install.packages("remotes", repos = "https://cloud.r-project.org")'
RUN R -e 'remotes::install_github("bczernecki/thunder")'
RUN R -e 'install.packages("climate", repos = "https://cloud.r-project.org")'

# thundeR lays out its text for Helvetica widths: use a metric-compatible font and a UTF-8 locale
RUN apt-get update && apt-get install -y --no-install-recommends fonts-liberation fontconfig \
    && rm -rf /var/lib/apt/lists/*
COPY fonts.conf /etc/fonts/local.conf
RUN fc-cache -f
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8

COPY sounding_script.R .
COPY sounding_script_pay.R .
COPY telegram_bot.py .

ENTRYPOINT ["python3"]
CMD ["telegram_bot.py"]
