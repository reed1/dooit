_pkgname=dooit
_branch=reed
pkgname=rd-$_pkgname
pkgver=3.1.0
pkgrel=1
pkgdesc="A TUI Todo Manager"
arch=('any')
url="https://github.com/reed1/$_pkgname"
license=('MIT')
depends=('python>=3.9')
makedepends=('python-build' 'python-installer' 'python-poetry-core')
source=("$_pkgname-$pkgver.tar.gz::https://github.com/reed1/$_pkgname/archive/refs/heads/$_branch.tar.gz")
sha256sums=('SKIP')  # You'll need to replace this with the actual SHA256 sum

prepare() {
    cd "$srcdir/$_pkgname-$_branch"
    # Create a virtual environment
    python -m venv .venv
    source .venv/bin/activate
    # Install poetry
    pip install poetry
    # Install dependencies with verbose output
    poetry install --only main --no-interaction --no-ansi -v
    # Verify installed packages
    pip list
}

build() {
    cd "$srcdir/$_pkgname-$_branch"
    source .venv/bin/activate
    poetry build
}

package() {
    cd "$srcdir/$_pkgname-$_branch"
    source .venv/bin/activate

    # Create a new virtual environment in the package directory
    install -d "$pkgdir/usr/lib/$pkgname"
    python -m venv "$pkgdir/usr/lib/$pkgname"
    source "$pkgdir/usr/lib/$pkgname/bin/activate"

    # Install the package with all dependencies
    pip install dist/*.whl

    # Create a wrapper script
    install -d "$pkgdir/usr/bin"
    cat > "$pkgdir/usr/bin/$pkgname" << EOF
#!/bin/sh
source /usr/lib/$pkgname/bin/activate
exec python -m $_pkgname "\$@"
EOF
    chmod +x "$pkgdir/usr/bin/$pkgname"

    # Install license
    install -Dm644 LICENSE "$pkgdir/usr/share/licenses/$pkgname/LICENSE"
}