# start with a base image
FROM python:3.5
MAINTAINER alex <Alex Miller, alex.miller@devinit.org>

RUN mkdir /src
ADD ./ /src

WORKDIR /src
# install dependencies
RUN apt-get update
RUN pip install -r requirements.txt

CMD echo "Successully built: to run 'docker-compose run app python app/run.py'"
