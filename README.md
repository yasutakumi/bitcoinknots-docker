# bitcoinknots/bitcoin

[![bitcoinknots/bitcoin][docker-pulls-image]][docker-hub-url] [![bitcoinknots/bitcoin][docker-stars-image]][docker-hub-url] [![bitcoinknots/bitcoin][docker-size-image]][docker-hub-url]

## Looking for Bitcoin Core images?

These images are meant to be drop-in replacements for the `bitcoin/bitcoin` (Bitcoin Core) images. If you're looking for those, go to [willcl-ark/bitcoin-core-docker](https://github.com/willcl-ark/bitcoin-core-docker).

## About the images

> [!IMPORTANT]
> These are **unofficial** Bitcoin Knots images, not endorsed or associated with the Bitcoin Knots project on GitHub: github.com/bitcoinknots/bitcoin

- The images are aimed at testing environments (e.g. for downstream or bitcoin-adjacent projects), as it is non-trivial to verify the authenticity of the Bitcoin Knots binaries inside.
  - When using Bitcoin Knots software for non-testing purposes you should always ensure that you have either: i) built it from source yourself, or ii) verfied your binary download.
- The images are built using CI workflows found in this repo: https://github.com/yasutakumi/bitcoinknots-docker
- The images are built with support for the following platforms:
  | Image                                   | Platforms                              |
  |-----------------------------------------|----------------------------------------|
  | `bitcoinknots/bitcoin:latest`           | linux/amd64, linux/arm64, linux/arm/v7 |
  | `bitcoinknots/bitcoin:alpine`           | linux/amd64                            |
  | `bitcoinknots/bitcoin:<version>`        | linux/amd64, linux/arm64, linux/arm/v7 |
  | `bitcoinknots/bitcoin:<version>-alpine` | linux/amd64                            |
  | `bitcoinknots/bitcoin:master`           | linux/amd64, linux/arm64               |
  | `bitcoinknots/bitcoin:master-alpine`    | linux/amd64, linux/arm64               |

