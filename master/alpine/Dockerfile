# Build stage for Bitcoin Knots
FROM alpine:3.21 AS build

RUN apk --no-cache add \
    autoconf \
    automake \
    boost-dev \
    build-base \
    ccache \
    chrpath \
    clang18 \
    file \
    gnupg \
    git \
    libevent-dev \
    libressl \
    libtool \
    linux-headers \
    sqlite-dev \
    zeromq-dev

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

# Copy build artefacts
FROM alpine:3.21

ARG UID=100
ARG GID=101

LABEL maintainer.0="Yasu Takumi (@yasutakumi)"

RUN addgroup --gid ${GID} --system bitcoin && \
    adduser --uid ${UID} --system bitcoin --ingroup bitcoin
RUN apk --no-cache add \
    bash \
    libevent \
    libzmq \
    shadow \
    sqlite-libs \
    su-exec

ENV BITCOIN_DATA=/home/bitcoin/.bitcoin
ENV PATH=/opt/bin:$PATH

COPY --from=build /opt/bitcoin /opt
COPY docker-entrypoint.sh /entrypoint.sh

VOLUME ["/home/bitcoin/.bitcoin"]

EXPOSE 8332 8333 18332 18333 18443 18444 38333 38332

ENTRYPOINT ["/entrypoint.sh"]

CMD ["bitcoind"]
