#!/usr/bin/env perl
use strict;
use warnings;
use Storable qw(fd_retrieve);
use Data::Dumper;

binmode STDIN;
local $/;
my $raw = <STDIN>;
unless (defined $raw) {
    warn "No input on STDIN\n";
    exit 2;
}

my $data = do {
    open my $fh, '<', \$raw or do {
        warn "Failed to open in-memory filehandle: $!\n";
        exit 3;
    };
    binmode $fh;
    my $d = eval { fd_retrieve($fh) };
    if ($@) {
        warn "Failed to fd_retrieve Storable data: $@\n";
        exit 3;
    }
    $d;
};

if (!ref $data) {
    # simple scalar
    print "$data\n";
} else {
    local $Data::Dumper::Terse  = 0; # show $VAR1 =
    local $Data::Dumper::Indent = 2;
    print Dumper($data);
}