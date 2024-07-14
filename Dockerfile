FROM alpine:3.20 AS build
COPY requirements.txt .
RUN <<EOF
apk add --no-cache cargo python3-dev=3.12.3-r1 py3-pip=24.0-r2
pip -q install --break-system-packages -r requirements.txt
cargo install bgpkit-parser --features cli
EOF

FROM alpine:3.20

RUN apk add --no-cache libgcc python3=3.12.3-r1 bash
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