#!/bin/sh

ASCIIDOCTOR=$(which asciidoctor)

# Build html docs
#
$ASCIIDOCTOR index.adoc
$ASCIIDOCTOR install.adoc
$ASCIIDOCTOR admin.adoc
$ASCIIDOCTOR user.adoc

# Build pdf
#
#$ASCIIDOCTOR -b PDF pdf.adoc
