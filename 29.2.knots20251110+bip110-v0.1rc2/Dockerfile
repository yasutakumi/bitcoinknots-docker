FROM debian:bookworm-slim AS builder

LABEL maintainer.0="Yasu Takumi (@yasutakumi)"

RUN apt-get update -y \
  && apt-get install -y ca-certificates curl git gnupg gosu python3 wget --no-install-recommends \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

ARG TARGETPLATFORM
ENV BITCOIN_VERSION=29.2.knots20251110+bip110-v0.1rc2
ENV BITCOIN_SOURCE=https://github.com/dathonohm/bitcoin/releases/download/v${BITCOIN_VERSION}
ENV SIGS_REPO_URL="https://github.com/dathonohm/guix.sigs"
ENV SIGS_CLONE_DIR="guix.sigs"
ENV VERIFY_SCRIPT_URL="https://raw.githubusercontent.com/dathonohm/bitcoin/v${BITCOIN_VERSION}/contrib/verify-binaries/verify.py"

WORKDIR /bitcoin
COPY verify.py .
COPY SHA256SUMS .
COPY SHA256SUMS.asc .

RUN set -ex \
  && if [ "${TARGETPLATFORM}" = "linux/amd64" ]; then export TARGETPLATFORM=x86_64-linux-gnu; fi \
  && if [ "${TARGETPLATFORM}" = "linux/arm64" ]; then export TARGETPLATFORM=aarch64-linux-gnu; fi \
  && if [ "${TARGETPLATFORM}" = "linux/arm/v7" ]; then export TARGETPLATFORM=arm-linux-gnueabihf; fi \
  && wget ${BITCOIN_SOURCE}/bitcoin-${BITCOIN_VERSION}-${TARGETPLATFORM}.tar.gz \
  && git clone ${SIGS_REPO_URL} ${SIGS_CLONE_DIR} \
  && gpg --import "${SIGS_CLONE_DIR}"/builder-keys/* \
  && ./verify.py --min-good-sigs 5 bin SHA256SUMS \
    "bitcoin-${BITCOIN_VERSION}-${TARGETPLATFORM}.tar.gz" \
  && tar -xzf "bitcoin-${BITCOIN_VERSION}-${TARGETPLATFORM}.tar.gz" -C /opt \
  && rm -rf ${SIGS_CLONE_DIR} \
  && rm -rf ${TMPDIR} \
  && rm -rf /opt/bitcoin-${BITCOIN_VERSION}/bin/bitcoin-qt

# Second stage
FROM debian:bookworm-slim

ARG UID=101
ARG GID=101

ENV BITCOIN_DATA=/home/bitcoin/.bitcoin
ENV BITCOIN_VERSION=29.2.knots20251110+bip110-v0.1rc2
ENV PATH=/opt/bitcoin-${BITCOIN_VERSION}/bin:$PATH

RUN groupadd --gid ${GID} bitcoin \
  && if echo "$BITCOIN_VERSION" | grep -q "rc"; then \
       PADDED_VERSION=$(echo $BITCOIN_VERSION | sed 's/\([0-9]\+\)\.\([0-9]\+\)rc/\1.\2.0rc/'); \
     else \
       PADDED_VERSION=$BITCOIN_VERSION; \
     fi \
  && echo "Padded version: $PADDED_VERSION" \
  && useradd --create-home --no-log-init -u ${UID} -g ${GID} bitcoin \
  && apt-get update -y \
  && apt-get install -y gosu --no-install-recommends \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

COPY --from=builder /opt/bitcoin-${BITCOIN_VERSION} /opt/bitcoin-${BITCOIN_VERSION}

COPY docker-entrypoint.sh /entrypoint.sh

VOLUME ["/home/bitcoin/.bitcoin"]
EXPOSE 8332 8333 18332 18333 18443 18444 38333 38332

ENTRYPOINT ["/entrypoint.sh"]
RUN bitcoind -version | grep "Bitcoin Knots daemon version v${PADDED_VERSION}"
CMD ["bitcoind"]