- The Debian-based (non-alpine) images use pre-built binaries pulled from bitcoinknots.org. These binaries are built using the Bitcoin Knots [reproducible build](https://github.com/bitcoinknots/bitcoin/blob/master/contrib/guix/README.md) system, and signatures attesting to them can be found in the [guix.sigs](https://github.com/bitcoinknots/guix.sigs) repo. Signatures are checked in the build process for these docker images using the [verify_binaries.py](https://github.com/bitcoinknots/bitcoin/tree/master/contrib/verify-binaries) script from the bitcoinknots/bitcoin git repository.
- The alpine images are built from source inside the CI.
- The nightly master image is source-built, and targeted at the linux/amd64 and linux/arm64 platforms.

## Tags

- `28.1`, `28`, `latest` ([28.1/Dockerfile](https://github.com/yasutakumi/bitcoinknots-docker/blob/master/28.1/Dockerfile)) [**multi-platform**]
- `28.1-alpine`, `28-alpine`, `alpine` ([28.1/alpine/Dockerfile](https://github.com/yasutakumi/bitcoinknots-docker/blob/master/28.1/alpine/Dockerfile))

### Picking the right tag

> [!IMPORTANT]
> The Alpine Linux distribution, whilst being a resource efficient Linux distribution with security in mind, is not officially supported by the Bitcoin Knots team nor the Bitcoin Core team — use at your own risk.

#### Latest released version

These tags refer to the latest major version, and the latest minor and patch of this version where applicable.

- `bitcoinknots/bitcoin:latest`: Release binaries directly from bitcoinknots.org. Caution when specifying this tag in production as blindly upgrading Bitcoin Knots major versions can introduce new behaviours.
- `bitcoinknots/bitcoin:alpine`: Source-built binaries using the Alpine Linux distribution.

#### Specific released version

These tags refer to a specific version of Bitcoin Knots.

- `bitcoinknots/bitcoin:<version>`: Release binaries of a specific release directly from bitcoinknots.org (e.g. `27.1` or `26`).
- `bitcoinknots/bitcoin:<version>-alpine`: Source-built binaries of a specific release of Bitcoin Knots (e.g. `27.1` or `26`) using the Alpine Linux distribution.

#### Nightly master build

This tag refers to a nightly build of https://github.com/bitcoinknots/bitcoin master branch using Alpine Linux.

- `bitcoinknots/bitcoin:master`: Source-built binaries on Debian Linux, compiled nightly using master branch pulled from https://github.com/bitcoinknots/bitcoin.
- `bitcoinknots/bitcoin:master-alpine`: Source-built binaries on Alpine Linux, compiled nightly using master branch pulled from https://github.com/bitcoinknots/bitcoin.

## Usage

### How to use these images

These images contain the main binaries from the Bitcoin Knots project - `bitcoind`, `bitcoin-cli` and `bitcoin-tx`. The images behave like binaries, so you can pass arguments to the image and they will be forwarded to the `bitcoind` binary (by default, other binaries on demand):

```sh
❯ docker run --rm -it bitcoinknots/bitcoin \
  -printtoconsole \
  -regtest=1 \
  -rpcallowip=172.17.0.0/16 \
  -rpcauth='foo:7d9ba5ae63c3d4dc30583ff4fe65a67e$9e3634e81c11659e3de036d0bf88f89cd169c1039e6e09607562d54765c649cc'
```

_Note: [learn more](#using-rpcauth-for-remote-authentication) about how `-rpcauth` works for remote authentication._

By default, `bitcoind` will run as user `bitcoin` in the group `bitcoin` for security reasons and its default data directory is set to `/home/bitcoin/.bitcoin`. If you'd like to customize where `bitcoin` stores its data, you must use the `BITCOIN_DATA` environment variable. The directory will be automatically created with the correct permissions for the `bitcoin` user and `bitcoind` automatically configured to use it.

```sh
❯ docker run --env BITCOIN_DATA=/var/lib/bitcoinknots --rm -it bitcoinknots/bitcoin \
  -printtoconsole \
  -regtest=1
```

You can also mount a directory in a volume under `/home/bitcoin/.bitcoin` in case you want to access it on the host:

```sh
❯ docker run -v ${PWD}/data:/home/bitcoin/.bitcoin -it --rm bitcoinknots/bitcoin \
  -printtoconsole \
  -regtest=1
```

You can optionally create a service using `docker-compose`:

```yml
bitcoin-server:
  image: bitcoinknots/bitcoin:latest
  command:
    -printtoconsole
    -regtest=1
```

### Using a custom user id (UID) and group id (GID)

By default, images are created with a `bitcoin` user/group using a static UID/GID (`101:101` on Debian and `100:101` on Alpine). You may customize the user and group ids using the build arguments `UID` (`--build-arg UID=<uid>`) and `GID` (`--build-arg GID=<gid>`).

If you'd like to use the pre-built images, you can also customize the UID/GID on runtime via environment variables `$UID` and `$GID`:

```sh
❯ docker run -e UID=10000 -e GID=10000 -it --rm bitcoinknots/bitcoin \
  -printtoconsole \
  -regtest=1
```

This will recursively change the ownership of the `bitcoin` home directory and `$BITCOIN_DATA` to UID/GID `10000:10000`.

### Using RPC to interact with the daemon

There are two communications methods to interact with a running Bitcoin Knots daemon.

The first one is using a cookie-based local authentication. It doesn't require any special authentication information as running a process locally under the same user that was used to launch the Bitcoin Knots daemon allows it to read the cookie file previously generated by the daemon for clients. The downside of this method is that it requires local machine access.

The second option is making a remote procedure call using a username and password combination. This has the advantage of not requiring local machine access, but in order to keep your credentials safe you should use the newer `rpcauth` authentication mechanism.

#### Using cookie-based local authentication

Start by launch the Bitcoin Knots daemon:

```sh
❯ docker run --rm --name bitcoin-server -it bitcoinknots/bitcoin \
  -printtoconsole \
  -regtest=1
```

Then, inside the running same `bitcoin-server` container, locally execute the query to the daemon using `bitcoin-cli`:

```sh
❯ docker exec --user bitcoin bitcoin-server bitcoin-cli -regtest getmininginfo

{
  "blocks": 0,
  "currentblocksize": 0,
  "currentblockweight": 0,
  "currentblocktx": 0,
  "difficulty": 4.656542373906925e-10,
  "errors": "",
  "networkhashps": 0,
  "pooledtx": 0,
  "chain": "regtest"
}
```

`bitcoin-cli` reads the authentication credentials automatically from the [data directory](https://github.com/bitcoinknots/bitcoin/blob/master/doc/files.md#data-directory-layout), on mainnet this means from `/home/bitcoin/.bitcoin/.cookie`.

#### Using rpcauth for remote authentication

Before setting up remote authentication, you will need to generate the `rpcauth` line that will hold the credentials for the Bitcoind Knots daemon. You can either do this yourself by constructing the line with the format `<user>:<salt>$<hash>` or use the official [`rpcauth.py`](https://github.com/bitcoinknots/bitcoin/blob/master/share/rpcauth/rpcauth.py)  script to generate this line for you, including a random password that is printed to the console.

_Note: This is a Python 3 script. use `[...] | python3 - <username>` when executing on macOS._

Example:

```sh
❯ curl -sSL https://raw.githubusercontent.com/bitcoinknots/bitcoin/master/share/rpcauth/rpcauth.py | python - <username>

String to be appended to bitcoin.conf:
rpcauth=foo:7d9ba5ae63c3d4dc30583ff4fe65a67e$9e3634e81c11659e3de036d0bf88f89cd169c1039e6e09607562d54765c649cc
Your password:
qDDZdeQ5vw9XXFeVnXT4PZ--tGN2xNjjR4nrtyszZx0=
```

Note that for each run, even if the username remains the same, the output will be always different as a new salt and password are generated.

Now that you have your credentials, you need to start the Bitcoin Knots daemon with the `-rpcauth` option. Alternatively, you could append the line to a `bitcoin.conf` file and mount it on the container.

Let's opt for the Docker way:

```sh
❯ docker run --rm --name bitcoin-server -it bitcoinknots/bitcoin \
  -printtoconsole \
  -regtest=1 \
  -rpcallowip=172.17.0.0/16 \
  -rpcauth='foo:7d9ba5ae63c3d4dc30583ff4fe65a67e$9e3634e81c11659e3de036d0bf88f89cd169c1039e6e09607562d54765c649cc'
```

Two important notes:

1. Some shells require escaping the rpcauth line (e.g. zsh).
2. It is now perfectly fine to pass the rpcauth line as a command line argument. Unlike `-rpcpassword`, the content is hashed so even if the arguments would be exposed, they would not allow the attacker to get the actual password.

To avoid any confusion about whether or not a remote call is being made, let's spin up another container to execute `bitcoin-cli` and connect it via the Docker network using the password generated above:

```sh
❯ docker run -it --link bitcoin-server --rm bitcoinknots/bitcoin \
  bitcoin-cli \
  -rpcconnect=bitcoin-server \
  -regtest \
  -rpcuser=foo\
  -stdinrpcpass \
  getbalance
```

Enter the password `qDDZdeQ5vw9XXFeVnXT4PZ--tGN2xNjjR4nrtyszZx0=` and hit enter:

```
0.00000000
```

### Exposing Ports

Depending on the network (mode) the Bitcoin Knots daemon is running as well as the chosen runtime flags, several default ports may be available for mapping.

Ports can be exposed by mapping all of the available ones (using `-P` and based on what `EXPOSE` documents) or individually by adding `-p`. This mode allows assigning a dynamic port on the host (`-p <port>`) or assigning a fixed port `-p <hostPort>:<containerPort>`.

Example for running a node in `regtest` mode mapping JSON-RPC/REST (18443) and P2P (18444) ports:

```sh
docker run --rm -it \
  -p 18443:18443 \
  -p 18444:18444 \
  bitcoinknots/bitcoin \
  -printtoconsole \
  -regtest=1 \
  -rpcallowip=172.17.0.0/16 \
  -rpcbind=0.0.0.0 \
  -rpcauth='foo:7d9ba5ae63c3d4dc30583ff4fe65a67e$9e3634e81c11659e3de036d0bf88f89cd169c1039e6e09607562d54765c649cc'
```

To test that mapping worked, you can send a JSON-RPC curl request to the host port:

```
curl --data-binary '{"jsonrpc":"1.0","id":"1","method":"getnetworkinfo","params":[]}' http://foo:qDDZdeQ5vw9XXFeVnXT4PZ--tGN2xNjjR4nrtyszZx0=@127.0.0.1:18443/
```

#### Mainnet

- JSON-RPC/REST: 8332
- P2P: 8333

#### Testnet

- JSON-RPC: 18332
- P2P: 18333

#### Regtest

- JSON-RPC/REST: 18443
- P2P: 18444

#### Signet

- JSON-RPC/REST: 38332
- P2P: 38333

## License

[License information](https://github.com/bitcoinknots/bitcoin/blob/master/COPYING) for the software contained in this image.

[License information](https://github.com/yasutakumi/bitcoinknots-docker/blob/master/LICENSE) for the [yasutakumi/bitcoinknots-docker][docker-hub-url] docker project.

[docker-hub-url]: https://hub.docker.com/r/bitcoinknots/bitcoin
[docker-pulls-image]: https://img.shields.io/docker/pulls/bitcoinknots/bitcoin.svg?style=flat-square
[docker-size-image]: https://img.shields.io/docker/image-size/bitcoinknots/bitcoin?style=flat-square
[docker-stars-image]: https://img.shields.io/docker/stars/bitcoinknots/bitcoin.svg?style=flat-square
