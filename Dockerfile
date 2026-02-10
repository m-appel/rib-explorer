FROM alpine:3.23 AS build
COPY requirements.txt .
RUN <<EOF
apk add --no-cache cargo=~1.91 python3-dev=~3.12 py3-pip=~25
pip -q install --break-system-packages -r requirements.txt
cargo install bgpkit-parser@0.15.0 --features cli
EOF

FROM alpine:3.23

RUN apk add --no-cache libgcc python3=~3.12 bash
COPY --from=build /usr/lib/python3.12/site-packages /usr/lib/python3.12/site-packages
COPY --from=build /root/.cargo/bin/bgpkit-parser /usr/bin/bgpkit-parser

RUN <<EOF
rm -r /usr/lib/python3.12/__pycache__/
rm -r /usr/lib/python3.12/ensurepip/
rm -r /usr/lib/python3.12/pydoc_data/
rm -r /usr/lib/python3.12/lib2to3/
rm -r /usr/lib/python3.12/site-packages/pip/
rm -r /usr/lib/python3.12/site-packages/setuptools
EOF

WORKDIR /code
COPY . .

ENTRYPOINT [ "/bin/bash",  "entry.sh" ]
