# The line below states we will base a new image on the Latest zewelor/bt-mqtt-gateway.
FROM zewelor/bt-mqtt-gateway:latest

# Update pip tool
RUN /usr/local/bin/python -m pip install --upgrade pip

# Install these packages for Python development environment
RUN apk add --no-cache gcc g++ python3 python3-dev py-pip mysql-dev linux-headers libffi-dev openssl-dev bash

# Install evdev package
RUN pip3 install evdev

# Copy wait-for-it.sh to container
COPY wait-for-it.sh /application/wait-for-it.sh

RUN chmod +x /application/wait-for-it.sh

# Update gateway.py
COPY gateway.py /application/gateway.py

# Update gateway.py
COPY /workers/blunoled.py /workers/blunonfc.py /workers/nteumm.py /application/workers/

# Update gateway.py
COPY start.sh /start.sh

RUN chmod +x /start.sh

# This is the command that will run when the Container starts
CMD ["/bin/sh"]