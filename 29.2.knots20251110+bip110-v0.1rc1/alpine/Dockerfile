# Build stage for Bitcoin Knots
FROM alpine:3.21 AS build

RUN apk --no-cache add \
    boost-dev \
    build-base \
    ccache \
    chrpath \
    clang18 \
    cmake \
    file \
    gnupg \
    git \
    libevent-dev \
    libtool \
    linux-headers \
    sqlite-dev \
    zeromq-dev

ENV BITCOIN_VERSION=29.2.knots20251110+bip110-v0.1rc1
ENV BITCOIN_PREFIX=/opt/bitcoin-${BITCOIN_VERSION}
ENV BITCOIN_SOURCE_DIR=/bitcoin/src
ENV BITCOIN_SOURCE=https://github.com/dathonohm/bitcoin/releases/download/v${BITCOIN_VERSION}
ENV SIGS_REPO_URL="https://github.com/dathonohm/guix.sigs"
ENV SIGS_CLONE_DIR="guix.sigs"
ENV VERIFY_SCRIPT_URL="https://raw.githubusercontent.com/dathonohm/bitcoin/v${BITCOIN_VERSION}/contrib/verify-binaries/verify.py"

WORKDIR /bitcoin
COPY verify.py .
COPY SHA256SUMS .
COPY SHA256SUMS.asc .

RUN set -ex \
  && wget ${BITCOIN_SOURCE}/bitcoin-${BITCOIN_VERSION}.tar.gz \
  && git clone ${SIGS_REPO_URL} ${SIGS_CLONE_DIR} \
  && gpg --import "${SIGS_CLONE_DIR}"/builder-keys/* \
  && ./verify.py --min-good-sigs 1 bin SHA256SUMS \
    "bitcoin-${BITCOIN_VERSION}.tar.gz" \
  && mkdir -p ${BITCOIN_SOURCE_DIR} \
  && tar -xzf "bitcoin-${BITCOIN_VERSION}.tar.gz" -C ${BITCOIN_SOURCE_DIR} \
  && rm -rf ${SIGS_CLONE_DIR}

WORKDIR "${BITCOIN_SOURCE_DIR}/bitcoin-${BITCOIN_VERSION}"

RUN cmake -B build \
    -DBUILD_TESTS=OFF \
    -DBUILD_TX=ON \
    -DBUILD_UTIL=OFF \
    -DCMAKE_BUILD_TYPE=RelWithDebInfo \
    -DCMAKE_CXX_COMPILER=clang++-18 \
    -DCMAKE_C_COMPILER=clang-18 \
    -DCMAKE_INSTALL_PREFIX:PATH="${BITCOIN_PREFIX}" \
    -DWITH_CCACHE=ON && \
    cmake --build build -j$(nproc) && \
    strip build/bin/bitcoin-cli build/bin/bitcoin-tx build/bin/bitcoind && \
    cmake --install build

# Build stage for compiled artifacts
FROM alpine:3.21

ARG UID=100
ARG GID=101

LABEL maintainer.0="Yasu Takumi (@yasutakumi)"

RUN addgroup bitcoin --gid ${GID} --system
RUN adduser --uid ${UID} --system bitcoin --ingroup bitcoin
RUN apk --no-cache add \
  libevent \
  libzmq \
  shadow \
  sqlite-libs \
  su-exec

ENV BITCOIN_DATA=/home/bitcoin/.bitcoin
ENV BITCOIN_VERSION=29.2.knots20251110+bip110-v0.1rc1
ENV BITCOIN_PREFIX=/opt/bitcoin-${BITCOIN_VERSION}
ENV PATH=/opt/bin:$PATH

COPY --from=build ${BITCOIN_PREFIX} /opt
COPY docker-entrypoint.sh /entrypoint.sh

RUN if echo "$BITCOIN_VERSION" | grep -q "rc"; then \
    PADDED_VERSION=$(echo $BITCOIN_VERSION | sed 's/\([0-9]\+\)\.\([0-9]\+\)rc/\1.\2.0rc/'); \
  else \
    PADDED_VERSION=$BITCOIN_VERSION; \
  fi

VOLUME ["/home/bitcoin/.bitcoin"]

EXPOSE 8332 8333 18332 18333 18444

ENTRYPOINT ["/entrypoint.sh"]

RUN bitcoind -version | grep "Bitcoin Knots daemon version v${PADDED_VERSION}"

CMD ["bitcoind"]
