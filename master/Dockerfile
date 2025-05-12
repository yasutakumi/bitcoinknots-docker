FROM debian:bookworm-slim AS build

LABEL maintainer.0="Yasu Takumi (@yasutakumi)"

RUN apt-get update -y \
  && apt-get install -y \
    autoconf \
    automake \
    build-essential \
    ca-certificates \
    ccache \
    clang-16 \
    git \
    libboost-dev \
    libevent-dev \
    libsqlite3-dev \
    libtool \
    libzmq3-dev \
    pkg-config \
    python3 \
    systemtap-sdt-dev \
    --no-install-recommends \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

ENV BITCOIN_PREFIX=/opt/bitcoin
ARG COMMIT=28.x-knots

WORKDIR /src

RUN git clone -b "$COMMIT" --single-branch --depth 1 "https://github.com/bitcoinknots/bitcoin.git" && \
    cd bitcoin && \
    git fetch origin "$COMMIT" && \
    git checkout "$COMMIT" && \
    git clean -fdx

WORKDIR /src/bitcoin

RUN ./autogen.sh
RUN ./configure \
  --prefix=${BITCOIN_PREFIX} \
  --mandir=/usr/share/man \
  --disable-tests \
  --disable-bench \
  --disable-fuzz-binary \
  --disable-ccache \
  --with-gui=no \
  --with-utils \
  --without-libs \
  --with-sqlite=yes \
  --with-daemon
RUN make -j`nproc` -C src bitcoind bitcoin-cli bitcoin-tx
RUN make -j`nproc` install
RUN strip ${BITCOIN_PREFIX}/bin/bitcoin-cli
RUN strip ${BITCOIN_PREFIX}/bin/bitcoin-tx
RUN strip ${BITCOIN_PREFIX}/bin/bitcoind

# Second stage
FROM debian:bookworm-slim

ARG UID=101
ARG GID=101

ENV BITCOIN_DATA=/home/bitcoin/.bitcoin

RUN groupadd --gid ${GID} bitcoin \
  && useradd --create-home --no-log-init -u ${UID} -g ${GID} bitcoin \
  && apt-get update -y \
  && apt-get install -y gosu libevent-dev libboost-dev libsqlite3-dev libzmq3-dev systemtap-sdt-dev --no-install-recommends \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

COPY --from=build /opt/bitcoin /opt
ENV PATH=/opt/bin:$PATH

COPY docker-entrypoint.sh /entrypoint.sh

VOLUME ["/home/bitcoin/.bitcoin"]
EXPOSE 8332 8333 18332 18333 18443 18444 38333 38332

ENTRYPOINT ["/entrypoint.sh"]
RUN bitcoind -version | grep "Bitcoin Knots daemon version"
CMD ["bitcoind"]
